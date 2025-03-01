import json
import os
import torch
import traceback
import requests
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

class LLMHandler:
    """处理LLM模型加载和推理的类"""
    
    def __init__(self, config_path="config.json"):
        """初始化LLM处理器
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.model_name = self.config['model']['name']
        self.use_ollama = self.config['model'].get('use_ollama', False)
        self.use_llama_cpp = self.config['model'].get('use_llama_cpp', False)
        self.ollama_base_url = self.config['model'].get('ollama_base_url', 'http://localhost:11434')
        self.local_model_path = self.config['model'].get('local_model_path', '')
        self.device = self.config['model']['device']
        self.dtype = self.config['model']['dtype']
        
        # llama-cpp-python 特定配置
        self.context_size = self.config['model'].get('context_size', 4096)
        self.n_gpu_layers = self.config['model'].get('n_gpu_layers', -1)
        self.n_threads = self.config['model'].get('n_threads', 4)
        
        # 设置torch数据类型
        if self.dtype == "bfloat16":
            self.torch_dtype = torch.bfloat16
        elif self.dtype == "float16":
            self.torch_dtype = torch.float16
        else:
            self.torch_dtype = torch.float32
        
        # 模型和分词器
        self.model = None
        self.tokenizer = None
        self.pipe = None
        self.llama_cpp_model = None
        
        # 系统提示词
        self.system_prompt = self.config['chat']['system_prompt']
        self.max_new_tokens = self.config['chat']['max_new_tokens']
    
    def _check_ollama_availability(self):
        """检查Ollama服务是否可用"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                
                if self.model_name in available_models:
                    print(f"Ollama模型 {self.model_name} 可用")
                    return True, "Ollama服务可用，模型已下载"
                else:
                    print(f"Ollama服务可用，但模型 {self.model_name} 未找到")
                    print(f"可用模型: {available_models}")
                    return False, f"模型 {self.model_name} 未在Ollama中找到。请使用 'ollama pull {self.model_name}' 下载模型。"
            else:
                return False, f"Ollama服务响应异常: {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, f"无法连接到Ollama服务，请确保Ollama正在运行 (URL: {self.ollama_base_url})"
        except Exception as e:
            return False, f"检查Ollama服务时出错: {str(e)}"
    
    def _check_llama_cpp_model(self):
        """检查llama-cpp-python模型文件是否存在"""
        if not os.path.exists(self.local_model_path):
            return False, f"模型文件不存在: {self.local_model_path}"
        
        return True, "模型文件检查通过"
    
    def load_model(self):
        """加载模型和分词器"""
        try:
            print(f"正在准备模型: {self.model_name}")
            
            if self.use_llama_cpp:
                # 检查模型文件
                is_valid, message = self._check_llama_cpp_model()
                if not is_valid:
                    print(f"模型文件检查失败: {message}")
                    return False
                
                # 导入llama_cpp
                try:
                    from llama_cpp import Llama
                except ImportError:
                    print("无法导入llama_cpp模块，请确保已安装llama-cpp-python")
                    return False
                
                print(f"正在加载模型: {self.local_model_path}")
                print(f"使用配置: n_gpu_layers={self.n_gpu_layers}, n_threads={self.n_threads}, n_ctx={self.context_size}")
                
                # 加载模型
                try:
                    self.llama_cpp_model = Llama(
                        model_path=self.local_model_path,
                        n_gpu_layers=self.n_gpu_layers,
                        n_ctx=self.context_size,
                        n_threads=self.n_threads,
                        verbose=False
                    )
                    print("模型加载完成!")
                    return True
                except Exception as e:
                    print(f"加载模型时出错: {str(e)}")
                    traceback.print_exc()
                    return False
                
            elif self.use_ollama:
                # 检查Ollama服务
                is_available, message = self._check_ollama_availability()
                if not is_available:
                    print(f"Ollama检查失败: {message}")
                    return False
                
                print("Ollama服务检查通过，模型可用")
                return True
            else:
                # 使用Transformers加载模型的原有代码
                print("使用Transformers加载模型")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.pipe = pipeline(
                    "text-generation",
                    model=self.model_name,
                    tokenizer=self.tokenizer,
                    model_kwargs={"torch_dtype": self.torch_dtype},
                    device_map=self.device,
                )
            
            print("模型准备完成!")
            return True
        except Exception as e:
            print(f"模型准备失败: {str(e)}")
            print("详细错误信息:")
            traceback.print_exc()
            return False
    
    def generate_response(self, messages):
        """生成回复
        
        Args:
            messages: 消息列表，格式为[{"role": "user", "content": "你好"}, ...]
            
        Returns:
            生成的回复文本
        """
        if self.use_llama_cpp:
            return self._generate_with_llama_cpp(messages)
        elif self.use_ollama:
            return self._generate_with_ollama(messages)
        else:
            return self._generate_with_transformers(messages)
    
    def _generate_with_llama_cpp(self, messages):
        """使用llama-cpp-python生成回复"""
        try:
            if not self.llama_cpp_model:
                raise ValueError("模型未加载，请先调用load_model()")
            
            # 确保系统提示词在消息列表的开头
            if not messages or messages[0].get("role") != "system":
                messages = [{"role": "system", "content": self.system_prompt}] + messages
            
            # 构造提示
            chat_format = "llama-3"  # Llama 3模型的聊天格式
            
            # 使用模型的chat方法
            response = self.llama_cpp_model.create_chat_completion(
                messages=[{"role": m["role"], "content": m["content"]} for m in messages],
                max_tokens=self.max_new_tokens,
                temperature=0.7,
                top_p=0.9,
                repeat_penalty=1.1,
                stop=["</s>"],
                stream=False
            )
            
            # 提取回复
            if "choices" in response and len(response["choices"]) > 0:
                return response["choices"][0]["message"]["content"]
            else:
                return "无法生成回复"
            
        except Exception as e:
            error_msg = f"使用llama-cpp生成回复时出错: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            return f"抱歉，生成回复时出现错误: {str(e)}"
    
    def _generate_with_ollama(self, messages):
        """使用Ollama API生成回复"""
        try:
            # 确保系统提示词在消息列表的开头
            if not messages or messages[0].get("role") != "system":
                messages = [{"role": "system", "content": self.system_prompt}] + messages
            
            # 构造Ollama API请求
            api_url = f"{self.ollama_base_url}/api/chat"
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,  # 明确指定非流式响应
                "options": {
                    "num_predict": self.max_new_tokens,
                    "temperature": 0.5,  # 降低温度，使回复更加确定性
                    "top_p": 0.9,        # 添加top_p参数，控制多样性
                    "stop": ["</s>"]     # 添加停止标记
                }
            }
            
            # 发送请求
            response = requests.post(api_url, json=payload)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    return result['message']['content']
                except requests.exceptions.JSONDecodeError:
                    # 尝试逐行解析JSON响应
                    print("尝试逐行解析响应...")
                    lines = response.text.strip().split('\n')
                    if lines and len(lines) > 0:
                        try:
                            # 尝试解析最后一行JSON
                            last_json = json.loads(lines[-1])
                            if 'message' in last_json and 'content' in last_json['message']:
                                return last_json['message']['content']
                        except:
                            pass
                    
                    # 如果无法解析JSON，直接返回文本响应
                    print("无法解析JSON，返回原始响应")
                    return f"API响应解析错误，原始响应: {response.text[:200]}..."
            else:
                error_msg = f"Ollama API返回错误: {response.status_code}, {response.text}"
                print(error_msg)
                return f"生成回复时出错: {error_msg}"
        
        except Exception as e:
            error_msg = f"使用Ollama生成回复时出错: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            return f"抱歉，生成回复时出现错误: {str(e)}"
    
    def _generate_with_transformers(self, messages):
        """使用Transformers生成回复"""
        if not self.pipe:
            raise ValueError("模型未加载，请先调用load_model()")
        
        # 确保系统提示词在消息列表的开头
        if not messages or messages[0].get("role") != "system":
            messages = [{"role": "system", "content": self.system_prompt}] + messages
        
        try:
            outputs = self.pipe(
                messages,
                max_new_tokens=self.max_new_tokens,
            )
            
            # 提取生成的回复
            response = outputs[0]["generated_text"][-1]["content"]
            return response
        except Exception as e:
            print(f"生成回复时出错: {str(e)}")
            traceback.print_exc()
            return "抱歉，生成回复时出现错误。"
