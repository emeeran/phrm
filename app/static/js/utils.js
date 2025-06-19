// Optimized utility functions for Personal Health Record Manager

/**
 * File size formatter
 */
export function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
}

/**
 * Enhanced file validation with detailed feedback
 */
export function validateFiles(files) {
    const maxFileSize = 16 * 1024 * 1024; // 16MB
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf', 'text/plain'];
    const errors = [];
    
    Array.from(files).forEach((file) => {
        if (file.size > maxFileSize) {
            errors.push(`File "${file.name}" exceeds the 16MB size limit.`);
        }
        
        if (!allowedTypes.includes(file.type)) {
            errors.push(`File "${file.name}" is not an allowed file type. Please upload JPG, PNG, PDF, or TXT files only.`);
        }
    });
    
    if (errors.length > 0) {
        showNotification('File validation errors:\n\n' + errors.join('\n'), 'error');
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
    const progressElement = document.createElement('div');
    progressElement.className = 'upload-progress';
    progressElement.innerHTML = `
        <div class="progress">
            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                 role="progressbar" style="width: 100%">
                Uploading...
            </div>
        </div>
    `;
    
    document.body.appendChild(progressElement);
    return progressElement;
}

/**
 * Enhanced notification system
 */
export function showNotification(message, type = 'info', duration = 5000) {
    // Remove existing notifications
    const existing = document.querySelectorAll('.notification-toast');
    existing.forEach(el => el.remove());
    
    const notification = document.createElement('div');
    notification.className = `notification-toast alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        max-width: 500px;
    `;
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-dismiss after duration
    if (duration > 0) {
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, duration);
    }
}

/**
 * Debounce function for performance optimization
 */
export function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        
        if (callNow) func(...args);
    };
}

/**
 * Throttle function for performance optimization
 */
export function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Safe API request with error handling
 */
export async function safeApiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        showNotification(`Request failed: ${error.message}`, 'error');
        throw error;
    }
}

/**
 * Format date for display
 */
export function formatDate(date, options = {}) {
    const defaultOptions = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };
    
    return new Intl.DateTimeFormat('en-US', { ...defaultOptions, ...options })
        .format(new Date(date));
}

/**
 * Sanitize HTML to prevent XSS
 */
export function sanitizeHTML(str) {
    const temp = document.createElement('div');
    temp.textContent = str;
    return temp.innerHTML;
}

/**
 * Local storage helper with JSON support
 */
export const storage = {
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.warn('Failed to parse localStorage item:', key);
            return defaultValue;
        }
    },
    
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.warn('Failed to set localStorage item:', key);
            return false;
        }
    },
    
    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.warn('Failed to remove localStorage item:', key);
            return false;
        }
    }
};
