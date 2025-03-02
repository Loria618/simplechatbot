# api_server.py - Updated version
from fastapi import FastAPI, WebSocket, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json
import asyncio
import uuid
import os
from chat_logic import ChatSession
from env_utils import configure_for_environment, is_production, get_port

# Get environment configuration
env_config = configure_for_environment()

# Create FastAPI application
app = FastAPI(
    title="Simple Chatbot API",
    description="A simple chatbot API that can be deployed locally or on Render",
    version="1.0.0"
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Store active chat sessions
chat_sessions = {}

# Homepage route
@app.get("/", response_class=HTMLResponse)
async def get_homepage():
    with open("static/index.html") as f:
        return f.read()

# Knowledge API model
class KnowledgeItem(BaseModel):
    content: str
    category: str = None

# Get all knowledge
@app.get("/api/knowledge")
async def get_knowledge(category: str = None):
    # Create temporary session to access knowledge base
    temp_session = ChatSession()
    knowledge = temp_session.knowledge_manager.get_knowledge(category)
    
    return {"status": "success", "data": knowledge}

# Add new knowledge
@app.post("/api/knowledge")
async def add_knowledge(item: KnowledgeItem):
    # Create temporary session to access knowledge base
    temp_session = ChatSession()
    knowledge_id = temp_session.knowledge_manager.add_knowledge(item.content, item.category)
    
    # Update system prompts for all active sessions
    for session in chat_sessions.values():
        session.update_system_prompt()
    
    return {"status": "success", "data": {"id": knowledge_id}}

# WebSocket connection handler
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    
    # Create chat session for new client
    if client_id not in chat_sessions:
        chat_sessions[client_id] = ChatSession()
        # Initialize model
        load_status = chat_sessions[client_id].initialize()
        await websocket.send_json({
            "type": "status",
            "content": "Model loaded successfully, ready to chat!" if load_status else "Model loading failed!"
        })
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "chat":
                # Get response
                category = message.get("category", None)
                response = chat_sessions[client_id].get_response(message["content"], category)
                
                # Send response
                await websocket.send_json({
                    "type": "chat",
                    "content": response
                })
            elif message["type"] == "clear":
                # Clear history
                chat_sessions[client_id].clear_history()
                await websocket.send_json({
                    "type": "status",
                    "content": "Chat history cleared"
                })
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Clean up resources when client disconnects
        if client_id in chat_sessions:
            # Keep chat session until timeout
            pass

# Health check endpoint for Render to confirm service is running properly
@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": "production" if is_production() else "local"}

if __name__ == "__main__":
    # Use port from environment configuration
    port = get_port()
    print(f"Starting server on port {port}")
    print(f"Environment: {'Production' if is_production() else 'Local'}")
    
    # Output useful information if in production environment
    if is_production():
        print("Running in production mode with HuggingFace API")
    else:
        print("Running in local mode with local model")
    
    uvicorn.run(app, host="0.0.0.0", port=port)