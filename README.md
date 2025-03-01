# 简单本地聊天机器人

这是一个基于Meta Llama 3.2 1B模型的简单本地聊天机器人。

## 功能特点

- 简单直观的用户界面
- 本地运行，无需联网
- 基于Meta Llama 3.2 1B模型
- 支持对话历史记录

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

1. 确保您已经下载了Meta Llama 3.2 1B模型
2. 运行主程序：

```bash
python main.py
```

## 文件结构

- `main.py`: 主程序入口
- `ui.py`: 用户界面相关代码
- `llm_handler.py`: LLM模型加载和调用
- `chat_logic.py`: 对话管理逻辑
- `config.json`: 配置文件
