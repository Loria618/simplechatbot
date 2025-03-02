import json
import os
import torch
import traceback
import requests
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from dotenv import load_dotenv
from env_utils import is_production

class LLMHandler:
    """Class for handling LLM model loading and inference"""
    
    def __init__(self, config_path="config.json"):
        """Initialize LLM handler
        
        Args:
            config_path: Path to configuration file
        """
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Check if running in production
        self.is_production = is_production()
        
        # If in production, override config to use HuggingFace API
        if self.is_production:
            self.use_ollama = False
            self.use_llama_cpp = False
            self.use_huggingface_api = True
            print("Running in production mode, using HuggingFace API")
        else:
            self.use_ollama = self.config['model'].get('use_ollama', False)
            self.use_llama_cpp = self.config['model'].get('use_llama_cpp', False)
            self.use_huggingface_api = self.config['model'].get('use_huggingface_api', False)
            print(f"Running in local mode, using {'Ollama' if self.use_ollama else 'local model'}")
        
        self.model_name = self.config['model']['name']
        self.ollama_base_url = self.config['model'].get('ollama_base_url', 'http://localhost:11434')
        self.local_model_path = self.config['model'].get('local_model_path', '')
        self.device = self.config['model']['device']
        self.dtype = self.config['model']['dtype']
        
        # HuggingFace API configuration
        self.huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
        self.huggingface_model_name = self.config.get('huggingface', {}).get('model_name', 
                                     self.config['model'].get('huggingface_model_name', 
                                     'meta-llama/Meta-Llama-3.1-8B-Instruct'))
        self.huggingface_api_url = f"https://api-inference.huggingface.co/models/{self.huggingface_model_name}"
        
        # llama-cpp-python specific configuration
        self.context_size = self.config['model'].get('context_size', 4096)
        self.n_gpu_layers = self.config['model'].get('n_gpu_layers', -1)
        self.n_threads = self.config['model'].get('n_threads', 4)
        
        # Set torch data type
        if self.dtype == "bfloat16":
            self.torch_dtype = torch.bfloat16
        elif self.dtype == "float16":
            self.torch_dtype = torch.float16
        else:
            self.torch_dtype = torch.float32
        
        # Model and tokenizer
        self.model = None
        self.tokenizer = None
        self.pipe = None
        self.llama_cpp_model = None
        
        # System prompt
        self.system_prompt = self.config['chat']['system_prompt']
        self.max_new_tokens = self.config['chat']['max_new_tokens']
    
    def _check_ollama_availability(self):
        """Check if Ollama service is available"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_models = [model['name'] for model in models]
                
                if self.model_name in available_models:
                    print(f"Ollama model {self.model_name} is available")
                    return True, "Ollama service is available, model has been downloaded"
                else:
                    print(f"Ollama service is available, but model {self.model_name} was not found")
                    print(f"Available models: {available_models}")
                    return False, f"Model {self.model_name} not found in Ollama. Please use 'ollama pull {self.model_name}' to download the model."
            else:
                return False, f"Ollama service response abnormal: {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, f"Cannot connect to Ollama service, please make sure Ollama is running (URL: {self.ollama_base_url})"
        except Exception as e:
            return False, f"Error checking Ollama service: {str(e)}"
    
    def _check_llama_cpp_model(self):
        """Check if llama-cpp-python model file exists"""
        if not os.path.exists(self.local_model_path):
            return False, f"Model file does not exist: {self.local_model_path}"
        
        return True, "Model file check passed"
    
    def load_model(self):
        """Load model and tokenizer"""
        try:
            print(f"Preparing model: {self.model_name if not self.is_production else self.huggingface_model_name}")
            
            if self.is_production or self.use_huggingface_api:
                # Check HuggingFace API key
                if not self.huggingface_api_key:
                    print("HuggingFace API key not set, please set HUGGINGFACE_API_KEY in the .env file")
                    return False
                
                print(f"Using HuggingFace Inference API: {self.huggingface_model_name}")
                return True
                
            elif self.use_llama_cpp:
                # Check model file
                is_valid, message = self._check_llama_cpp_model()
                if not is_valid:
                    print(f"Model file check failed: {message}")
                    return False
                
                # Import llama_cpp
                try:
                    from llama_cpp import Llama
                except ImportError:
                    print("Cannot import llama_cpp module, please make sure llama-cpp-python is installed")
                    return False
                
                print(f"Loading model: {self.local_model_path}")
                print(f"Using configuration: n_gpu_layers={self.n_gpu_layers}, n_threads={self.n_threads}, n_ctx={self.context_size}")
                
                # Load model
                try:
                    self.llama_cpp_model = Llama(
                        model_path=self.local_model_path,
                        n_gpu_layers=self.n_gpu_layers,
                        n_ctx=self.context_size,
                        n_threads=self.n_threads,
                        verbose=False
                    )
                    print("Model loading complete!")
                    return True
                except Exception as e:
                    print(f"Error loading model: {str(e)}")
                    traceback.print_exc()
                    return False
                
            elif self.use_ollama:
                # Check Ollama service
                is_available, message = self._check_ollama_availability()
                if not is_available:
                    print(f"Ollama check failed: {message}")
                    return False
                
                print("Ollama service check passed, model is available")
                return True
            else:
                # Original code for loading models using Transformers
                print("Loading model using Transformers")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.pipe = pipeline(
                    "text-generation",
                    model=self.model_name,
                    tokenizer=self.tokenizer,
                    model_kwargs={"torch_dtype": self.torch_dtype},
                    device_map=self.device,
                )
            
            print("Model preparation complete!")
            return True
        except Exception as e:
            print(f"Model preparation failed: {str(e)}")
            print("Detailed error information:")
            traceback.print_exc()
            return False
    
    def generate_response(self, messages):
        """Generate response
        
        Args:
            messages: List of messages, format is [{"role": "user", "content": "hello"}, ...]
            
        Returns:
            Generated response text
        """
        if self.is_production or self.use_huggingface_api:
            return self._generate_with_huggingface_api(messages)
        elif self.use_llama_cpp:
            return self._generate_with_llama_cpp(messages)
        elif self.use_ollama:
            return self._generate_with_ollama(messages)
        else:
            return self._generate_with_transformers(messages)
    
    def _generate_with_llama_cpp(self, messages):
        """Generate response using llama-cpp-python"""
        try:
            if not self.llama_cpp_model:
                raise ValueError("Model not loaded, please call load_model() first")
            
            # Ensure system prompt is at the beginning of the message list
            if not messages or messages[0].get("role") != "system":
                messages = [{"role": "system", "content": self.system_prompt}] + messages
            
            # Construct prompt
            chat_format = "llama-3"  # Chat format for Llama 3 models
            
            # Use the model's chat method
            response = self.llama_cpp_model.create_chat_completion(
                messages=[{"role": m["role"], "content": m["content"]} for m in messages],
                max_tokens=self.max_new_tokens,
                temperature=0.7,
                top_p=0.9,
                repeat_penalty=1.1,
                stop=["</s>"],
                stream=False
            )
            
            # Extract response
            if "choices" in response and len(response["choices"]) > 0:
                return response["choices"][0]["message"]["content"]
            else:
                return "Unable to generate response"
            
        except Exception as e:
            error_msg = f"Error generating response using llama-cpp: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            return f"Sorry, an error occurred while generating a response: {str(e)}"
    
    def _generate_with_ollama(self, messages):
        """Generate response using Ollama API"""
        try:
            # Ensure system prompt is at the beginning of the message list
            if not messages or messages[0].get("role") != "system":
                messages = [{"role": "system", "content": self.system_prompt}] + messages
            
            # Construct Ollama API request
            api_url = f"{self.ollama_base_url}/api/chat"
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,  # Explicitly specify non-streaming response
                "options": {
                    "num_predict": self.max_new_tokens,
                    "temperature": 0.5,  # Lower temperature for more deterministic responses
                    "top_p": 0.9,        # Add top_p parameter to control diversity
                    "stop": ["</s>"]     # Add stop token
                }
            }
            
            # Send request
            response = requests.post(api_url, json=payload)
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    return result['message']['content']
                except requests.exceptions.JSONDecodeError:
                    # Try parsing JSON response line by line
                    print("Trying to parse response line by line...")
                    lines = response.text.strip().split('\n')
                    if lines and len(lines) > 0:
                        try:
                            # Try to parse the last line of JSON
                            last_json = json.loads(lines[-1])
                            if 'message' in last_json and 'content' in last_json['message']:
                                return last_json['message']['content']
                        except:
                            pass
                    
                    # If unable to parse JSON, return the text response directly
                    print("Unable to parse JSON, returning original response")
                    return f"API response parsing error, original response: {response.text[:200]}..."
            else:
                error_msg = f"Ollama API returned an error: {response.status_code}, {response.text}"
                print(error_msg)
                return f"Error generating response: {error_msg}"
        
        except Exception as e:
            error_msg = f"Error generating response using Ollama: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            return f"Sorry, an error occurred while generating a response: {str(e)}"
    
    def _generate_with_transformers(self, messages):
        """Generate response using Transformers"""
        if not self.pipe:
            raise ValueError("Model not loaded, please call load_model() first")
        
        # Ensure system prompt is at the beginning of the message list
        if not messages or messages[0].get("role") != "system":
            messages = [{"role": "system", "content": self.system_prompt}] + messages
        
        try:
            outputs = self.pipe(
                messages,
                max_new_tokens=self.max_new_tokens,
            )
            
            # Extract the generated response
            response = outputs[0]["generated_text"][-1]["content"]
            return response
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            traceback.print_exc()
            return "Sorry, an error occurred while generating a response."
            
    def _generate_with_huggingface_api(self, messages):
        """Generate response using HuggingFace Inference API"""
        try:
            # Ensure system prompt is at the beginning of the message list
            if not messages or messages[0].get("role") != "system":
                messages = [{"role": "system", "content": self.system_prompt}] + messages
            
            # Construct request headers
            headers = {
                "Authorization": f"Bearer {self.huggingface_api_key}",
                "Content-Type": "application/json"
            }
            
            # Get only the last few messages to avoid context overflow
            # For Llama models, we'll use just the system prompt and the last user message
            last_user_msg = None
            for msg in reversed(messages):
                if msg["role"] == "user":
                    last_user_msg = msg["content"]
                    break
            
            if not last_user_msg:
                return "No user message found to respond to."
            
            # Create a simple prompt with just the system message and last user query
            system_msg = messages[0]["content"]
            prompt = f"<s>[INST] {system_msg} [/INST]</s>\n<s>[INST] {last_user_msg} [/INST]"
            
            # Construct request body for text-generation API
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": self.max_new_tokens,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "repetition_penalty": 1.1,
                    "do_sample": True,
                    "return_full_text": False
                }
            }
            
            # Send request
            response = requests.post(self.huggingface_api_url, headers=headers, json=payload)
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                
                # Extract the generated text from the response
                if isinstance(result, str):
                    # Some models return just the string
                    return result
                elif isinstance(result, list) and len(result) > 0:
                    # Some models return a list with the first item containing the generated text
                    if isinstance(result[0], str):
                        return result[0]
                    elif isinstance(result[0], dict):
                        if "generated_text" in result[0]:
                            # Extract just the generated text, not the prompt
                            generated_text = result[0]["generated_text"]
                            # Remove any prompt artifacts that might be included
                            if "[/INST]" in generated_text:
                                generated_text = generated_text.split("[/INST]", 1)[1].strip()
                            return generated_text
                elif isinstance(result, dict):
                    if "generated_text" in result:
                        generated_text = result["generated_text"]
                        # Remove any prompt artifacts that might be included
                        if "[/INST]" in generated_text:
                            generated_text = generated_text.split("[/INST]", 1)[1].strip()
                        return generated_text
                
                # If we can't parse the result in any of the expected formats,
                # return a generic message and log the full response
                print(f"Unable to parse API response format: {str(result)}")
                return "I'm having trouble generating a response right now. Please try again later."
            else:
                error_msg = f"HuggingFace API returned an error: {response.status_code}, {response.text}"
                print(error_msg)
                return f"Error generating response: {error_msg}"
        
        except Exception as e:
            error_msg = f"Error generating response using HuggingFace API: {str(e)}"
            print(error_msg)
            return f"Sorry, an error occurred while generating a response: {str(e)}"
