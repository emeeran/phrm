/**
 * PHRM Core Utilities - Consolidated and Optimized
 * Unified utility functions for the Personal Health Record Manager
 */

// ============================================================================
// PERFORMANCE UTILITIES
// ============================================================================

/**
 * Debounce function for performance optimization
 */
export function debounce(func, wait, immediate = false) {
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

// ============================================================================
// UNIFIED NOTIFICATION SYSTEM
// ============================================================================

class NotificationManager {
    constructor() {
        this.container = this.createContainer();
        this.notifications = new Map();
        this.nextId = 1;
    }
    
    createContainer() {
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'notification-container';
            container.style.cssText = `
                position: fixed;
                top: 1rem;
                right: 1rem;
                z-index: 10000;
                pointer-events: none;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }
    
    show(message, type = 'info', duration = 5000, actions = []) {
        const id = this.nextId++;
        const notification = this.createNotification(id, message, type, duration, actions);
        
        this.container.appendChild(notification);
        this.notifications.set(id, notification);
        
        // Trigger animation
        requestAnimationFrame(() => {
            notification.classList.add('show');
        });
        
        // Auto-dismiss
        if (duration > 0) {
            setTimeout(() => this.dismiss(id), duration);
        }
        
        return id;
    }
    
    createNotification(id, message, type, duration, actions) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            pointer-events: auto;
            margin-bottom: 0.75rem;
            padding: 1rem;
            border-radius: 0.5rem;
            background: var(--bs-${type === 'error' ? 'danger' : type}, rgba(13, 110, 253, 0.1));
            border-left: 4px solid var(--bs-${type === 'error' ? 'danger' : type}, #0d6efd);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transform: translateX(100%);
            opacity: 0;
            transition: all 0.3s ease-in-out;
        `;
        
        // Create content
        const content = document.createElement('div');
        content.className = 'notification-content';
        content.style.cssText = 'display: flex; align-items: flex-start; justify-content: space-between;';
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'notification-message';
        messageDiv.style.cssText = 'flex: 1; margin-right: 1rem;';
        messageDiv.innerHTML = message;
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'notification-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.style.cssText = `
            background: none;
            border: none;
            font-size: 1.25rem;
            cursor: pointer;
            opacity: 0.6;
            padding: 0;
            line-height: 1;
        `;
        closeBtn.addEventListener('click', () => this.dismiss(id));
        
        content.appendChild(messageDiv);
        content.appendChild(closeBtn);
        notification.appendChild(content);
        
        // Add actions if provided
        if (actions && actions.length > 0) {
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'notification-actions';
            actionsDiv.style.cssText = 'margin-top: 0.75rem; display: flex; gap: 0.5rem;';
            
            actions.forEach(action => {
                const actionBtn = document.createElement('button');
                actionBtn.className = 'btn btn-sm btn-outline-secondary';
                actionBtn.textContent = action.text;
                actionBtn.addEventListener('click', () => {
                    action.onClick();
                    if (action.dismiss !== false) {
                        this.dismiss(id);
                    }
                });
                actionsDiv.appendChild(actionBtn);
            });
            
            notification.appendChild(actionsDiv);
        }
        
        // Add show class for animation
        notification.classList.add('notification-enter');
        
        return notification;
    }
    
    dismiss(id) {
        const notification = this.notifications.get(id);
        if (notification) {
            notification.style.transform = 'translateX(100%)';
            notification.style.opacity = '0';
            
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
                this.notifications.delete(id);
            }, 300);
        }
    }
    
    dismissAll() {
        this.notifications.forEach((_, id) => this.dismiss(id));
    }
    
    // Convenience methods
    success(message, duration = 5000, actions = []) {
        return this.show(message, 'success', duration, actions);
    }
    
    error(message, duration = 7000, actions = []) {
        return this.show(message, 'error', duration, actions);
    }
    
    warning(message, duration = 6000, actions = []) {
        return this.show(message, 'warning', duration, actions);
    }
    
    info(message, duration = 4000, actions = []) {
        return this.show(message, 'info', duration, actions);
    }
    
    progress(message, progress = 0) {
        const id = this.nextId++;
        const notification = document.createElement('div');
        notification.className = 'notification notification-progress';
        notification.style.cssText = `
            pointer-events: auto;
            margin-bottom: 0.75rem;
            padding: 1rem;
            border-radius: 0.5rem;
            background: rgba(13, 110, 253, 0.1);
            border-left: 4px solid #0d6efd;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transform: translateX(100%);
            opacity: 0;
            transition: all 0.3s ease-in-out;
        `;
        
        notification.innerHTML = `
            <div style="margin-bottom: 0.75rem; font-weight: 500;">${message}</div>
            <div class="progress" style="height: 8px; background-color: rgba(0,0,0,0.1); border-radius: 4px;">
                <div class="progress-bar" style="width: ${progress}%; background-color: #0d6efd; transition: width 0.3s ease;"></div>
            </div>
            <div class="progress-text" style="font-size: 0.875rem; margin-top: 0.5rem; color: #666;">${progress}%</div>
        `;
        
        this.container.appendChild(notification);
        this.notifications.set(id, notification);
        
        // Trigger animation
        requestAnimationFrame(() => {
            notification.style.transform = 'translateX(0)';
            notification.style.opacity = '1';
        });
        
        // Return update function
        return {
            id,
            update: (newProgress, newMessage) => {
                const progressBar = notification.querySelector('.progress-bar');
                const progressText = notification.querySelector('.progress-text');
                const messageDiv = notification.querySelector('div');
                
                if (progressBar) progressBar.style.width = `${newProgress}%`;
                if (progressText) progressText.textContent = `${newProgress}%`;
                if (newMessage && messageDiv) messageDiv.textContent = newMessage;
            },
            dismiss: () => this.dismiss(id)
        };
    }
}

// Create global instance
const notificationManager = new NotificationManager();

// Export unified interface
export const notifications = {
    show: (message, type, duration, actions) => notificationManager.show(message, type, duration, actions),
    success: (message, duration, actions) => notificationManager.success(message, duration, actions),
    error: (message, duration, actions) => notificationManager.error(message, duration, actions),
    warning: (message, duration, actions) => notificationManager.warning(message, duration, actions),
    info: (message, duration, actions) => notificationManager.info(message, duration, actions),
    progress: (message, progress) => notificationManager.progress(message, progress),
    dismiss: (id) => notificationManager.dismiss(id),
    dismissAll: () => notificationManager.dismissAll()
};

// Backward compatibility
export function showNotification(message, type = 'info', duration = 5000) {
    return notifications.show(message, type, duration);
}

// ============================================================================
// FILE UTILITIES
// ============================================================================

/**
 * Format file size for display
 */
export function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
}

/**
 * Enhanced file validation with detailed feedback
 */
export function validateFiles(files, options = {}) {
    const defaults = {
        maxSize: 16 * 1024 * 1024, // 16MB
        allowedTypes: ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf', 'text/plain'],
        maxFiles: 10
    };
    const config = { ...defaults, ...options };
    const errors = [];
    
    if (files.length > config.maxFiles) {
        errors.push(`Too many files selected. Maximum allowed: ${config.maxFiles}`);
    }
    
    Array.from(files).forEach(file => {
        if (file.size > config.maxSize) {
            errors.push(`File "${file.name}" exceeds the ${formatFileSize(config.maxSize)} size limit.`);
        }
        
        if (!config.allowedTypes.includes(file.type)) {
            const allowedExtensions = config.allowedTypes
                .map(type => type.split('/')[1].toUpperCase())
                .join(', ');
            errors.push(`File "${file.name}" is not an allowed file type. Allowed: ${allowedExtensions}`);
        }
    });
    
    if (errors.length > 0) {
        notifications.error(`File validation errors:\n\n${errors.join('\n')}`);
        return false;
    }
    
    return true;
}

// ============================================================================
// STORAGE UTILITIES
// ============================================================================

export const storage = {
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.warn('Failed to parse localStorage item:', key, error);
            return defaultValue;
        }
    },
    
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.warn('Failed to set localStorage item:', key, error);
            return false;
        }
    },
    
    remove(key) {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.warn('Failed to remove localStorage item:', key, error);
            return false;
        }
    },
    
    clear() {
        try {
            localStorage.clear();
            return true;
        } catch (error) {
            console.warn('Failed to clear localStorage:', error);
            return false;
        }
    }
};

// ============================================================================
// API UTILITIES
// ============================================================================

/**
 * Safe API request with unified error handling
 */
export async function apiRequest(url, options = {}) {
    const defaults = {
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin'
    };
    
    try {
        const response = await fetch(url, { ...defaults, ...options });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        } else {
            return await response.text();
        }
    } catch (error) {
        console.error('API request failed:', error);
        notifications.error(`Request failed: ${error.message}`);
        throw error;
    }
}

// ============================================================================
// DOM UTILITIES
// ============================================================================

/**
 * Prevent default drag behaviors
 */
export function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

/**
 * Safe element selector with error handling
 */
export function $(selector, context = document) {
    try {
        return context.querySelector(selector);
    } catch (error) {
        console.warn('Invalid selector:', selector, error);
        return null;
    }
}

export function $$(selector, context = document) {
    try {
        return context.querySelectorAll(selector);
    } catch (error) {
        console.warn('Invalid selector:', selector, error);
        return [];
    }
}

// ============================================================================
// DATE/TIME UTILITIES
// ============================================================================

/**
 * Format date for display
 */
export function formatDate(date, options = {}) {
    const defaults = {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    };
    
    try {
        const dateObj = date instanceof Date ? date : new Date(date);
        return dateObj.toLocaleDateString(undefined, { ...defaults, ...options });
    } catch (error) {
        console.warn('Invalid date:', date, error);
        return 'Invalid Date';
    }
}

/**
 * Format time for display
 */
export function formatTime(date, options = {}) {
    const defaults = {
        hour: '2-digit',
        minute: '2-digit'
    };
    
    try {
        const dateObj = date instanceof Date ? date : new Date(date);
        return dateObj.toLocaleTimeString(undefined, { ...defaults, ...options });
    } catch (error) {
        console.warn('Invalid time:', date, error);
        return 'Invalid Time';
    }
}

// ============================================================================
// SECURITY UTILITIES
// ============================================================================

/**
 * Sanitize HTML to prevent XSS
 */
export function sanitizeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

/**
 * Escape HTML entities
 */
export function escapeHTML(str) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    };
    return str.replace(/[&<>"']/g, m => map[m]);
}

// ============================================================================
// PERFORMANCE MONITORING
// ============================================================================

/**
 * Simple performance timer
 */
export function timer(name) {
    const start = performance.now();
    return {
        end: () => {
            const duration = performance.now() - start;
            console.log(`⏱️ ${name}: ${duration.toFixed(2)}ms`);
            return duration;
        }
    };
}

// ============================================================================
// EXPORTS
// ============================================================================

// Export default object for backward compatibility
export default {
    // Performance
    debounce,
    throttle,
    timer,
    
    // Notifications
    notifications,
    showNotification,
    
    // Files
    formatFileSize,
    validateFiles,
    preventDefaults,
    
    // Storage
    storage,
    
    // API
    apiRequest,
    
    // DOM
    $,
    $$,
    
    // Date/Time
    formatDate,
    formatTime,
    
    // Security
    sanitizeHTML,
    escapeHTML
};
