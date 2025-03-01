# api_server.py 更新版
from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
import json
import asyncio
import uuid
from chat_logic import ChatSession

app = FastAPI()

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

# 存储活跃的聊天会话
chat_sessions = {}

# 主页路由
@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    with open("static/index.html") as f:
        return f.read()

# 知识库API模型
class KnowledgeItem(BaseModel):
    content: str
    category: str = None

# 获取所有知识
@app.get("/api/knowledge")
async def get_knowledge(category: str = None):
    # 创建临时会话来访问知识库
    temp_session = ChatSession()
    knowledge = temp_session.knowledge_manager.get_knowledge(category)
    
    return {"status": "success", "data": knowledge}

# 添加新知识
@app.post("/api/knowledge")
async def add_knowledge(item: KnowledgeItem):
    # 创建临时会话来访问知识库
    temp_session = ChatSession()
    knowledge_id = temp_session.knowledge_manager.add_knowledge(item.content, item.category)
    
    # 更新所有活跃会话的系统提示词
    for session in chat_sessions.values():
        session.update_system_prompt()
    
    return {"status": "success", "data": {"id": knowledge_id}}

# WebSocket连接处理
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    
    # 为新客户端创建聊天会话
    if client_id not in chat_sessions:
        chat_sessions[client_id] = ChatSession()
        # 初始化模型
        load_status = chat_sessions[client_id].initialize()
        await websocket.send_json({
            "type": "status",
            "content": "模型已加载完成，可以开始聊天了！" if load_status else "模型加载失败！"
        })
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "chat":
                # 获取响应
                category = message.get("category", None)
                response = chat_sessions[client_id].get_response(message["content"], category)
                
                # 发送响应
                await websocket.send_json({
                    "type": "chat",
                    "content": response
                })
            elif message["type"] == "clear":
                # 清除历史
                chat_sessions[client_id].clear_history()
                await websocket.send_json({
                    "type": "status",
                    "content": "聊天历史已清除"
                })
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # 客户端断开时清理资源
        if client_id in chat_sessions:
            # 保留聊天会话，直到会话超时
            pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)