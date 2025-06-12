// PHRM - Optimized Modern JavaScript

class PHRMApp {
    constructor() {
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        this.initBootstrap();
        this.initAlerts();
        this.initForms();
        this.initTooltips();
        this.initAnimations();
        this.initPerformanceOptimizations();
    }

    // Bootstrap component initialization
    initBootstrap() {
        // Initialize tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

        // Initialize popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
    }

    // Auto-dismiss alerts
    initAlerts() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            // Auto-dismiss success alerts after 3 seconds
            if (alert.classList.contains('alert-success')) {
                setTimeout(() => {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }, 3000);
            }
        });
    }

    // Form enhancements
    initForms() {
        // Add loading states to forms
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.classList.add('loading');
                    submitBtn.disabled = true;
                }
            });
        });

        // Auto-focus first input
        const firstInput = document.querySelector('.form-control:not([readonly]):not([disabled])');
        if (firstInput) {
            firstInput.focus();
        }

        // Real-time validation
        const inputs = document.querySelectorAll('.form-control');
        inputs.forEach(input => {
            input.addEventListener('blur', () => this.validateField(input));
        });
    }

    // Tooltip initialization
    initTooltips() {
        // Add tooltips to truncated text
        const truncatedElements = document.querySelectorAll('[title]');
        truncatedElements.forEach(el => {
            if (el.scrollWidth > el.clientWidth) {
                el.setAttribute('data-bs-toggle', 'tooltip');
                el.setAttribute('data-bs-placement', 'top');
                new bootstrap.Tooltip(el);
            }
        });
    }

    // Smooth animations
    initAnimations() {
        // Intersection Observer for fade-in animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        // Observe cards for animation
        const cards = document.querySelectorAll('.card-modern');
        cards.forEach(card => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            observer.observe(card);
        });
    }

    // Performance optimizations
    initPerformanceOptimizations() {
        // Lazy load images
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));

        // Debounced resize handler
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 250);
        });
    }

    // Field validation
    validateField(field) {
        const value = field.value.trim();
        
        if (field.type === 'email' && value && !this.isValidEmail(value)) {
            this.showFieldError(field, 'Please enter a valid email address');
            return false;
        }

        this.clearFieldError(field);
        return true;
    }

    showFieldError(field, message) {
        field.classList.add('is-invalid');
        
        let feedback = field.parentNode.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentNode.appendChild(feedback);
        }
        feedback.textContent = message;
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    handleResize() {
        // Handle responsive changes
        const isMobile = window.innerWidth < 768;
        document.body.classList.toggle('mobile', isMobile);
    }

    // Utility methods
    showNotification(message, type = 'info') {
        const alertContainer = document.querySelector('.alert-container') || 
                             this.createAlertContainer();
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.appendChild(alert);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    }

    createAlertContainer() {
        const container = document.createElement('div');
        container.className = 'alert-container';
        document.body.appendChild(container);
        return container;
    }

    // API utility
    async apiCall(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            this.showNotification('An error occurred. Please try again.', 'danger');
            throw error;
        }
    }
}

// Dashboard specific functionality
class Dashboard {
    constructor() {
        if (document.body.classList.contains('dashboard-page')) {
            this.init();
        }
    }

    init() {
        this.initQuickActions();
        this.initStatsRefresh();
    }

    initQuickActions() {
        const quickActions = document.querySelectorAll('.btn-quick');
        quickActions.forEach(btn => {
            btn.addEventListener('click', (e) => {
                btn.classList.add('loading');
            });
        });
    }

    initStatsRefresh() {
        // Auto-refresh stats every 5 minutes
        setInterval(() => {
            this.refreshStats();
        }, 300000);
    }

    async refreshStats() {
        try {
            const stats = await app.apiCall('/api/dashboard/stats');
            this.updateStatsDisplay(stats);
        } catch (error) {
            console.error('Failed to refresh stats:', error);
        }
    }

    updateStatsDisplay(stats) {
        Object.keys(stats).forEach(key => {
            const element = document.querySelector(`[data-stat="${key}"]`);
            if (element) {
                element.textContent = stats[key];
            }
        });
    }
}

// File upload enhancement
class FileUploadEnhancer {
    constructor() {
        this.initFileInputs();
    }

    initFileInputs() {
        const fileInputs = document.querySelectorAll('input[type="file"]');
        fileInputs.forEach(input => {
            this.enhanceFileInput(input);
        });
    }

    enhanceFileInput(input) {
        const wrapper = document.createElement('div');
        wrapper.className = 'file-upload-wrapper';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);

        // Add drag and drop
        wrapper.addEventListener('dragover', (e) => {
            e.preventDefault();
            wrapper.classList.add('dragover');
        });

        wrapper.addEventListener('dragleave', () => {
            wrapper.classList.remove('dragover');
        });

        wrapper.addEventListener('drop', (e) => {
            e.preventDefault();
            wrapper.classList.remove('dragover');
            const files = e.dataTransfer.files;
            input.files = files;
            this.handleFileSelection(input, files);
        });

        input.addEventListener('change', (e) => {
            this.handleFileSelection(input, e.target.files);
        });
    }

    handleFileSelection(input, files) {
        if (files.length > 0) {
            const file = files[0];
            const maxSize = 10 * 1024 * 1024; // 10MB
            
            if (file.size > maxSize) {
                app.showNotification('File size must be less than 10MB', 'warning');
                input.value = '';
                return;
            }

            this.showFilePreview(input, file);
        }
    }

    showFilePreview(input, file) {
        const wrapper = input.closest('.file-upload-wrapper');
        let preview = wrapper.querySelector('.file-preview');
        
        if (!preview) {
            preview = document.createElement('div');
            preview.className = 'file-preview';
            wrapper.appendChild(preview);
        }

        preview.innerHTML = `
            <div class="file-info">
                <i class="fas fa-file me-2"></i>
                <span>${file.name}</span>
                <small class="text-muted ms-2">(${this.formatFileSize(file.size)})</small>
            </div>
        `;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Initialize the application
const app = new PHRMApp();
const dashboard = new Dashboard();
const fileUploader = new FileUploadEnhancer();

// Export for global access
window.PHRMApp = PHRMApp;
window.app = app;
