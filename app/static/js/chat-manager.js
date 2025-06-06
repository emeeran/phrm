// Chat functionality for Personal Health Record Manager

export class ChatManager {
    constructor() {
        this.chatForm = document.getElementById('chat-form');
        this.chatInput = document.getElementById('chat-input');
        this.chatMessages = document.getElementById('chat-messages');
        this.conversationHistory = [];
        this.init();
    }

    init() {
        if (!this.chatForm || !this.chatInput || !this.chatMessages) return;
        
        this.loadConversationHistory();
        this.setupEventListeners();
        this.initializeVoiceInput();
        this.initializeModeSelectors();
        this.chatInput.focus();
    }

    loadConversationHistory() {
        try {
            const saved = localStorage.getItem('chatConversation');
            if (saved) {
                const parsed = JSON.parse(saved);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    this.chatMessages.innerHTML = '';
                    parsed.forEach(entry => {
                        this.appendMessage(entry.role, entry.content, entry.timestamp);
                    });
                    this.conversationHistory = parsed;
                    this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
                }
            }
        } catch (e) {
            console.error('Error loading conversation history:', e);
        }
    }

    setupEventListeners() {
        // Submit on Enter (allow Shift+Enter for new line)
        this.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSubmit();
            }
        });

        this.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });

        // Suggestion buttons
        document.querySelectorAll('.suggestion-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.chatInput.value = btn.textContent.trim();
                this.handleSubmit();
            });
        });

        // Action buttons
        this.setupActionButtons();
    }

    setupActionButtons() {
        const clearBtn = document.getElementById('clear-chat');
        const copyBtn = document.getElementById('copy-chat');
        const exportBtn = document.getElementById('export-md');

        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                if (confirm('Are you sure you want to clear the conversation history?')) {
                    this.clearConversation();
                }
            });
        }

        if (copyBtn) {
            copyBtn.addEventListener('click', () => this.copyConversation(copyBtn));
        }

        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportToMarkdown(exportBtn));
        }
    }

    initializeVoiceInput() {
        const voiceBtn = document.getElementById('voice-input-btn');
        if (!voiceBtn || !('webkitSpeechRecognition' in window)) {
            if (voiceBtn) voiceBtn.style.display = 'none';
            return;
        }

        const recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'en-US';
        
        let isListening = false;

        voiceBtn.addEventListener('click', () => {
            if (!isListening) {
                recognition.start();
                isListening = true;
                voiceBtn.classList.add('voice-active');
                voiceBtn.title = 'Stop listening';
                this.chatInput.placeholder = 'Listening...';
            } else {
                recognition.stop();
                isListening = false;
                voiceBtn.classList.remove('voice-active');
                voiceBtn.title = 'Voice input';
                this.chatInput.placeholder = 'Type your health question here...';
            }
        });

        recognition.onresult = (event) => {
            const transcript = Array.from(event.results)
                .map(result => result[0].transcript)
                .join('');
            this.chatInput.value = transcript;
        };

        recognition.onend = () => {
            isListening = false;
            voiceBtn.classList.remove('voice-active');
            voiceBtn.title = 'Voice input';
            this.chatInput.placeholder = 'Type your health question here...';
        };
    }

    initializeModeSelectors() {
        const modeSelector = document.getElementById('mode-selector');
        const patientContainer = document.getElementById('patient-selector-container');
        const patientSelector = document.getElementById('patient-selector');

        if (!modeSelector || !patientContainer) return;

        modeSelector.addEventListener('change', () => {
            const isPrivate = modeSelector.value === 'private';
            patientContainer.classList.toggle('hidden', !isPrivate);
            if (!isPrivate && patientSelector) {
                patientSelector.value = 'self';
            }
            this.updateWelcomeMessage();
        });

        if (patientSelector) {
            patientSelector.addEventListener('change', () => this.updateWelcomeMessage());
        }

        // Initialize state
        const isPrivate = modeSelector.value === 'private';
        patientContainer.classList.toggle('hidden', !isPrivate);
        this.updateWelcomeMessage();
    }

    updateWelcomeMessage() {
        const welcomeMsg = document.querySelector('.welcome-message');
        if (!welcomeMsg) return;

        const mode = document.getElementById('mode-selector')?.value || 'public';
        const patient = document.getElementById('patient-selector')?.value || 'self';
        
        let messageText, contextInfo;

        if (mode === 'public') {
            messageText = 'Welcome to your Health Assistant';
            contextInfo = 'Ask me general health questions. I won\'t access your personal medical records in this mode.';
        } else {
            if (patient === 'self') {
                messageText = 'Welcome to your Health Assistant';
                contextInfo = 'Ask me anything about your health, medications, or use the quick questions. I have access to your personal medical records.';
            } else {
                const patientSelector = document.getElementById('patient-selector');
                const patientName = patientSelector?.options[patientSelector.selectedIndex]?.text || 'Patient';
                messageText = `Health Assistant for ${patientName}`;
                contextInfo = `Ask me about ${patientName}'s health records, medications, or medical history.`;
            }
        }

        welcomeMsg.innerHTML = `
            <i class="fas fa-comment-medical fa-3x mb-3"></i>
            <h5>${messageText}</h5>
            <p>${contextInfo}</p>
        `;
    }

    async handleSubmit() {
        const message = this.chatInput.value.trim();
        if (!message) return;

        const timestamp = new Date().toISOString();
        this.appendMessage('user', message, timestamp);
        this.chatInput.value = '';

        this.conversationHistory.push({
            role: 'user',
            content: message,
            timestamp: timestamp
        });
        this.saveConversation();

        const typingIndicator = this.showTypingIndicator();

        try {
            const response = await this.sendMessage(message);
            this.chatMessages.removeChild(typingIndicator);
            
            const responseTimestamp = new Date().toISOString();
            this.appendMessage('assistant', response.response, responseTimestamp, response.model);
            
            this.conversationHistory.push({
                role: 'assistant',
                content: response.response,
                timestamp: responseTimestamp
            });
            this.saveConversation();
        } catch (error) {
            console.error('Chat error:', error);
            this.chatMessages.removeChild(typingIndicator);
            
            const errorMsg = 'Sorry, there was an error processing your request. Please try again.';
            const errorTimestamp = new Date().toISOString();
            this.appendMessage('assistant', errorMsg, errorTimestamp);
            
            this.conversationHistory.push({
                role: 'assistant',
                content: errorMsg,
                timestamp: errorTimestamp
            });
            this.saveConversation();
        }
    }

    async sendMessage(message) {
        const mode = document.getElementById('mode-selector')?.value || 'private';
        const patient = document.getElementById('patient-selector')?.value || 'self';

        const response = await fetch('/ai/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, mode, patient }),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response.json();
    }

    showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = '<span></span><span></span><span></span>';
        this.chatMessages.appendChild(indicator);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        return indicator;
    }

    appendMessage(sender, text, timestamp, model = 'MedGemma') {
        const messageEl = document.createElement('div');
        messageEl.className = `chat-message ${sender}-message`;

        const time = new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const avatarIcon = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        const senderName = sender === 'user' ? 'You' : `Health Assistant [${model}]`;

        let messageContent;
        if (sender === 'user') {
            messageContent = `<div>${text}</div>`;
        } else {
            try {
                messageContent = `<div class="markdown-body">${marked.parse(text)}</div>`;
            } catch (e) {
                console.error('Error rendering markdown:', e);
                messageContent = `<div>${text}</div>`;
            }
        }

        messageEl.innerHTML = `
            <div class="chat-avatar">${avatarIcon}</div>
            <div class="message-content">
                <div class="message-sender">${senderName} <span class="message-time">${time}</span></div>
                ${messageContent}
            </div>
        `;

        this.chatMessages.appendChild(messageEl);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    saveConversation() {
        localStorage.setItem('chatConversation', JSON.stringify(this.conversationHistory));
    }

    clearConversation() {
        this.chatMessages.innerHTML = '';
        this.conversationHistory = [];
        localStorage.removeItem('chatConversation');
    }

    copyConversation(button) {
        if (this.conversationHistory.length === 0) {
            alert('No conversation to copy');
            return;
        }

        const chatText = this.conversationHistory.map(entry => {
            const sender = entry.role === 'user' ? 'You' : 'Health Assistant';
            const time = new Date(entry.timestamp).toLocaleString();
            return `${sender} (${time}):\n${entry.content}\n`;
        }).join('\n');

        navigator.clipboard.writeText(chatText).then(() => {
            this.showButtonFeedback(button, 'success');
        }).catch(err => {
            console.error('Failed to copy text:', err);
            alert('Failed to copy conversation to clipboard');
        });
    }

    exportToMarkdown(button) {
        if (this.conversationHistory.length === 0) {
            alert('No conversation to export');
            return;
        }

        const today = new Date();
        const dateStr = today.toISOString().split('T')[0];
        const timeStr = today.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        let content = `# Health Assistant Conversation\n\n`;
        content += `**Date:** ${dateStr} at ${timeStr}\n`;
        content += `**Total Messages:** ${this.conversationHistory.length}\n\n---\n\n`;

        this.conversationHistory.forEach((entry, index) => {
            const sender = entry.role === 'user' ? '👤 You' : '🤖 Health Assistant';
            const time = new Date(entry.timestamp).toLocaleString();
            
            content += `## ${sender}\n*${time}*\n\n${entry.content}\n\n`;
            if (index < this.conversationHistory.length - 1) content += `---\n\n`;
        });

        const blob = new Blob([content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `health_conversation_${dateStr}_${timeStr.replace(':', '-')}.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showButtonFeedback(button, 'success');
    }

    showButtonFeedback(button, type) {
        const originalHTML = button.innerHTML;
        const originalClasses = button.className;
        
        button.innerHTML = '<i class="fas fa-check"></i>';
        button.className = button.className.replace('btn-outline-light', `btn-${type}`);
        
        setTimeout(() => {
            button.innerHTML = originalHTML;
            button.className = originalClasses;
        }, 2000);
    }
}
