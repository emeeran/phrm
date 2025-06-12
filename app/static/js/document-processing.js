// Document Processing Status Manager
// Handles real-time updates for document vectorization status

export class DocumentProcessingManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupStatusPolling();
        this.setupStatusUpdates();
    }

    /**
     * Poll for document processing status updates
     */
    setupStatusPolling() {
        // Check for documents that are currently being processed
        const processingDocs = document.querySelectorAll('.badge.bg-warning');
        
        if (processingDocs.length > 0) {
            // Start polling every 5 seconds
            this.statusInterval = setInterval(() => {
                this.checkProcessingStatus();
            }, 5000);
        }
    }

    /**
     * Check the processing status of documents
     */
    async checkProcessingStatus() {
        try {
            const response = await fetch('/api/documents/status', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateDocumentStatuses(data.documents);
            }
        } catch (error) {
            console.error('Error checking document status:', error);
        }
    }

    /**
     * Update document status badges
     */
    updateDocumentStatuses(documents) {
        documents.forEach(doc => {
            const statusBadge = document.querySelector(`[data-document-id="${doc.id}"] .status-badge`);
            
            if (statusBadge) {
                if (doc.vectorized) {
                    statusBadge.className = 'badge bg-success status-badge';
                    statusBadge.innerHTML = '<i class="fas fa-check-circle me-1"></i>AI Ready';
                    
                    // Show success animation
                    this.showStatusAnimation(statusBadge, 'success');
                    
                    // Stop polling if all documents are processed
                    this.checkIfAllProcessed();
                } else if (doc.processing_error) {
                    statusBadge.className = 'badge bg-danger status-badge';
                    statusBadge.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i>Error';
                    
                    this.showStatusAnimation(statusBadge, 'error');
                }
            }
        });
    }

    /**
     * Show status change animation
     */
    showStatusAnimation(element, type) {
        element.style.animation = 'pulse 0.5s ease-in-out';
        
        setTimeout(() => {
            element.style.animation = '';
        }, 500);
    }

    /**
     * Check if all documents are processed and stop polling
     */
    checkIfAllProcessed() {
        const processingDocs = document.querySelectorAll('.badge.bg-warning');
        
        if (processingDocs.length === 0 && this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
    }

    /**
     * Setup status updates for new uploads
     */
    setupStatusUpdates() {
        // Listen for form submissions with file uploads
        document.addEventListener('submit', (e) => {
            const form = e.target;
            
            if (form.enctype === 'multipart/form-data') {
                const fileInput = form.querySelector('#documents-input');
                
                if (fileInput && fileInput.files.length > 0) {
                    this.showUploadingStatus(fileInput.files.length);
                }
            }
        });
    }

    /**
     * Show uploading and processing status
     */
    showUploadingStatus(fileCount) {
        // Create or update status message
        let statusContainer = document.getElementById('upload-status-container');
        
        if (!statusContainer) {
            statusContainer = document.createElement('div');
            statusContainer.id = 'upload-status-container';
            statusContainer.className = 'alert alert-info mt-3';
            
            const form = document.querySelector('form[enctype="multipart/form-data"]');
            if (form) {
                form.appendChild(statusContainer);
            }
        }

        statusContainer.innerHTML = `
            <div class="d-flex align-items-center">
                <div class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></div>
                <div>
                    <strong>Processing ${fileCount} document(s)...</strong><br>
                    <small>
                        <i class="fas fa-upload me-1"></i>Uploading files<br>
                        <i class="fas fa-font me-1"></i>Extracting text content<br>
                        <i class="fas fa-brain me-1"></i>Vectorizing for AI queries
                    </small>
                </div>
            </div>
        `;
    }

    /**
     * Start real-time vectorization status monitoring
     */
    startVectorizationMonitoring(documentIds) {
        if (!documentIds || documentIds.length === 0) return;

        const checkStatus = async () => {
            try {
                const response = await fetch('/api/documents/vectorization-status', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ document_ids: documentIds })
                });

                if (response.ok) {
                    const data = await response.json();
                    
                    data.documents.forEach(doc => {
                        this.updateVectorizationStatus(doc);
                    });

                    // Continue polling if any documents are still processing
                    const stillProcessing = data.documents.some(doc => !doc.vectorized && !doc.error);
                    
                    if (stillProcessing) {
                        setTimeout(checkStatus, 2000); // Check every 2 seconds
                    } else {
                        this.onVectorizationComplete(data.documents);
                    }
                }
            } catch (error) {
                console.error('Error checking vectorization status:', error);
            }
        };

        // Start checking after a short delay
        setTimeout(checkStatus, 1000);
    }

    /**
     * Update vectorization status for a specific document
     */
    updateVectorizationStatus(docData) {
        const statusElement = document.querySelector(`[data-document-id="${docData.id}"] .vectorization-status`);
        
        if (statusElement) {
            if (docData.vectorized) {
                statusElement.innerHTML = '<i class="fas fa-check-circle text-success"></i> Vectorized';
                statusElement.className = 'vectorization-status text-success';
            } else if (docData.error) {
                statusElement.innerHTML = '<i class="fas fa-exclamation-triangle text-danger"></i> Error';
                statusElement.className = 'vectorization-status text-danger';
            } else {
                statusElement.innerHTML = '<i class="fas fa-spinner fa-spin text-primary"></i> Processing...';
                statusElement.className = 'vectorization-status text-primary';
            }
        }
    }

    /**
     * Handle completion of all vectorization processes
     */
    onVectorizationComplete(documents) {
        const successful = documents.filter(doc => doc.vectorized).length;
        const total = documents.length;

        // Show completion message
        const statusContainer = document.getElementById('upload-status-container');
        if (statusContainer) {
            if (successful === total) {
                statusContainer.className = 'alert alert-success mt-3';
                statusContainer.innerHTML = `
                    <div class="d-flex align-items-center">
                        <i class="fas fa-check-circle text-success me-2"></i>
                        <div>
                            <strong>All documents processed successfully!</strong><br>
                            <small>Your documents are now available for AI queries.</small>
                        </div>
                    </div>
                `;
            } else {
                statusContainer.className = 'alert alert-warning mt-3';
                statusContainer.innerHTML = `
                    <div class="d-flex align-items-center">
                        <i class="fas fa-exclamation-triangle text-warning me-2"></i>
                        <div>
                            <strong>Processing completed with some issues</strong><br>
                            <small>${successful}/${total} documents processed successfully.</small>
                        </div>
                    </div>
                `;
            }

            // Auto-hide after 5 seconds
            setTimeout(() => {
                statusContainer.style.opacity = '0';
                setTimeout(() => statusContainer.remove(), 300);
            }, 5000);
        }
    }
}
