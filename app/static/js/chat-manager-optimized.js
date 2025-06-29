/**
 * PHRM Chat Manager - Optimized Version
 * Consolidated chat functionality using unified utilities
 */

import { notifications, storage, apiRequest, debounce, formatDate, formatTime } from './core-utils.js';
import UIManager from './ui-manager.js';

export class ChatManager {
    constructor() {
        this.chatForm = null;
        this.chatInput = null;
        this.chatMessages = null;
        this.conversationHistory = [];
        this.isProcessing = false;
        
        this.init();
    }

    init() {
        // Get DOM elements
        this.chatForm = document.getElementById('chat-form');
        this.chatInput = document.getElementById('chat-input');
        this.chatMessages = document.getElementById('chat-messages');
        
        if (!this.chatForm || !this.chatInput || !this.chatMessages) {
            return; // Chat not available on this page
        }

        this.loadConversationHistory();
        this.setupEventListeners();
        this.setupControlButtons();
        this.setupModeHandling();
        this.initializeUI();
    }

    loadConversationHistory() {
        const history = storage.get('chatConversation', []);
        if (Array.isArray(history) && history.length > 0) {
            this.conversationHistory = history;
            this.renderConversationHistory();
        }
    }

    renderConversationHistory() {
        this.chatMessages.innerHTML = '';
        this.conversationHistory.forEach(entry => {
            this.addMessage(entry.role, entry.content, entry.timestamp, entry.model);
        });
        this.scrollToBottom();
    }

