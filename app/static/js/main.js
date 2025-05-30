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

    // Enhanced file upload preview for multiple files
    const documentsInput = document.getElementById('documents-input');
    if (documentsInput) {
        let selectedFiles = [];
        
        documentsInput.addEventListener('change', function (e) {
            const files = Array.from(this.files);
            selectedFiles = files;
            updateFilePreview();
        });
        
        function updateFilePreview() {
            const previewContainer = document.getElementById('file-preview');
            
            if (selectedFiles && selectedFiles.length > 0) {
                previewContainer.style.display = 'block';
                previewContainer.innerHTML = '<div class="d-flex justify-content-between align-items-center mb-3"><h6 class="mb-0">Selected Files (' + selectedFiles.length + '):</h6><button type="button" class="btn btn-sm btn-outline-danger" id="clear-all-files"><i class="fas fa-trash"></i> Clear All</button></div><div class="row" id="file-list"></div>';
                
                const fileList = document.getElementById('file-list');
                
                selectedFiles.forEach((file, index) => {
                    const fileItem = document.createElement('div');
                    fileItem.className = 'col-md-4 mb-3';
                    fileItem.dataset.fileIndex = index;
                    
                    const fileCard = document.createElement('div');
                    fileCard.className = 'card position-relative';
                    
                    let previewContent = '';
                    
                    // Show preview for image files
                    if (file.type.match('image.*')) {
                        const reader = new FileReader();
                        reader.onload = function (e) {
                            const img = fileCard.querySelector('.file-preview-img');
                            if (img) {
                                img.src = e.target.result;
                            }
                        };
                        reader.readAsDataURL(file);
                        previewContent = '<img class="file-preview-img card-img-top" style="height: 120px; object-fit: cover;" alt="Preview">';
                    } else if (file.type === 'application/pdf') {
                        previewContent = '<div class="card-img-top d-flex align-items-center justify-content-center bg-light" style="height: 120px;"><i class="fas fa-file-pdf fa-3x text-danger"></i></div>';
                    } else {
                        previewContent = '<div class="card-img-top d-flex align-items-center justify-content-center bg-light" style="height: 120px;"><i class="fas fa-file fa-3x text-secondary"></i></div>';
                    }
                    
                    fileCard.innerHTML = `
                        ${previewContent}
                        <button type="button" class="btn btn-sm btn-danger position-absolute top-0 end-0 m-1 remove-file-btn" data-file-index="${index}" style="z-index: 5;">
                            <i class="fas fa-times"></i>
                        </button>
                        <div class="card-body p-2">
                            <p class="card-text small text-truncate" title="${file.name}">${file.name}</p>
                            <small class="text-muted">${formatFileSize(file.size)}</small>
                        </div>
                    `;
                    
                    fileItem.appendChild(fileCard);
                    fileList.appendChild(fileItem);
                });
                
                // Add event listeners for remove buttons
                document.querySelectorAll('.remove-file-btn').forEach(btn => {
                    btn.addEventListener('click', function() {
                        const fileIndex = parseInt(this.dataset.fileIndex);
                        removeFile(fileIndex);
                    });
                });
                
                // Add event listener for clear all button
                document.getElementById('clear-all-files').addEventListener('click', function() {
                    selectedFiles = [];
                    updateFileInput();
                    updateFilePreview();
                });
                
            } else {
                previewContainer.style.display = 'none';
                previewContainer.innerHTML = '';
            }
        }
        
        function removeFile(index) {
            selectedFiles.splice(index, 1);
            updateFileInput();
            updateFilePreview();
        }
        
        function updateFileInput() {
            // Create new FileList from selectedFiles
            const dt = new DataTransfer();
            selectedFiles.forEach(file => dt.items.add(file));
            documentsInput.files = dt.files;
        }
    }

    // File upload preview (legacy support for other file inputs)
    const fileInputs = document.querySelectorAll('.file-upload');
    fileInputs.forEach(input => {
        if (input.id !== 'documents-input') { // Skip if it's the enhanced input
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
        }
    });

    // Helper function to format file size
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

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

                // Get current mode and patient selection
                const mode = document.getElementById('mode-selector')?.value || 'private';
                const patient = document.getElementById('patient-selector')?.value || 'self';

                // Send message to backend
                fetch('/ai/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        message: message,
                        mode: mode,
                        patient: patient
                    }),
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

    // Chat Mode and Patient Selector Functionality
    const modeSelector = document.getElementById('mode-selector');
    const patientSelectorContainer = document.getElementById('patient-selector-container');
    const patientSelector = document.getElementById('patient-selector');

    if (modeSelector && patientSelectorContainer) {
        // Handle mode changes
        modeSelector.addEventListener('change', function() {
            const isPrivate = this.value === 'private';
            
            if (isPrivate) {
                patientSelectorContainer.classList.remove('hidden');
            } else {
                patientSelectorContainer.classList.add('hidden');
                // Reset to self when switching to public mode
                if (patientSelector) {
                    patientSelector.value = 'self';
                }
            }
            
            // Update welcome message based on mode
            updateWelcomeMessage();
        });

        // Handle patient selection changes
        if (patientSelector) {
            patientSelector.addEventListener('change', function() {
                updateWelcomeMessage();
            });
        }

        // Function to update welcome message based on current selections
        function updateWelcomeMessage() {
            const welcomeMessage = document.querySelector('.welcome-message');
            if (!welcomeMessage) return;

            const mode = modeSelector.value;
            const patient = patientSelector?.value || 'self';
            
            let messageText = '';
            let contextInfo = '';

            if (mode === 'public') {
                messageText = 'Welcome to your Health Assistant';
                contextInfo = 'Ask me general health questions. I won\'t access your personal medical records in this mode.';
            } else {
                if (patient === 'self') {
                    messageText = 'Welcome to your Health Assistant';
                    contextInfo = 'Ask me anything about your health, medications, or use the quick questions. I have access to your personal medical records.';
                } else {
                    // Get patient name from selector option text
                    const selectedOption = patientSelector.options[patientSelector.selectedIndex];
                    const patientName = selectedOption.text;
                    messageText = `Health Assistant for ${patientName}`;
                    contextInfo = `Ask me about ${patientName}'s health records, medications, or medical history.`;
                }
            }

            welcomeMessage.innerHTML = `
                <i class="fas fa-comment-medical fa-3x mb-3"></i>
                <h5>${messageText}</h5>
                <p>${contextInfo}</p>
            `;
        }

        // Initialize the welcome message
        updateWelcomeMessage();
    }

    // Enhanced drag and drop file upload
    const fileDropAreas = document.querySelectorAll('#documents-input');
    fileDropAreas.forEach(fileInput => {
        const parentDiv = fileInput.closest('.mb-3');
        
        if (parentDiv) {
            // Add drag and drop styling
            parentDiv.style.position = 'relative';
            
            // Create drop overlay
            const dropOverlay = document.createElement('div');
            dropOverlay.className = 'file-drop-overlay';
            dropOverlay.style.cssText = `
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(66, 135, 245, 0.1);
                border: 2px dashed #4287f5;
                border-radius: 0.375rem;
                display: none;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                color: #4287f5;
                z-index: 10;
            `;
            dropOverlay.innerHTML = '<i class="fas fa-cloud-upload-alt fa-2x mb-2"></i><br>Drop files here';
            dropOverlay.style.flexDirection = 'column';
            parentDiv.appendChild(dropOverlay);
            
            // Prevent default drag behaviors
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                parentDiv.addEventListener(eventName, preventDefaults, false);
                document.body.addEventListener(eventName, preventDefaults, false);
            });

            // Highlight drop area when item is dragged over it
            ['dragenter', 'dragover'].forEach(eventName => {
                parentDiv.addEventListener(eventName, () => {
                    dropOverlay.style.display = 'flex';
                }, false);
            });

            ['dragleave', 'drop'].forEach(eventName => {
                parentDiv.addEventListener(eventName, () => {
                    dropOverlay.style.display = 'none';
                }, false);
            });

            // Handle dropped files
            parentDiv.addEventListener('drop', (e) => {
                const dt = e.dataTransfer;
                const files = dt.files;
                
                // Create a new FileList-like object and assign to input
                fileInput.files = files;
                
                // Trigger change event to update preview
                const event = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(event);
            }, false);
        }
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // File validation function
    function validateFiles(files) {
        const maxFileSize = 16 * 1024 * 1024; // 16MB
        const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
        const errors = [];
        
        Array.from(files).forEach((file, index) => {
            // Check file size
            if (file.size > maxFileSize) {
                errors.push(`File "${file.name}" exceeds the 16MB size limit.`);
            }
            
            // Check file type
            if (!allowedTypes.includes(file.type)) {
                errors.push(`File "${file.name}" is not an allowed file type. Please upload JPG, PNG, or PDF files only.`);
            }
        });
        
        if (errors.length > 0) {
            alert('File validation errors:\n\n' + errors.join('\n'));
            return false;
        }
        
        return true;
    }

    // Upload progress indicator
    function showUploadProgress() {
        const progressContainer = document.createElement('div');
        progressContainer.id = 'upload-progress';
        progressContainer.className = 'alert alert-info mt-3';
        progressContainer.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></div>
                <span>Uploading files, please wait...</span>
            </div>
        `;
        
        const submitButton = document.querySelector('form[enctype="multipart/form-data"] button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Uploading...';
            submitButton.parentNode.insertBefore(progressContainer, submitButton);
        }
    }

    // Enhanced form submission handling
    const recordForms = document.querySelectorAll('form[enctype="multipart/form-data"]');
    recordForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const fileInput = this.querySelector('#documents-input');
            if (fileInput && fileInput.files.length > 0) {
                if (!validateFiles(fileInput.files)) {
                    e.preventDefault();
                    return false;
                }
                // Show progress indicator for multiple files
                if (fileInput.files.length > 1) {
                    showUploadProgress();
                }
            }
        });
    });
});