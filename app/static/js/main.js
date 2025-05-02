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

    // AI Chat Interface
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');

    if (chatForm && chatInput && chatMessages) {
        chatForm.addEventListener('submit', function (e) {
            e.preventDefault();

            const message = chatInput.value.trim();
            if (message) {
                // Add user message to chat
                appendMessage('user', message);
                chatInput.value = '';

                // Show loading spinner
                const loadingElement = document.createElement('div');
                loadingElement.className = 'chat-message bot-message';
                loadingElement.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"><span class="visually-hidden">Loading...</span></div> Thinking...';
                chatMessages.appendChild(loadingElement);
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
                        // Remove loading element
                        chatMessages.removeChild(loadingElement);

                        // Add AI response
                        appendMessage('bot', data.response);
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        chatMessages.removeChild(loadingElement);
                        appendMessage('bot', 'Sorry, there was an error processing your request.');
                    });
            }
        });

        function appendMessage(sender, text) {
            const messageElement = document.createElement('div');
            messageElement.className = `chat-message ${sender}-message`;
            messageElement.textContent = text;
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