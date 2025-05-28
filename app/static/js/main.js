// Main JavaScript for Personal Health Record Manager

document.addEventListener('DOMContentLoaded', function () {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Initialize Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    const popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    });

    // File upload preview
    const fileInputs = document.querySelectorAll('.file-upload');
    fileInputs.forEach(input => {
        input.addEventListener('change', function (e) {
            const fileLabel = this.nextElementSibling;
            if (this.files && this.files.length > 0) {
                const fileNames = Array.from(this.files).map(file => file.name).join(', ');
                fileLabel.textContent = fileNames;

                // Show preview for image files
                if (this.files[0].type.match('image.*')) {
                    const reader = new FileReader();
                    reader.onload = function (e) {
                        const previewContainer = document.querySelector('.file-preview');
                        if (previewContainer) {
                            previewContainer.innerHTML = `<img src="${e.target.result}" class="img-fluid img-thumbnail mb-3" alt="Preview">`;
                        }
                    }
                    reader.readAsDataURL(this.files[0]);
                }
            } else {
                fileLabel.textContent = 'Choose file...';
            }
        });
    });

    // Health Record filtering
    const filterButtons = document.querySelectorAll('.filter-btn');
    if (filterButtons.length > 0) {
        filterButtons.forEach(button => {
            button.addEventListener('click', function () {
                const filter = this.dataset.filter;
                const records = document.querySelectorAll('.record-item');

                filterButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');

                if (filter === 'all') {
                    records.forEach(record => record.style.display = 'block');
                } else {
                    records.forEach(record => {
                        if (record.dataset.type === filter) {
                            record.style.display = 'block';
                        } else {
                            record.style.display = 'none';
                        }
                    });
                }
            });
        });
    }

    // Confirmation modals
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(button => {
        button.addEventListener('click', function (e) {
            if (!confirm(this.dataset.confirm)) {
                e.preventDefault();
            }
        });
    });

    // Dynamic form fields for medications
    const addMedBtn = document.getElementById('add-medication');
    if (addMedBtn) {
        let medicationCount = document.querySelectorAll('.medication-item').length;

        addMedBtn.addEventListener('click', function () {
            const medicationsContainer = document.getElementById('medications-container');
            const newMedication = document.createElement('div');
            newMedication.className = 'medication-item row mb-3';
            newMedication.innerHTML = `
                <div class="col-md-4">
                    <input type="text" class="form-control" name="medication_name_${medicationCount}" placeholder="Medication Name" required>
                </div>
                <div class="col-md-3">
                    <input type="text" class="form-control" name="medication_dosage_${medicationCount}" placeholder="Dosage">
                </div>
                <div class="col-md-3">
                    <input type="text" class="form-control" name="medication_frequency_${medicationCount}" placeholder="Frequency">
                </div>
                <div class="col-md-2">
                    <button type="button" class="btn btn-danger remove-medication">Remove</button>
                </div>
            `;
            medicationsContainer.appendChild(newMedication);
            medicationCount++;

            // Add event listener to the new remove button
            newMedication.querySelector('.remove-medication').addEventListener('click', function () {
                this.closest('.medication-item').remove();
            });
        });

        // Event delegation for removing medication fields
        document.addEventListener('click', function (e) {
            if (e.target && e.target.classList.contains('remove-medication')) {
                e.target.closest('.medication-item').remove();
            }
        });
    }

    // Enhanced AI Chat Interface
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const voiceInputBtn = document.getElementById('voice-input-btn');
    const clearChatBtn = document.getElementById('clear-chat');
    const suggestionBtns = document.querySelectorAll('.suggestion-btn');

    if (chatForm && chatInput && chatMessages) {
        // Store conversation history
        let conversationHistory = [];

        // Load conversation from localStorage if available
        try {
            const savedConversation = localStorage.getItem('chatConversation');
            if (savedConversation) {
                const parsedHistory = JSON.parse(savedConversation);

                // Only restore if there's actual history and it's properly formatted
                if (Array.isArray(parsedHistory) && parsedHistory.length > 0) {
                    // Don't show the first welcome message again if we're restoring history
                    chatMessages.innerHTML = '';

                    parsedHistory.forEach(entry => {
                        appendMessage(entry.role, entry.content, entry.timestamp);
                    });

                    conversationHistory = parsedHistory;

                    // Scroll to bottom
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                }
            }
        } catch (e) {
            console.error('Error loading conversation history:', e);
            // If loading fails, just continue with empty history
        }

        // Set focus to chat input
        chatInput.focus();

        // Handle suggestion buttons
        if (suggestionBtns) {
            suggestionBtns.forEach(btn => {
                btn.addEventListener('click', function () {
                    const questionText = this.textContent.trim();
                    chatInput.value = questionText;
                    chatForm.dispatchEvent(new Event('submit'));
                });
            });
        }

        // Clear chat history
        if (clearChatBtn) {
            clearChatBtn.addEventListener('click', function () {
                if (confirm('Are you sure you want to clear the conversation history?')) {
                    // Clear the chat UI
                    chatMessages.innerHTML = '';

                    // Clear conversation history
                    conversationHistory = [];
                    localStorage.removeItem('chatConversation');
                }
            });
        }

        // Copy chat conversation
        const copyChatBtn = document.getElementById('copy-chat');
        if (copyChatBtn) {
            copyChatBtn.addEventListener('click', function () {
                if (conversationHistory.length === 0) {
                    alert('No conversation to copy');
                    return;
                }

                const chatText = conversationHistory.map(entry => {
                    const sender = entry.role === 'user' ? 'You' : 'Health Assistant';
                    const time = new Date(entry.timestamp).toLocaleString();
                    return `${sender} (${time}):\n${entry.content}\n`;
                }).join('\n');

                navigator.clipboard.writeText(chatText).then(() => {
                    // Show temporary success feedback
                    const originalHTML = copyChatBtn.innerHTML;
                    copyChatBtn.innerHTML = '<i class="fas fa-check"></i>';
                    copyChatBtn.classList.add('btn-success');
                    copyChatBtn.classList.remove('btn-outline-light');
                    
                    setTimeout(() => {
                        copyChatBtn.innerHTML = originalHTML;
                        copyChatBtn.classList.remove('btn-success');
                        copyChatBtn.classList.add('btn-outline-light');
                    }, 2000);
                }).catch(err => {
                    console.error('Failed to copy text: ', err);
                    alert('Failed to copy conversation to clipboard');
                });
            });
        }

        // Export chat to Markdown
        const exportMdBtn = document.getElementById('export-md');
        if (exportMdBtn) {
            exportMdBtn.addEventListener('click', function () {
                if (conversationHistory.length === 0) {
                    alert('No conversation to export');
                    return;
                }

                const today = new Date();
                const dateStr = today.toISOString().split('T')[0];
                const timeStr = today.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                let markdownContent = `# Health Assistant Conversation\n\n`;
                markdownContent += `**Date:** ${dateStr} at ${timeStr}\n\n`;
                markdownContent += `**Total Messages:** ${conversationHistory.length}\n\n`;
                markdownContent += `---\n\n`;

                conversationHistory.forEach((entry, index) => {
                    const sender = entry.role === 'user' ? '👤 You' : '🤖 Health Assistant';
                    const time = new Date(entry.timestamp).toLocaleString();
                    
                    markdownContent += `## ${sender}\n`;
                    markdownContent += `*${time}*\n\n`;
                    markdownContent += `${entry.content}\n\n`;
                    
                    if (index < conversationHistory.length - 1) {
                        markdownContent += `---\n\n`;
                    }
                });

                // Create and download the file
                const blob = new Blob([markdownContent], { type: 'text/markdown' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `health_conversation_${dateStr}_${timeStr.replace(':', '-')}.md`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

                // Show temporary success feedback
                const originalHTML = exportMdBtn.innerHTML;
                exportMdBtn.innerHTML = '<i class="fas fa-check"></i>';
                exportMdBtn.classList.add('btn-success');
                exportMdBtn.classList.remove('btn-outline-light');
                
                setTimeout(() => {
                    exportMdBtn.innerHTML = originalHTML;
                    exportMdBtn.classList.remove('btn-success');
                    exportMdBtn.classList.add('btn-outline-light');
                }, 2000);
            });
        }

        // Voice input functionality
        if (voiceInputBtn && 'webkitSpeechRecognition' in window) {
            const recognition = new webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = true;
            recognition.lang = 'en-US';

            let isListening = false;

            voiceInputBtn.addEventListener('click', function () {
                if (!isListening) {
                    // Start listening
                    recognition.start();
                    isListening = true;
                    voiceInputBtn.classList.add('voice-active');
                    voiceInputBtn.title = 'Stop listening';

                    // Show feedback to user
                    chatInput.placeholder = 'Listening...';
                } else {
                    // Stop listening
                    recognition.stop();
                    isListening = false;
                    voiceInputBtn.classList.remove('voice-active');
                    voiceInputBtn.title = 'Voice input';

                    // Restore placeholder
                    chatInput.placeholder = 'Type your health question here...';
                }
            });

            recognition.onresult = function (event) {
                const transcript = Array.from(event.results)
                    .map(result => result[0])
                    .map(result => result.transcript)
                    .join('');

                chatInput.value = transcript;
            };

            recognition.onend = function () {
                isListening = false;
                voiceInputBtn.classList.remove('voice-active');
                voiceInputBtn.title = 'Voice input';
                chatInput.placeholder = 'Type your health question here...';
            };
        } else if (voiceInputBtn) {
            // Hide the button if speech recognition is not supported
            voiceInputBtn.style.display = 'none';
        }

        // Submit message on enter key (but allow shift+enter for new line)
        chatInput.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event('submit'));
            }
        });

        chatForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const message = chatInput.value.trim();
            if (message) {
                // Add user message to chat with current time
                const timestamp = new Date().toISOString();
                appendMessage('user', message, timestamp);
                chatInput.value = '';

                // Save to conversation history
                conversationHistory.push({
                    role: 'user',
                    content: message,
                    timestamp: timestamp
                });

                // Save to localStorage
                localStorage.setItem('chatConversation', JSON.stringify(conversationHistory));

                // Show typing indicator
                const typingIndicator = document.createElement('div');
                typingIndicator.className = 'typing-indicator';
                typingIndicator.innerHTML = `
                    <span></span>
                    <span></span>
                    <span></span>
                `;
                chatMessages.appendChild(typingIndicator);
                chatMessages.scrollTop = chatMessages.scrollHeight;

                // Send message to backend
                fetch('/ai/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message }),
                })
                    .then(response => response.json())
                    .then(data => {
                        // Remove typing indicator
                        chatMessages.removeChild(typingIndicator);

                        // Add AI response with current time
                        const responseTimestamp = new Date().toISOString();
                        appendMessage('assistant', data.response, responseTimestamp);

                        // Save to conversation history
                        conversationHistory.push({
                            role: 'assistant',
                            content: data.response,
                            timestamp: responseTimestamp
                        });

                        // Save to localStorage
                        localStorage.setItem('chatConversation', JSON.stringify(conversationHistory));
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        chatMessages.removeChild(typingIndicator);

                        const errorTimestamp = new Date().toISOString();
                        appendMessage('assistant', 'Sorry, there was an error processing your request. Please try again.', errorTimestamp);

                        // Save error message to history
                        conversationHistory.push({
                            role: 'assistant',
                            content: 'Sorry, there was an error processing your request. Please try again.',
                            timestamp: errorTimestamp
                        });

                        // Save to localStorage
                        localStorage.setItem('chatConversation', JSON.stringify(conversationHistory));
                    });
            }
        });

        function appendMessage(sender, text, timestamp) {
            const messageElement = document.createElement('div');
            messageElement.className = `chat-message ${sender}-message`;

            const time = new Date(timestamp);
            const formattedTime = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

            // Create message structure with avatar
            let avatarIcon = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
            let senderName = sender === 'user' ? 'You' : 'Health Assistant';

            // For user messages, display as plain text. For assistant messages, render markdown.
            let messageContent;
            if (sender === 'user') {
                messageContent = `<div>${text}</div>`;
            } else {
                // Use the marked library to render markdown to HTML
                try {
                    // Add markdown-body class for GitHub-style markdown
                    messageContent = `<div class="markdown-body">${marked.parse(text)}</div>`;
                } catch (e) {
                    console.error('Error rendering markdown:', e);
                    messageContent = `<div>${text}</div>`;
                }
            }

            messageElement.innerHTML = `
                <div class="chat-avatar">
                    ${avatarIcon}
                </div>
                <div class="message-content">
                    <div class="message-sender">${senderName} <span class="message-time">${formattedTime}</span></div>
                    ${messageContent}
                </div>
            `;

            // Add to chat container and scroll to bottom
            chatMessages.appendChild(messageElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    // Date range picker for record filtering
    const dateRangePicker = document.getElementById('date-range-picker');
    if (dateRangePicker) {
        const today = new Date();
        const lastMonth = new Date();
        lastMonth.setMonth(lastMonth.getMonth() - 1);

        // If using a date range picker library like daterangepicker.js
        // This is a placeholder for implementation with an actual library
        $(dateRangePicker).daterangepicker({
            startDate: lastMonth,
            endDate: today,
            ranges: {
                'Today': [today, today],
                'Yesterday': [new Date(today - 86400000), new Date(today - 86400000)],
                'Last 7 Days': [new Date(today - 6 * 86400000), today],
                'Last 30 Days': [new Date(today - 29 * 86400000), today],
                'This Month': [new Date(today.getFullYear(), today.getMonth(), 1), new Date(today.getFullYear(), today.getMonth() + 1, 0)],
                'Last Month': [new Date(today.getFullYear(), today.getMonth() - 1, 1), new Date(today.getFullYear(), today.getMonth(), 0)]
            }
        }, function (start, end) {
            // Filter records based on date range
            filterRecordsByDate(start, end);
        });

        function filterRecordsByDate(start, end) {
            const records = document.querySelectorAll('.record-item');
            records.forEach(record => {
                const recordDate = new Date(record.dataset.date);
                if (recordDate >= start && recordDate <= end) {
                    record.style.display = 'block';
                } else {
                    record.style.display = 'none';
                }
            });
        }
    }
});