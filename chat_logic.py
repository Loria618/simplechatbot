# chat_logic.py 更新版
import json
from llm_handler import LLMHandler

class KnowledgeManager:
    """管理知识库的类"""
    
    def __init__(self, knowledge_path="knowledge.json"):
        """初始化知识库管理器
        
        Args:
            knowledge_path: 知识库文件路径
        """
        self.knowledge_path = knowledge_path
        self.knowledge = self._load_knowledge()
    
    def _load_knowledge(self):
        """加载知识库"""
        try:
            with open(self.knowledge_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # 如果文件不存在或格式错误，创建空知识库
            return {"general": [], "categories": {}}
    
    def save_knowledge(self):
        """保存知识库"""
        with open(self.knowledge_path, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge, f, ensure_ascii=False, indent=4)
    
    def add_knowledge(self, content, category=None):
        """添加知识
        
        Args:
            content: 知识内容
            category: 知识分类，如果为None则添加到通用知识
        
        Returns:
            成功添加的知识ID
        """
        if category:
            if category not in self.knowledge["categories"]:
                self.knowledge["categories"][category] = []
            
            self.knowledge["categories"][category].append(content)
            knowledge_id = f"{category}_{len(self.knowledge['categories'][category]) - 1}"
        else:
            self.knowledge["general"].append(content)
            knowledge_id = f"general_{len(self.knowledge['general']) - 1}"
        
        self.save_knowledge()
        return knowledge_id
    
    def get_knowledge(self, category=None):
        """获取知识
        
        Args:
            category: 知识分类，如果为None则获取所有知识
        
        Returns:
            知识列表
        """
        if category and category in self.knowledge["categories"]:
            return self.knowledge["categories"][category]
        elif category:
            return []
        else:
            # 返回所有知识
            all_knowledge = self.knowledge["general"].copy()
            for category_knowledge in self.knowledge["categories"].values():
                all_knowledge.extend(category_knowledge)
            return all_knowledge
    
    def format_for_prompt(self, category=None, max_items=5):
        """将知识格式化为提示词
        
        Args:
            category: 知识分类，如果为None则使用所有知识
            max_items: 最大知识条目数
        
        Returns:
            格式化后的知识文本
        """
        knowledge_items = self.get_knowledge(category)
        
        # 如果知识太多，只取前max_items条
        if len(knowledge_items) > max_items:
            knowledge_items = knowledge_items[:max_items]
        
        if not knowledge_items:
            return ""
        
        formatted = "以下是你应该了解的重要信息：\n\n"
        for i, item in enumerate(knowledge_items, 1):
            formatted += f"{i}. {item}\n"
        
        return formatted

class ChatSession:
    """管理聊天会话的类"""
    
    def __init__(self, config_path="config.json", knowledge_path="knowledge.json"):
        """初始化聊天会话
        
        Args:
            config_path: 配置文件路径
            knowledge_path: 知识库文件路径
        """
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # 初始化LLM处理器
        self.llm_handler = LLMHandler(config_path)
        
        # 初始化知识库管理器
        self.knowledge_manager = KnowledgeManager(knowledge_path)
        
        # 聊天历史
        self.chat_history = []
        self.max_history = self.config['chat']['max_history']
        
        # 添加系统提示词
        self.update_system_prompt()
    
    def update_system_prompt(self, category=None):
        """更新系统提示词，包含知识库内容
        
        Args:
            category: 知识分类，如果为None则使用所有知识
        """
        base_prompt = self.config['chat']['system_prompt']
        knowledge_text = self.knowledge_manager.format_for_prompt(category)
        
        if knowledge_text:
            system_prompt = f"{base_prompt}\n\n{knowledge_text}"
        else:
            system_prompt = base_prompt
        
        # 更新聊天历史中的系统提示词
        if self.chat_history and self.chat_history[0]["role"] == "system":
            self.chat_history[0]["content"] = system_prompt
        else:
            self.chat_history.insert(0, {"role": "system", "content": system_prompt})
    
    def initialize(self):
        """初始化聊天会话，加载模型"""
        return self.llm_handler.load_model()
    
    def add_message(self, role, content):
        """添加消息到历史记录
        
        Args:
            role: 角色，'user'或'assistant'
            content: 消息内容
        """
        self.chat_history.append({"role": role, "content": content})
        
        # 如果历史记录超过最大长度，删除最早的消息
        # 但保留系统提示词
        if len(self.chat_history) > self.max_history + 1:
            # 如果第一条是系统提示词，保留它
            if self.chat_history[0]["role"] == "system":
                self.chat_history = [self.chat_history[0]] + self.chat_history[-(self.max_history):]
            else:
                self.chat_history = self.chat_history[-self.max_history:]
    
    def get_response(self, user_input, category=None):
        """获取对用户输入的回复
        
        Args:
            user_input: 用户输入的文本
            category: 使用的知识分类，如果为None则使用所有知识
            
        Returns:
            助手的回复文本
        """
        # 如果指定了分类，更新系统提示词
        if category:
            self.update_system_prompt(category)
        
        # 添加用户消息到历史
        self.add_message("user", user_input)
        
        # 获取回复
        response = self.llm_handler.generate_response(self.chat_history)
        
        # 添加助手回复到历史
        self.add_message("assistant", response)
        
        return response
    
    def clear_history(self):
        """清除聊天历史"""
        # 保留系统提示词
        if self.chat_history and self.chat_history[0]["role"] == "system":
            system_prompt = self.chat_history[0]["content"]
            self.chat_history = [{"role": "system", "content": system_prompt}]
        else:
            self.chat_history = []
            # 重新添加系统提示词
            self.update_system_prompt()