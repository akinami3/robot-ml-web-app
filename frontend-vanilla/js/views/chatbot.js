// Chatbot View
import { api } from '../services/api.js';

export class ChatbotView {
    constructor() {
        this.messages = [];
        this.isLoading = false;
    }

    render() {
        const view = document.createElement('div');
        view.className = 'view chatbot-view';
        view.innerHTML = `
            <div class="view-header">
                <h1>Chatbot</h1>
                <p class="subtitle">Ask questions about the robot and web application</p>
            </div>

            <div class="chatbot-container">
                <div class="chat-messages" id="chatMessages">
                    <div class="message assistant">
                        <div class="message-content">
                            こんにちは！Robot ML Web Applicationについて質問があればお答えします。
                        </div>
                    </div>
                </div>

                <div class="chat-input-container">
                    <input 
                        type="text" 
                        class="input" 
                        id="chatInput" 
                        placeholder="メッセージを入力..."
                        autocomplete="off"
                    >
                    <button class="btn btn-primary" id="sendBtn">送信</button>
                </div>
            </div>
        `;
        return view;
    }

    init() {
        this.setupChatInput();
        
        // Add initial assistant message to messages array
        this.messages.push({
            role: 'assistant',
            content: 'こんにちは！Robot ML Web Applicationについて質問があればお答えします。',
        });
    }

    setupChatInput() {
        const input = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendBtn');

        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
        }

        if (input) {
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !this.isLoading) {
                    this.sendMessage();
                }
            });
        }
    }

    async sendMessage() {
        const input = document.getElementById('chatInput');
        if (!input || !input.value.trim()) return;

        const userMessage = input.value.trim();
        input.value = '';

        // Add user message
        this.messages.push({
            role: 'user',
            content: userMessage,
        });
        this.renderMessages();

        // Show loading state
        this.isLoading = true;
        this.updateSendButton();
        this.addLoadingMessage();

        try {
            const response = await api.post('/api/v1/chatbot/message', {
                message: userMessage,
                conversation_history: this.messages.slice(0, -1), // Exclude the loading message
            });

            // Remove loading message
            this.removeLoadingMessage();

            // Add assistant response
            const assistantMessage = response.content || response.message || 'すみません、理解できませんでした。';
            this.messages.push({
                role: 'assistant',
                content: assistantMessage,
            });
            
            this.renderMessages();
        } catch (error) {
            console.error('Failed to send message:', error);
            
            // Remove loading message
            this.removeLoadingMessage();
            
            // Add error message
            this.messages.push({
                role: 'assistant',
                content: 'エラーが発生しました。もう一度お試しください。',
            });
            
            this.renderMessages();
        } finally {
            this.isLoading = false;
            this.updateSendButton();
        }
    }

    renderMessages() {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;

        messagesContainer.innerHTML = this.messages.map(msg => `
            <div class="message ${msg.role}">
                <div class="message-content">${this.escapeHtml(msg.content)}</div>
            </div>
        `).join('');

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    addLoadingMessage() {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;

        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant';
        loadingDiv.id = 'loadingMessage';
        loadingDiv.innerHTML = `
            <div class="message-content">
                <span class="loading"></span>
            </div>
        `;
        messagesContainer.appendChild(loadingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    removeLoadingMessage() {
        const loadingMessage = document.getElementById('loadingMessage');
        if (loadingMessage) {
            loadingMessage.remove();
        }
    }

    updateSendButton() {
        const sendBtn = document.getElementById('sendBtn');
        const input = document.getElementById('chatInput');
        
        if (sendBtn) {
            sendBtn.disabled = this.isLoading;
            sendBtn.textContent = this.isLoading ? '送信中...' : '送信';
        }
        
        if (input) {
            input.disabled = this.isLoading;
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    cleanup() {
        // No cleanup needed for chatbot view
    }
}
