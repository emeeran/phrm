/**
 * Enhanced Chat Manager for PHRM
 * Handles comprehensive chat functionality with improved UI/UX
 */

export class ChatManager {
    constructor() {
        this.chatForm = document.getElementById('chat-form');
        this.chatInput = document.getElementById('chat-input');
        this.chatMessages = document.getElementById('chat-messages');
        this.modeSelector = document.getElementById('mode-selector');
        this.patientSelectorContainer = document.getElementById('patient-selector-container');
        this.chatSidebar = document.getElementById('chat-sidebar');
        this.chatMainArea = document.getElementById('chat-main-area');
        this.typingIndicator = document.getElementById('typing-indicator');
        this.welcomeTitle = document.getElementById('welcome-title');
        this.welcomeText = document.getElementById('welcome-text');
        this.publicDisclaimer = document.getElementById('public-disclaimer');
        this.isTyping = false;
        this.init();
    }

    init() {
        if (!this.chatForm || !this.chatInput || !this.chatMessages) {
            console.log('Chat elements not found on this page');
            return;
        }

        this.setupEventListeners();
        this.setupModeToggle();
        this.setupSuggestionButtons();
        this.updateUIForMode();
        console.log('Enhanced chat manager initialized');
    }

    setupEventListeners() {
        this.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });

        this.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSubmit();
            }
        });

        // Enhanced chat controls
        this.setupChatControls();
    }

    setupChatControls() {
        // New chat button
        const newChatBtn = document.getElementById('new-chat');
        if (newChatBtn) {
            newChatBtn.addEventListener('click', () => this.startNewChat());
        }

        // Clear chat button
        const clearChatBtn = document.getElementById('clear-chat');
        if (clearChatBtn) {
            clearChatBtn.addEventListener('click', () => this.clearChat());
        }

        // Copy chat button
        const copyChatBtn = document.getElementById('copy-chat');
        if (copyChatBtn) {
            copyChatBtn.addEventListener('click', () => this.copyChat());
        }

        // Export markdown button
        const exportMdBtn = document.getElementById('export-md');
        if (exportMdBtn) {
            exportMdBtn.addEventListener('click', () => this.exportToMarkdown());
        }
    }

    startNewChat() {
        if (confirm('Start a new conversation? This will clear the current chat.')) {
            this.clearChat();
            this.showWelcomeMessage();
        }
    }

    clearChat() {
        const messages = this.chatMessages.querySelectorAll('.message');
        messages.forEach(msg => {
            msg.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => msg.remove(), 300);
        });
        setTimeout(() => this.showWelcomeMessage(), 400);
    }

    showWelcomeMessage() {
        const welcomeDiv = document.createElement('div');
        welcomeDiv.className = 'welcome-message text-center text-muted py-4';
        const mode = this.modeSelector ? this.modeSelector.value : 'public';
        
        welcomeDiv.innerHTML = `
            <i class="fas fa-comment-medical fa-3x mb-3"></i>
            <h5 id="welcome-title">${mode === 'public' ? 'Welcome to your Health Assistant' : 'Welcome to your Personal Health Assistant'}</h5>
            <p id="welcome-text">${mode === 'public' ? 'Ask me anything about general health, medications, or symptoms.' : 'Ask me about your health records, medications, or use the quick questions on the left.'}</p>
            ${mode === 'public' ? `
                <div id="public-disclaimer" class="mt-3 p-3 bg-info bg-opacity-10 border border-info rounded">
                    <i class="fas fa-info-circle text-info me-2"></i>
                    <strong>Public Mode:</strong> Responses are based on general medical knowledge. 
                    For personalized advice, switch to Private mode or consult your healthcare provider.
                </div>
            ` : ''}
        `;
        
        this.chatMessages.appendChild(welcomeDiv);
    }

    setupModeToggle() {
        if (this.modeSelector && this.patientSelectorContainer) {
            // Set initial state - hide patient selector in public mode
            this.togglePatientSelector();
            this.updateUIForMode();
            
            this.modeSelector.addEventListener('change', () => {
                this.togglePatientSelector();
                this.updateUIForMode();
            });
        }
    }

    togglePatientSelector() {
        if (!this.modeSelector || !this.patientSelectorContainer) return;
        
        const mode = this.modeSelector.value;
        if (mode === 'public') {
            this.patientSelectorContainer.style.display = 'none';
        } else {
            this.patientSelectorContainer.style.display = 'flex';
        }
    }

    updateUIForMode() {
        const mode = this.modeSelector ? this.modeSelector.value : 'public';
        
        // Show/hide sidebar based on mode
        if (this.chatSidebar && this.chatMainArea) {
            if (mode === 'public') {
                this.chatSidebar.style.display = 'none';
                this.chatMainArea.className = 'col-12 d-flex flex-column h-100';
            } else {
                this.chatSidebar.style.display = 'block';
                this.chatMainArea.className = 'col-md-10 col-lg-11 d-flex flex-column h-100';
            }
        }

        // Update welcome message based on mode
        if (this.welcomeTitle && this.welcomeText) {
            if (mode === 'public') {
                this.welcomeTitle.textContent = 'Welcome to your Health Assistant';
                this.welcomeText.textContent = 'Ask me anything about general health, medications, or symptoms.';
                if (this.publicDisclaimer) this.publicDisclaimer.style.display = 'block';
            } else {
                this.welcomeTitle.textContent = 'Welcome to your Personal Health Assistant';
                this.welcomeText.textContent = 'Ask me about your health records, medications, or use the quick questions on the left.';
                if (this.publicDisclaimer) this.publicDisclaimer.style.display = 'none';
            }
        }

        // Update input placeholder
        if (this.chatInput) {
            if (mode === 'public') {
                this.chatInput.placeholder = 'Ask about general health, medications, symptoms...';
            } else {
                this.chatInput.placeholder = 'Ask about your health, medications, symptoms...';
            }
        }
    }

    setupSuggestionButtons() {
        const suggestionBtns = document.querySelectorAll('.suggestion-btn');
        suggestionBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const message = btn.getAttribute('data-message') || btn.getAttribute('title');
                if (message && this.chatInput) {
                    this.chatInput.value = message;
                    this.handleSubmit();
                }
            });
        });
    }

    async handleSubmit() {
        const message = this.chatInput.value.trim();
        if (!message || this.isTyping) return;

        // Get current mode and patient selection
        const mode = this.modeSelector ? this.modeSelector.value : 'public';
        const patientSelector = document.getElementById('patient-selector');
        const patient = patientSelector ? patientSelector.value : 'self';

        this.addMessage('user', message);
        this.chatInput.value = '';
        this.showTypingIndicator();
        
        this.isTyping = true;
        const loadingId = this.addMessage('assistant', 'Analyzing your question and gathering relevant information...', true);

        try {
            const response = await fetch('/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    mode: mode,
                    patient: patient
                })
            });

            this.hideTypingIndicator();

            if (response.ok) {
                const data = await response.json();
                const modelInfo = data.model ? data.model : null;
                const responseTime = data.response_time ? ` (${data.response_time}s)` : '';
                this.updateMessage(loadingId, data.response || 'No response received', modelInfo, responseTime);
            } else {
                this.updateMessage(loadingId, 'Sorry, I encountered an error processing your request. Please try again.');
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.hideTypingIndicator();
            this.updateMessage(loadingId, 'Network error. Please check your connection and try again.');
        } finally {
            this.isTyping = false;
        }
    }

    showTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'flex';
            this.scrollToBottom();
        }
    }

    hideTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'none';
        }
    }

    addMessage(role, content, isLoading = false) {
        const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        const messageDiv = document.createElement('div');
        messageDiv.id = messageId;
        messageDiv.className = `message ${role}-message`;
        
        const timestamp = new Date().toLocaleString('en-US', {
            year: 'numeric',
            month: 'short', 
            day: 'numeric',
            hour: 'numeric',
            minute: 'numeric',
            hour12: true
        });
        
        if (role === 'user') {
            messageDiv.innerHTML = `
                <div class="d-flex align-items-start gap-2">
                    <div class="chat-avatar user-avatar">
                        <i class="fas fa-user"></i>
                    </div>
                    <div class="message-bubble flex-grow-1">
                        <div class="message-header">
                            <strong>You</strong>
                            <small class="text-muted ms-2">
                                <i class="fas fa-clock me-1"></i>${timestamp}
                            </small>
                        </div>
                        <div class="message-content">${this.escapeHtml(content)}</div>
                    </div>
                </div>
            `;
        } else {
            const loadingClass = isLoading ? 'loading-message' : '';
            messageDiv.innerHTML = `
                <div class="d-flex align-items-start gap-2">
                    <div class="chat-avatar assistant-avatar">
                        <i class="fas fa-robot"></i>
                    </div>
                    <div class="message-bubble flex-grow-1 ${loadingClass}">
                        <div class="message-header">
                            <strong>Health Assistant</strong>
                            <small class="text-muted ms-2">
                                <i class="fas fa-clock me-1"></i>${timestamp}
                            </small>
                        </div>
                        <div class="message-content">${isLoading ? this.createLoadingContent(content) : this.formatResponse(content)}</div>
                    </div>
                </div>
            `;
        }

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        return messageId;
    }

    createLoadingContent(message) {
        return `
            <div class="d-flex align-items-center">
                <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="text-muted">${message}</span>
            </div>
        `;
    }

    updateMessage(messageId, content, modelInfo = null, responseTime = '') {
        const messageElement = document.getElementById(messageId);
        if (messageElement) {
            const contentDiv = messageElement.querySelector('.message-content');
            const headerDiv = messageElement.querySelector('.message-header small');
            const messageBubble = messageElement.querySelector('.message-bubble');
            
            if (contentDiv) {
                contentDiv.innerHTML = this.formatResponse(content);
            }
            
            // Remove loading class
            if (messageBubble) {
                messageBubble.classList.remove('loading-message');
            }
            
            // Add model information to the timestamp if provided
            if (modelInfo && headerDiv) {
                const currentTimestamp = headerDiv.innerHTML;
                // Only add model info if it's not already there
                if (!currentTimestamp.includes('Generated by')) {
                    headerDiv.innerHTML = currentTimestamp + 
                        `<br><i class="fas fa-robot ms-0 me-1 text-primary"></i><span class="fw-bold text-primary">Generated by ${modelInfo}</span>${responseTime}`;
                }
            }
        }
    }

    formatResponse(content) {
        // Enhanced markdown-like formatting with better medical content support
        let formatted = content
            // Headers
            .replace(/^### (.*$)/gim, '<h5 class="mt-3 mb-2 text-primary">$1</h5>')
            .replace(/^## (.*$)/gim, '<h4 class="mt-3 mb-2 text-primary">$1</h4>')
            .replace(/^# (.*$)/gim, '<h3 class="mt-3 mb-2 text-primary">$1</h3>')
            // Bold and italic
            .replace(/\*\*(.*?)\*\*/g, '<strong class="text-dark">$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Medical terms highlighting
            .replace(/\b(medication|symptom|diagnosis|treatment|dosage|side effect)\b/gi, '<span class="badge bg-light text-dark border">$1</span>')
            // Lists
            .replace(/^\* (.+)$/gm, '<li>$1</li>')
            .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
            // Line breaks
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');

        // Wrap in paragraphs if not already wrapped
        if (!formatted.includes('<p>') && !formatted.includes('<h')) {
            formatted = '<p>' + formatted + '</p>';
        }

        // Clean up list formatting
        formatted = formatted.replace(/(<li>.*?<\/li>)/gs, (match) => {
            return '<ul class="list-unstyled ms-3">' + match + '</ul>';
        });

        // Add medical disclaimer for medical-related responses
        if (this.containsMedicalContent(content)) {
            formatted += '<div class="mt-3 p-2 bg-warning bg-opacity-10 border border-warning rounded-2 small">' +
                        '<i class="fas fa-exclamation-triangle text-warning me-2"></i>' +
                        '<strong>Medical Disclaimer:</strong> This information is for educational purposes only and should not replace professional medical advice.' +
                        '</div>';
        }

        return formatted;
    }

    containsMedicalContent(content) {
        const medicalKeywords = ['medication', 'symptom', 'diagnosis', 'treatment', 'dosage', 'prescription', 
                               'side effect', 'disease', 'condition', 'doctor', 'physician', 'therapy'];
        return medicalKeywords.some(keyword => content.toLowerCase().includes(keyword));
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    copyChat() {
        const messages = this.chatMessages.querySelectorAll('.message');
        let chatText = 'Health Assistant Conversation\n';
        chatText += '=' + '='.repeat(30) + '\n\n';
        
        messages.forEach(msg => {
            const header = msg.querySelector('.message-header strong');
            const content = msg.querySelector('.message-content');
            if (header && content) {
                chatText += `${header.textContent}:\n${content.textContent.trim()}\n\n`;
            }
        });
        
        navigator.clipboard.writeText(chatText).then(() => {
            this.showToast('Chat copied to clipboard!', 'success');
        }).catch(() => {
            this.showToast('Failed to copy chat', 'error');
        });
    }

    exportToMarkdown() {
        const messages = this.chatMessages.querySelectorAll('.message');
        let markdown = '# Health Assistant Conversation\n\n';
        markdown += `*Exported on ${new Date().toLocaleString()}*\n\n`;
        
        messages.forEach(msg => {
            const header = msg.querySelector('.message-header strong');
            const content = msg.querySelector('.message-content');
            if (header && content) {
                const isUser = header.textContent === 'You';
                markdown += `## ${header.textContent}\n\n`;
                markdown += `${content.textContent.trim()}\n\n`;
                if (!isUser) markdown += '---\n\n';
            }
        });
        
        const blob = new Blob([markdown], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `health-chat-${new Date().toISOString().split('T')[0]}.md`;
        a.click();
        URL.revokeObjectURL(url);
        
        this.showToast('Chat exported as Markdown!', 'success');
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'error' ? 'danger' : type} position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}-circle me-2"></i>
            ${message}
        `;
        
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}