    setupEventListeners() {
        // Form submission
        this.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });

        // Enter key handling
        this.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSubmit();
            }
        });

        // Suggestion buttons
        document.querySelectorAll('.suggestion-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.chatInput.value = btn.textContent.trim();
                this.handleSubmit();
            });
        });

        // Auto-resize textarea
        this.chatInput.addEventListener('input', debounce(() => {
            this.autoResizeTextarea();
        }, 100));
    }

    setupControlButtons() {
        const controls = {
            'new-chat': () => this.startNewChat(),
            'clear-chat': () => this.clearChat(),
            'copy-chat': () => this.copyChat(),
            'export-md': () => this.exportToMarkdown()
        };

        Object.entries(controls).forEach(([id, handler]) => {
            const btn = document.getElementById(id);
            if (btn) {
                btn.addEventListener('click', handler);
            }
        });
    }

    setupModeHandling() {
        const modeSelector = document.getElementById('mode-selector');
        const patientContainer = document.getElementById('patient-selector-container');
        const patientSelector = document.getElementById('patient-selector');

        if (modeSelector && patientContainer) {
            modeSelector.addEventListener('change', () => {
                this.updateModeDisplay();
            });

            if (patientSelector) {
                patientSelector.addEventListener('change', () => {
                    this.updateWelcomeMessage();
                });
            }

            this.updateModeDisplay();
        }
    }

    updateModeDisplay() {
        const modeSelector = document.getElementById('mode-selector');
        const patientContainer = document.getElementById('patient-selector-container');
        
        if (!modeSelector || !patientContainer) return;

        const isPrivate = modeSelector.value === 'private';
        patientContainer.style.display = isPrivate ? 'flex' : 'none';
        
        this.updateWelcomeMessage();
    }

    updateWelcomeMessage() {
        const welcomeEl = document.querySelector('.welcome-message');
        if (!welcomeEl) return;

        const mode = document.getElementById('mode-selector')?.value || 'public';
        const patient = document.getElementById('patient-selector')?.value || 'self';

        let title, description;

        if (mode === 'public') {
            title = 'Welcome to your Health Assistant';
            description = 'Ask me general health questions. I won\'t access your personal medical records in this mode.';
        } else {
            if (patient === 'self') {
                title = 'Welcome to your Personal Health Assistant';
                description = 'Ask me about your health records, medications, or medical history.';
            } else {
                const patientName = document.getElementById('patient-selector')?.selectedOptions[0]?.text || 'Patient';
                title = `Health Assistant for ${patientName}`;
                description = `Ask me about ${patientName}'s health records, medications, or medical history.`;
            }
        }

        welcomeEl.innerHTML = `
            <i class="fas fa-comment-medical fa-3x mb-3 text-primary"></i>
            <h5 class="mb-3">${title}</h5>
            <p class="text-muted">${description}</p>
        `;
    }

    initializeUI() {
        this.autoResizeTextarea();
        this.updateWelcomeMessage();
        this.chatInput.focus();
    }

    async handleSubmit() {
        if (this.isProcessing) {
            notifications.warning('Please wait for the current response to complete.');
            return;
        }

        const message = this.chatInput.value.trim();
        if (!message) return;

        this.isProcessing = true;

        // Add user message
        const timestamp = new Date().toISOString();
        this.addMessage('user', message, timestamp);
        this.addToHistory('user', message, timestamp);

        // Clear input and show processing
        this.chatInput.value = '';
        this.autoResizeTextarea();
        
        const processingId = this.showProcessingIndicator();

        try {
            const response = await this.sendMessage(message);
            
            // Remove processing indicator
            this.removeProcessingIndicator(processingId);
            
            // Add assistant response
            const responseTime = new Date().toISOString();
            this.addMessage('assistant', response.response, responseTime, response.model);
            this.addToHistory('assistant', response.response, responseTime, response.model);

        } catch (error) {
            this.removeProcessingIndicator(processingId);
            
            const errorMsg = 'Sorry, there was an error processing your request. Please try again.';
            const errorTime = new Date().toISOString();
            
            this.addMessage('assistant', errorMsg, errorTime);
            this.addToHistory('assistant', errorMsg, errorTime);
            
            notifications.error('Failed to get response from health assistant.');
        } finally {
            this.isProcessing = false;
        }
    }

    async sendMessage(message) {
        const mode = document.getElementById('mode-selector')?.value || 'private';
        const patient = document.getElementById('patient-selector')?.value || 'self';

        return apiRequest('/ai/chat', {
            method: 'POST',
            body: JSON.stringify({
                message,
                mode,
                patient
            })
        });
    }

    showProcessingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'message assistant-message processing';
        indicator.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-sender">Health Assistant</span>
                    <span class="message-time">${formatTime(new Date())}</span>
                </div>
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;

        this.chatMessages.appendChild(indicator);
        this.scrollToBottom();
        
        return indicator;
    }

    removeProcessingIndicator(indicator) {
        if (indicator && indicator.parentNode) {
            indicator.parentNode.removeChild(indicator);
        }
    }

    addMessage(role, content, timestamp, model = 'Health Assistant') {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${role}-message`;

        const time = formatTime(new Date(timestamp));
        const avatar = role === 'user' ? 
            '<i class="fas fa-user"></i>' : 
            '<i class="fas fa-robot"></i>';
        
        const sender = role === 'user' ? 'You' : model;

        let processedContent;
        if (role === 'assistant' && window.marked) {
            try {
                processedContent = window.marked.parse(content);
            } catch (e) {
                processedContent = content;
            }
        } else {
            processedContent = content;
        }

        messageEl.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-sender">${sender}</span>
                    <span class="message-time">${time}</span>
                </div>
                <div class="message-text">${processedContent}</div>
            </div>
        `;

        this.chatMessages.appendChild(messageEl);
        this.scrollToBottom();
    }

    addToHistory(role, content, timestamp, model = null) {
        const entry = { role, content, timestamp };
        if (model) entry.model = model;
        
        this.conversationHistory.push(entry);
        this.saveConversation();
    }

    saveConversation() {
        storage.set('chatConversation', this.conversationHistory);
    }

    startNewChat() {
        if (this.conversationHistory.length === 0) {
            notifications.info('No conversation to clear.');
            return;
        }

        if (confirm('Start a new conversation? This will clear the current chat.')) {
            this.clearChat();
            notifications.success('New conversation started.');
        }
    }

    clearChat() {
        this.chatMessages.innerHTML = '';
        this.conversationHistory = [];
        storage.remove('chatConversation');
        this.updateWelcomeMessage();
    }

    copyChat() {
        if (this.conversationHistory.length === 0) {
            notifications.warning('No conversation to copy.');
            return;
        }

        const chatText = this.conversationHistory.map((entry, index) => {
            const sender = entry.role === 'user' ? 'You' : (entry.model || 'Health Assistant');
            const time = formatDate(new Date(entry.timestamp)) + ' ' + formatTime(new Date(entry.timestamp));
            return `${sender} (${time}):\n${entry.content}\n`;
        }).join('\n');

        navigator.clipboard.writeText(chatText).then(() => {
            notifications.success('Chat copied to clipboard!');
        }).catch(() => {
            notifications.error('Failed to copy chat to clipboard.');
        });
    }

    exportToMarkdown() {
        if (this.conversationHistory.length === 0) {
            notifications.warning('No conversation to export.');
            return;
        }

        let markdown = '# Health Assistant Conversation\n\n';
        markdown += `**Date:** ${formatDate(new Date())}\n`;
        markdown += `**Messages:** ${this.conversationHistory.length}\n\n---\n\n`;

        this.conversationHistory.forEach((entry, index) => {
            const sender = entry.role === 'user' ? '👤 You' : '🤖 Health Assistant';
            const time = formatDate(new Date(entry.timestamp)) + ' ' + formatTime(new Date(entry.timestamp));
            
            markdown += `## ${sender}\n`;
            markdown += `*${time}*\n\n`;
            markdown += `${entry.content}\n\n`;
        });

        const blob = new Blob([markdown], { type: 'text/markdown' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `health-chat-${formatDate(new Date(), { year: 'numeric', month: '2-digit', day: '2-digit' }).replace(/\//g, '-')}.md`;
        
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        notifications.success('Chat exported successfully!');
    }

    autoResizeTextarea() {
        this.chatInput.style.height = 'auto';
        this.chatInput.style.height = Math.min(this.chatInput.scrollHeight, 120) + 'px';
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
}

// Auto-initialize if on a page with chat
export default ChatManager;
