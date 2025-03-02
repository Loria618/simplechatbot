# chat_logic.py - Updated version
import json
import os
from llm_handler import LLMHandler
from env_utils import is_production, configure_for_environment

class KnowledgeManager:
    """Class for managing the knowledge base"""
    
    def __init__(self, knowledge_path="knowledge.json"):
        """Initialize the knowledge base manager
        
        Args:
            knowledge_path: Path to the knowledge base file
        """
        self.knowledge_path = knowledge_path
        self.knowledge = self._load_knowledge()
    
    def _load_knowledge(self):
        """Load the knowledge base"""
        try:
            with open(self.knowledge_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If the file doesn't exist or has incorrect format, create an empty knowledge base
            return {"general": [], "categories": {}}
    
    def save_knowledge(self):
        """Save the knowledge base"""
        with open(self.knowledge_path, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge, f, ensure_ascii=False, indent=4)
    
    def add_knowledge(self, content, category=None):
        """Add knowledge
        
        Args:
            content: Knowledge content
            category: Knowledge category, if None it will be added to general knowledge
        
        Returns:
            ID of the successfully added knowledge
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
        """Get knowledge
        
        Args:
            category: Knowledge category, if None it will get all knowledge
        
        Returns:
            List of knowledge items
        """
        if category and category in self.knowledge["categories"]:
            return self.knowledge["categories"][category]
        elif category:
            return []
        else:
            # Return all knowledge
            all_knowledge = self.knowledge["general"].copy()
            for category_knowledge in self.knowledge["categories"].values():
                all_knowledge.extend(category_knowledge)
            return all_knowledge
    
    def format_for_prompt(self, category=None, max_items=5):
        """Format knowledge for prompt
        
        Args:
            category: Knowledge category, if None it will use all knowledge
            max_items: Maximum number of knowledge items
        
        Returns:
            Formatted knowledge text
        """
        knowledge_items = self.get_knowledge(category)
        
        # If there's too much knowledge, only take the first max_items
        if len(knowledge_items) > max_items:
            knowledge_items = knowledge_items[:max_items]
        
        if not knowledge_items:
            return ""
        
        formatted = "Here is important information you should know:\n\n"
        for i, item in enumerate(knowledge_items, 1):
            formatted += f"{i}. {item}\n"
        
        return formatted

class ChatSession:
    """Class for managing chat sessions"""
    
    def __init__(self, config_path="config.json", knowledge_path="knowledge.json"):
        """Initialize chat session
        
        Args:
            config_path: Path to configuration file
            knowledge_path: Path to knowledge base file
        """
        # Get environment configuration
        self.env_config = configure_for_environment()
        
        # Load configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
            
        # If in production environment, update configuration to use HuggingFace API
        if is_production():
            self.config['model']['use_huggingface_api'] = True
            self.config['model']['use_ollama'] = False
            self.config['model']['use_llama_cpp'] = False
            print("Production environment detected, using HuggingFace API")
        
        # Initialize LLM handler
        self.llm_handler = LLMHandler(config_path)
        
        # Initialize knowledge base manager
        self.knowledge_manager = KnowledgeManager(knowledge_path)
        
        # Chat history
        self.chat_history = []
        self.max_history = self.config['chat']['max_history']
        
        # Add system prompt
        self.update_system_prompt()
    
    def update_system_prompt(self, category=None):
        """Update system prompt, including knowledge base content
        
        Args:
            category: Knowledge category, if None it will use all knowledge
        """
        base_prompt = self.config['chat']['system_prompt']
        knowledge_text = self.knowledge_manager.format_for_prompt(category)
        
        if knowledge_text:
            system_prompt = f"{base_prompt}\n\n{knowledge_text}"
        else:
            system_prompt = base_prompt
        
        # Update system prompt in chat history
        if self.chat_history and self.chat_history[0]["role"] == "system":
            self.chat_history[0]["content"] = system_prompt
        else:
            self.chat_history.insert(0, {"role": "system", "content": system_prompt})
    
    def initialize(self):
        """Initialize chat session, load model"""
        return self.llm_handler.load_model()
    
    def add_message(self, role, content):
        """Add message to history
        
        Args:
            role: Role, 'user' or 'assistant'
            content: Message content
        """
        self.chat_history.append({"role": role, "content": content})
        
        # If history exceeds maximum length, delete the oldest messages
        # but keep the system prompt
        if len(self.chat_history) > self.max_history + 1:
            # If the first message is a system prompt, keep it
            if self.chat_history[0]["role"] == "system":
                self.chat_history = [self.chat_history[0]] + self.chat_history[-(self.max_history):]
            else:
                self.chat_history = self.chat_history[-self.max_history:]
    
    def get_response(self, user_input, category=None):
        """Get response to user input
        
        Args:
            user_input: User input text
            category: Knowledge category to use, if None it will use all knowledge
            
        Returns:
            Assistant's response text
        """
        # If a category is specified, update the system prompt
        if category:
            self.update_system_prompt(category)
        
        # Add user message to history
        self.add_message("user", user_input)
        
        # Get response
        response = self.llm_handler.generate_response(self.chat_history)
        
        # Add assistant response to history
        self.add_message("assistant", response)
        
        return response
    
    def clear_history(self):
        """Clear chat history"""
        # Keep system prompt
        if self.chat_history and self.chat_history[0]["role"] == "system":
            system_prompt = self.chat_history[0]["content"]
            self.chat_history = [{"role": "system", "content": system_prompt}]
        else:
            self.chat_history = []
            # Re-add system prompt
            self.update_system_prompt()