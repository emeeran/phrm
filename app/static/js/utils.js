// Utility functions for Personal Health Record Manager

/**
 * File size formatter
 */
export function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * File validation
 */
export function validateFiles(files) {
    const maxFileSize = 16 * 1024 * 1024; // 16MB
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
    const errors = [];
    
    Array.from(files).forEach((file) => {
        if (file.size > maxFileSize) {
            errors.push(`File "${file.name}" exceeds the 16MB size limit.`);
        }
        
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

/**
 * Prevent default drag behaviors
 */
export function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

/**
 * Show upload progress indicator
 */
export function showUploadProgress() {
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
