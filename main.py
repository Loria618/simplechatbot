#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
简单本地聊天机器人主程序
基于Meta Llama 3.1 8B Instruct模型
"""

import os
import sys
import json
from ui import ChatbotUI

def check_config():
    """检查配置文件是否存在，如果不存在则创建默认配置"""
    if not os.path.exists("config.json"):
        default_config = {
            "model": {
                "name": "meta-llama/Meta-Llama-3.1-8B-Instruct",
                "local_path": "",
                "device": "auto",
                "dtype": "bfloat16"
            },
            "ui": {
                "title": "简单本地聊天机器人",
                "width": 800,
                "height": 600,
                "theme": "light"
            },
            "chat": {
                "max_history": 10,
                "system_prompt": "你是一个有用的AI助手。",
                "max_new_tokens": 256
            }
        }
        
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=4)
        
        print("已创建默认配置文件: config.json")

def main():
    """主函数"""
    # 检查配置文件
    check_config()
    
    # 创建并运行UI
    app = ChatbotUI()
    app.run()

if __name__ == "__main__":
    main()
