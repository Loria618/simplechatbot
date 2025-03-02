#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Local Chatbot Main Program
Based on Meta Llama 3.1 8B Instruct model
"""

import os
import sys
import json
from ui import ChatbotUI

def check_config():
    """Check if the configuration file exists, if not, create a default configuration"""
    if not os.path.exists("config.json"):
        default_config = {
            "model": {
                "name": "meta-llama/Meta-Llama-3.1-8B-Instruct",
                "local_path": "",
                "device": "auto",
                "dtype": "bfloat16"
            },
            "ui": {
                "title": "Simple Local Chatbot",
                "width": 800,
                "height": 600,
                "theme": "light"
            },
            "chat": {
                "max_history": 10,
                "system_prompt": "You are a helpful AI assistant.",
                "max_new_tokens": 256
            }
        }
        
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)
        
        print("Default configuration file created: config.json")

def main():
    """Main function"""
    # Check configuration file
    check_config()
    
    # Create and run UI
    app = ChatbotUI()
    app.run()

if __name__ == "__main__":
    main()
