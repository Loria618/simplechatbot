// static/script.js
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const chatIcon = document.getElementById('chatIcon');
    const chatContainer = document.getElementById('chatContainer');
    const closeChat = document.getElementById('closeChat');
    const chatBody = document.getElementById('chatBody');
    const userInput = document.getElementById('userInput');
    const sendMessage = document.getElementById('sendMessage');
    const clearChat = document.getElementById('clearChat');
    const presetQuestions = document.querySelectorAll('.question-btn');
    
    // Generate unique client ID
    const clientId = 'client_' + Math.random().toString(36).substr(2, 9);
    
    // WebSocket connection
    let socket;
    
    // Connection status
    let isConnected = false;
    
    // Show/hide chat window
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
    
    // Establish WebSocket connection
    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${clientId}`;
        
        socket = new WebSocket(wsUrl);
        
        socket.onopen = function(e) {
            console.log('WebSocket connection established');
            isConnected = true;
        };
        
        socket.onmessage = function(event) {
            const data = JSON.parse(event.data);
            console.log('Message received:', data);
            
            if (data.type === 'chat') {
                addBotMessage(data.content);
            } else if (data.type === 'status') {
                addSystemMessage(data.content);
            }
        };
        
        socket.onclose = function(event) {
            console.log('WebSocket connection closed', event);
            isConnected = false;
            addSystemMessage('Connection lost, please refresh the page to try again');
        };
        
        socket.onerror = function(error) {
            console.error('WebSocket error:', error);
            isConnected = false;
            addSystemMessage('Connection error, please refresh the page to try again');
        };
    }
    
    // Add user message to chat window
    function addUserMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'user-message';
        messageElement.textContent = message;
        chatBody.appendChild(messageElement);
        chatBody.scrollTop = chatBody.scrollHeight;
    }
    
    // Add bot message to chat window
    function addBotMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'bot-message';
        messageElement.textContent = message;
        chatBody.appendChild(messageElement);
        chatBody.scrollTop = chatBody.scrollHeight;
    }
    
    // Add system message to chat window
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
        <option value="">All</option>
        <option value="Programming">Code</option>
        <option value="Travel">Travel</option>
    `;
    
    // Add category selection to chat footer
    const chatFooter = document.querySelector('.chat-footer');
    chatFooter.insertBefore(categorySelect, userInput);
    
    // Send message
    function sendUserMessage() {
        const message = userInput.value.trim();
        if (message && isConnected) {
            addUserMessage(message);
            
            // Get currently selected category
            const category = categorySelect.value;
            
            socket.send(JSON.stringify({
                type: 'chat',
                content: message,
                category: category || null
            }));
            userInput.value = '';
        }
    }
    
    // Send button click event
    sendMessage.addEventListener('click', sendUserMessage);
    
    // Input box Enter key event
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendUserMessage();
        }
    });
    
    // Clear chat history
    clearChat.addEventListener('click', function() {
        if (isConnected) {
            socket.send(JSON.stringify({
                type: 'clear'
            }));
            // Only keep system messages
            const systemMessages = chatBody.querySelectorAll('.system-message');
            chatBody.innerHTML = '';
            systemMessages.forEach(msg => chatBody.appendChild(msg));
        }
    });
    
    // Preset question click event
    presetQuestions.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const question = this.getAttribute('data-question');
            userInput.value = question;
            sendUserMessage();
        });
    });

    // Add knowledge base management link
    const knowledgeLink = document.createElement('a');
    knowledgeLink.href = '/static/knowledge.html';
    knowledgeLink.textContent = 'Knowledge Base Management';
    knowledgeLink.style.position = 'absolute';
    knowledgeLink.style.top = '10px';
    knowledgeLink.style.right = '10px';
    knowledgeLink.style.color = '#4a6cf7';
    knowledgeLink.style.textDecoration = 'none';
    document.body.appendChild(knowledgeLink);
});