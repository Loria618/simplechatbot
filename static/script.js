// static/script.js
document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const chatIcon = document.getElementById('chatIcon');
    const chatContainer = document.getElementById('chatContainer');
    const closeChat = document.getElementById('closeChat');
    const chatBody = document.getElementById('chatBody');
    const userInput = document.getElementById('userInput');
    const sendMessage = document.getElementById('sendMessage');
    const clearChat = document.getElementById('clearChat');
    const presetQuestions = document.querySelectorAll('.question-btn');
    
    // 生成唯一客户端ID
    const clientId = 'client_' + Math.random().toString(36).substr(2, 9);
    
    // WebSocket连接
    let socket;
    
    // 连接状态
    let isConnected = false;
    
    // 显示/隐藏聊天窗口
    chatIcon.addEventListener('click', function() {
        chatContainer.style.display = 'flex';
        chatIcon.style.display = 'none';
        
        if (!isConnected) {
            connectWebSocket();
        }
    });
    
    closeChat.addEventListener('click', function() {
        chatContainer.style.display = 'none';
        chatIcon.style.display = 'flex';
    });
    
    // 建立WebSocket连接
    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${clientId}`;
        
        socket = new WebSocket(wsUrl);
        
        socket.onopen = function(e) {
            console.log('WebSocket连接已建立');
            isConnected = true;
        };
        
        socket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            console.log('收到消息:', data);
            
            if (data.type === 'chat') {
                addBotMessage(data.content);
            } else if (data.type === 'status') {
                addSystemMessage(data.content);
            }
        };
        
        socket.onclose = function(event) {
            console.log('WebSocket连接已关闭', event);
            isConnected = false;
            addSystemMessage('连接已断开，请刷新页面重试');
        };
        
        socket.onerror = function(error) {
            console.error('WebSocket错误:', error);
            isConnected = false;
            addSystemMessage('连接出错，请刷新页面重试');
        };
    }
    
    // 添加用户消息到聊天窗口
    function addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'user-message';
        messageElement.textContent = message;
        chatBody.appendChild(messageElement);
        chatBody.scrollTop = chatBody.scrollHeight;
    }
    
    // 添加机器人消息到聊天窗口
    function addBotMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'bot-message';
        messageElement.textContent = message;
        chatBody.appendChild(messageElement);
        chatBody.scrollTop = chatBody.scrollHeight;
    }
    
    // 添加系统消息到聊天窗口
    function addSystemMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'system-message';
        messageElement.textContent = message;
        chatBody.appendChild(messageElement);
        chatBody.scrollTop = chatBody.scrollHeight;
    }
    
    const categorySelect = document.createElement('select');
    categorySelect.id = 'categorySelect';
    categorySelect.innerHTML = `
        <option value="">所有知识</option>
        <option value="编程">编程</option>
        <option value="旅游">旅游</option>
    `;
    
    // 将分类选择添加到聊天页脚
    const chatFooter = document.querySelector('.chat-footer');
    chatFooter.insertBefore(categorySelect, userInput);
    
    // 发送消息
    function sendUserMessage() {
        const message = userInput.value.trim();
        if (message && isConnected) {
            addUserMessage(message);
            
            // 获取当前选择的分类
            const category = categorySelect.value;
            
            socket.send(JSON.stringify({
                type: 'chat',
                content: message,
                category: category || null
            }));
            userInput.value = '';
        }
    }
    
    // 发送按钮点击事件
    sendMessage.addEventListener('click', sendUserMessage);
    
    // 输入框回车事件
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendUserMessage();
        }
    });
    
    // 清除聊天历史
    clearChat.addEventListener('click', function() {
        if (isConnected) {
            socket.send(JSON.stringify({
                type: 'clear'
            }));
            // 只保留系统消息
            const systemMessages = chatBody.querySelectorAll('.system-message');
            chatBody.innerHTML = '';
            systemMessages.forEach(msg => chatBody.appendChild(msg));
        }
    });
    
    // 预设问题点击事件
    presetQuestions.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const question = this.getAttribute('data-question');
            userInput.value = question;
            sendUserMessage();
        });
    });

    // 添加知识库管理链接
    const knowledgeLink = document.createElement('a');
    knowledgeLink.href = '/static/knowledge.html';
    knowledgeLink.textContent = '知识库管理';
    knowledgeLink.style.position = 'absolute';
    knowledgeLink.style.top = '10px';
    knowledgeLink.style.right = '10px';
    knowledgeLink.style.color = '#4a6cf7';
    knowledgeLink.style.textDecoration = 'none';
    document.body.appendChild(knowledgeLink);
});