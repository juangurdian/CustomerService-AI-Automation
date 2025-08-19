(function() {
    'use strict';
    
    // Configuration
    const WIDGET_CONFIG = {
        apiEndpoint: window.location.origin + '/webhook/web',
        position: 'bottom-right',
        primaryColor: '#2563EB',
        title: 'Chat con nosotros'
    };
    
    // Generate unique user ID
    function generateUserId() {
        let userId = localStorage.getItem('ai-bot-user-id');
        if (!userId) {
            userId = 'web_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
            localStorage.setItem('ai-bot-user-id', userId);
        }
        return userId;
    }
    
    // Create widget HTML
    function createWidget() {
        const widgetHTML = `
            <div id="ai-chat-widget" style="
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 9999;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            ">
                <!-- Chat Button -->
                <div id="chat-button" style="
                    width: 60px;
                    height: 60px;
                    background: ${WIDGET_CONFIG.primaryColor};
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    transition: all 0.3s ease;
                " onclick="toggleChat()">
                    <svg width="24" height="24" fill="white" viewBox="0 0 24 24">
                        <path d="M12 2C6.48 2 2 6.48 2 12c0 1.54.36 3.04 1.05 4.36L2 22l5.64-1.05C9.96 21.64 10.46 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm0 18c-1.29 0-2.51-.3-3.64-.84L4 20l.84-4.36C4.3 14.51 4 13.29 4 12c0-4.41 3.59-8 8-8s8 3.59 8 8-3.59 8-8 8z"/>
                        <path d="M7 12h2v2H7zm4-1h2v3h-2zm4-1h2v3h-2z"/>
                    </svg>
                </div>
                
                <!-- Chat Window -->
                <div id="chat-window" style="
                    position: absolute;
                    bottom: 80px;
                    right: 0;
                    width: 350px;
                    height: 500px;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
                    display: none;
                    flex-direction: column;
                    overflow: hidden;
                ">
                    <!-- Header -->
                    <div style="
                        background: ${WIDGET_CONFIG.primaryColor};
                        color: white;
                        padding: 16px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    ">
                        <div>
                            <h3 style="margin: 0; font-size: 16px; font-weight: 600;">${WIDGET_CONFIG.title}</h3>
                            <p style="margin: 0; font-size: 12px; opacity: 0.9;">En línea</p>
                        </div>
                        <button onclick="toggleChat()" style="
                            background: none;
                            border: none;
                            color: white;
                            font-size: 20px;
                            cursor: pointer;
                            padding: 4px;
                        ">×</button>
                    </div>
                    
                    <!-- Messages -->
                    <div id="chat-messages" style="
                        flex: 1;
                        padding: 16px;
                        overflow-y: auto;
                        background: #f8fafc;
                    ">
                        <div class="bot-message">
                            <div style="
                                background: white;
                                padding: 12px;
                                border-radius: 12px;
                                margin-bottom: 12px;
                                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                                max-width: 80%;
                            ">
                                <p style="margin: 0; font-size: 14px; line-height: 1.4;">
                                    ¡Hola! Soy el asistente virtual. ¿En qué te puedo ayudar?
                                </p>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Quick Replies -->
                    <div id="quick-replies" style="
                        padding: 0 16px;
                        display: none;
                    "></div>
                    
                    <!-- Input -->
                    <div style="
                        padding: 16px;
                        border-top: 1px solid #e2e8f0;
                        background: white;
                    ">
                        <div style="display: flex; gap: 8px;">
                            <input 
                                type="text" 
                                id="chat-input" 
                                placeholder="Escribe tu mensaje..."
                                style="
                                    flex: 1;
                                    border: 1px solid #d1d5db;
                                    border-radius: 8px;
                                    padding: 8px 12px;
                                    font-size: 14px;
                                    outline: none;
                                "
                                onkeypress="handleChatKeyPress(event)"
                            >
                            <button 
                                onclick="sendChatMessage()" 
                                style="
                                    background: ${WIDGET_CONFIG.primaryColor};
                                    color: white;
                                    border: none;
                                    border-radius: 8px;
                                    padding: 8px 16px;
                                    cursor: pointer;
                                    font-size: 14px;
                                "
                            >
                                Enviar
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', widgetHTML);
    }
    
    // Toggle chat window
    window.toggleChat = function() {
        const chatWindow = document.getElementById('chat-window');
        const isVisible = chatWindow.style.display === 'flex';
        chatWindow.style.display = isVisible ? 'none' : 'flex';
        
        if (!isVisible) {
            document.getElementById('chat-input').focus();
        }
    };
    
    // Handle chat input
    window.handleChatKeyPress = function(event) {
        if (event.key === 'Enter') {
            sendChatMessage();
        }
    };
    
    // Send message
    window.sendChatMessage = async function() {
        const input = document.getElementById('chat-input');
        const text = input.value.trim();
        if (!text) return;
        
        // Add user message
        addChatMessage(text, 'user');
        input.value = '';
        
        // Clear quick replies
        document.getElementById('quick-replies').style.display = 'none';
        
        try {
            const response = await fetch(WIDGET_CONFIG.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    user_id: generateUserId()
                })
            });
            
            const result = await response.json();
            
            // Add bot response
            addChatMessage(result.message, 'bot');
            
            // Show quick replies if available
            if (result.quick_replies && result.quick_replies.length > 0) {
                showQuickReplies(result.quick_replies);
            }
            
        } catch (error) {
            addChatMessage('Lo siento, hubo un error. Intenta de nuevo.', 'bot');
            console.error('Chat error:', error);
        }
    };
    
    // Add message to chat
    function addChatMessage(text, type) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = type + '-message';
        
        const alignment = type === 'user' ? 'flex-end' : 'flex-start';
        const bgColor = type === 'user' ? WIDGET_CONFIG.primaryColor : 'white';
        const textColor = type === 'user' ? 'white' : '#374151';
        const maxWidth = type === 'user' ? '80%' : '80%';
        
        messageDiv.innerHTML = `
            <div style="
                background: ${bgColor};
                color: ${textColor};
                padding: 12px;
                border-radius: 12px;
                margin-bottom: 12px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                max-width: ${maxWidth};
                align-self: ${alignment};
                word-wrap: break-word;
            ">
                <p style="margin: 0; font-size: 14px; line-height: 1.4;">${text}</p>
            </div>
        `;
        
        messagesContainer.style.display = 'flex';
        messagesContainer.style.flexDirection = 'column';
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Show quick replies
    function showQuickReplies(replies) {
        const quickRepliesContainer = document.getElementById('quick-replies');
        quickRepliesContainer.innerHTML = '';
        
        replies.forEach(reply => {
            const button = document.createElement('button');
            button.style.cssText = `
                background: #f1f5f9;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
                padding: 6px 12px;
                margin: 4px;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s;
            `;
            button.textContent = reply;
            button.onclick = () => {
                document.getElementById('chat-input').value = reply;
                sendChatMessage();
            };
            
            button.onmouseover = () => {
                button.style.background = '#e2e8f0';
            };
            button.onmouseout = () => {
                button.style.background = '#f1f5f9';
            };
            
            quickRepliesContainer.appendChild(button);
        });
        
        quickRepliesContainer.style.display = 'block';
    }
    
    // Initialize widget when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createWidget);
    } else {
        createWidget();
    }
    
})();