import json
import os
import requests
import traceback
from dotenv import load_dotenv

class HuggingFaceHandler:
    """Class for handling the HuggingFace Inference API"""
    
    def __init__(self, config_path="config.json"):
        """Initialize the HuggingFace handler
        
        Args:
            config_path: Path to the configuration file
        """
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Get API configuration
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")
        
        # Check if huggingface section exists in config
        if 'huggingface' in self.config:
            self.model_name = self.config['huggingface']['model_name']
            # Use the max_new_tokens from huggingface section if available, otherwise from chat section
            self.max_new_tokens = self.config['huggingface'].get('max_new_tokens', 
                                 self.config['chat']['max_new_tokens'])
            self.temperature = self.config['huggingface'].get('temperature', 0.7)
            self.top_p = self.config['huggingface'].get('top_p', 0.9)
            self.repetition_penalty = self.config['huggingface'].get('repetition_penalty', 1.1)
        else:
            # Fallback to model section
            self.model_name = self.config['model'].get('huggingface_model_name', 
                             'meta-llama/Llama-3.2-1B')
            self.max_new_tokens = self.config['chat']['max_new_tokens']
            self.temperature = 0.7
            self.top_p = 0.9
            self.repetition_penalty = 1.1
        
        self.api_url = f"https://api-inference.huggingface.co/models/{self.model_name}"
        
        # System prompt
        self.system_prompt = self.config['chat']['system_prompt']
    
    def is_available(self):
        """Check if HuggingFace API is available"""
        if not self.api_key:
            return False, "HuggingFace API key not set, please set HUGGINGFACE_API_KEY in the .env file"
        
        try:
            # Test API connection
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.head(self.api_url, headers=headers)
            
            if response.status_code == 200:
                return True, "HuggingFace API is available"
            elif response.status_code == 401:
                return False, "Invalid HuggingFace API key"
            elif response.status_code == 404:
                return False, f"Model {self.model_name} not found"
            else:
                return False, f"HuggingFace API returned status code {response.status_code}"
        except Exception as e:
            return False, f"Error connecting to HuggingFace API: {str(e)}"
    
    def generate_response(self, messages):
        """Generate a response
        
        Args:
            messages: List of messages, format is [{"role": "user", "content": "hello"}, ...]
            
        Returns:
            Generated response text
        """
        # Ensure system prompt is at the beginning of the message list
        if not messages or messages[0].get("role") != "system":
            messages = [{"role": "system", "content": self.system_prompt}] + messages
        
        # Construct request headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Construct request body
        payload = {
            "inputs": {
                "messages": messages
            },
            "parameters": {
                "max_new_tokens": self.max_new_tokens,
                "temperature": self.temperature,
                "top_p": self.top_p,
                "repetition_penalty": self.repetition_penalty,
                "do_sample": True
            }
        }
        
        try:
            # Send request
            response = requests.post(self.api_url, headers=headers, json=payload)
            
            # Check response
            if response.status_code == 200:
                result = response.json()
                
                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    if "generated_text" in result[0]:
                        return result[0]["generated_text"]
                    elif "content" in result[0]:
                        return result[0]["content"]
                elif isinstance(result, dict):
                    if "generated_text" in result:
                        return result["generated_text"]
                    elif "content" in result:
                        return result["content"]
                    # For Llama 3 models
                    elif "message" in result and "content" in result["message"]:
                        return result["message"]["content"]
                
                # If parsing fails, return the original response
                print(f"Unable to parse API response: {str(result)}")
                return "I'm having trouble generating a response right now. Please try again later."
            else:
                error_msg = f"HuggingFace API returned an error: {response.status_code}, {response.text}"
                print(error_msg)
                return f"Error generating response: {error_msg}"
        
        except Exception as e:
            error_msg = f"Error generating response using HuggingFace API: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            return f"Sorry, an error occurred while generating a response: {str(e)}"
