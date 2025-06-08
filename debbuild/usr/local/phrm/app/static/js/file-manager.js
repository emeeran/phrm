// File upload management for Personal Health Record Manager
import { formatFileSize, validateFiles, preventDefaults } from './utils.js';

export class FileUploadManager {
    constructor(inputId) {
        this.inputElement = document.getElementById(inputId);
        this.selectedFiles = [];
        this.init();
    }

    init() {
        if (!this.inputElement) return;
        
        this.inputElement.addEventListener('change', (e) => {
            this.selectedFiles = Array.from(this.inputElement.files);
            this.updatePreview();
        });

        this.setupDragAndDrop();
    }

    updatePreview() {
        const previewContainer = document.getElementById('file-preview');
        if (!previewContainer) return;

        if (this.selectedFiles.length > 0) {
            previewContainer.style.display = 'block';
            previewContainer.innerHTML = this.generatePreviewHTML();
            this.attachPreviewEventListeners();
        } else {
            previewContainer.style.display = 'none';
            previewContainer.innerHTML = '';
        }
    }

    generatePreviewHTML() {
        const header = `
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0">Selected Files (${this.selectedFiles.length}):</h6>
                <button type="button" class="btn btn-sm btn-outline-danger" id="clear-all-files">
                    <i class="fas fa-trash"></i> Clear All
                </button>
            </div>
            <div class="row" id="file-list">
        `;

        const files = this.selectedFiles.map((file, index) => {
            let previewContent = '';
            
            if (file.type.match('image.*')) {
                previewContent = '<img class="file-preview-img card-img-top" style="height: 120px; object-fit: cover;" alt="Preview">';
            } else if (file.type === 'application/pdf') {
                previewContent = '<div class="card-img-top d-flex align-items-center justify-content-center bg-light" style="height: 120px;"><i class="fas fa-file-pdf fa-3x text-danger"></i></div>';
            } else {
                previewContent = '<div class="card-img-top d-flex align-items-center justify-content-center bg-light" style="height: 120px;"><i class="fas fa-file fa-3x text-secondary"></i></div>';
            }

            return `
                <div class="col-md-4 mb-3" data-file-index="${index}">
                    <div class="card position-relative">
                        ${previewContent}
                        <button type="button" class="btn btn-sm btn-danger position-absolute top-0 end-0 m-1 remove-file-btn" 
                                data-file-index="${index}" style="z-index: 5;">
                            <i class="fas fa-times"></i>
                        </button>
                        <div class="card-body p-2">
                            <p class="card-text small text-truncate" title="${file.name}">${file.name}</p>
                            <small class="text-muted">${formatFileSize(file.size)}</small>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        return header + files + '</div>';
    }

    attachPreviewEventListeners() {
        // Handle image loading for previews
        this.selectedFiles.forEach((file, index) => {
            if (file.type.match('image.*')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    const img = document.querySelector(`[data-file-index="${index}"] .file-preview-img`);
                    if (img) img.src = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        });

        // Remove file buttons
        document.querySelectorAll('.remove-file-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const fileIndex = parseInt(btn.dataset.fileIndex);
                this.removeFile(fileIndex);
            });
        });

        // Clear all button
        const clearAllBtn = document.getElementById('clear-all-files');
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => {
                this.selectedFiles = [];
                this.updateInputFiles();
                this.updatePreview();
            });
        }
    }

    removeFile(index) {
        this.selectedFiles.splice(index, 1);
        this.updateInputFiles();
        this.updatePreview();
    }

    updateInputFiles() {
        const dt = new DataTransfer();
        this.selectedFiles.forEach(file => dt.items.add(file));
        this.inputElement.files = dt.files;
    }

    setupDragAndDrop() {
        const parentDiv = this.inputElement.closest('.mb-3');
        if (!parentDiv) return;

        parentDiv.style.position = 'relative';
        
        const dropOverlay = this.createDropOverlay();
        parentDiv.appendChild(dropOverlay);
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            parentDiv.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });

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

        parentDiv.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            this.inputElement.files = files;
            this.inputElement.dispatchEvent(new Event('change', { bubbles: true }));
        }, false);
    }

    createDropOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'file-drop-overlay';
        overlay.style.cssText = `
            position: absolute; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(66, 135, 245, 0.1); border: 2px dashed #4287f5;
            border-radius: 0.375rem; display: none; align-items: center;
            justify-content: center; font-weight: bold; color: #4287f5;
            z-index: 10; flex-direction: column;
        `;
        overlay.innerHTML = '<i class="fas fa-cloud-upload-alt fa-2x mb-2"></i><br>Drop files here';
        return overlay;
    }
}
