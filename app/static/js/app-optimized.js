// PHRM - Optimized Modern JavaScript
import { notifications, debounce, throttle, apiRequest, storage } from './core-utils.js';
import UIManager from './ui-manager.js';

class PHRMApp {
    constructor() {
        this.uiManager = UIManager;
        this.notifications = notifications;
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
        // UI Manager handles most initialization now
        this.setupAppSpecificFeatures();
        this.setupMenuListeners(); // Ensure menu listeners are always attached
        this.setupDropdownListeners(); // Ensure dropdowns work
    }

    setupMenuListeners() {
        // Example: Attach click handlers to all menu items
        const menuItems = document.querySelectorAll('.menu-item');
        menuItems.forEach(item => {
            item.removeEventListener('click', this.handleMenuClick); // Remove previous to avoid duplicates
            item.addEventListener('click', this.handleMenuClick);
        });
    }

    handleMenuClick(e) {
        // Example: Toggle active class or open submenu
        const item = e.currentTarget;
        document.querySelectorAll('.menu-item.active').forEach(el => el.classList.remove('active'));
        item.classList.add('active');
        // Add more logic as needed for your menu system
    }

    setupDropdownListeners() {
        // Close all dropdowns
        const closeAllDropdowns = () => {
            document.querySelectorAll('.dropdown-menu.show').forEach(menu => menu.classList.remove('show'));
            document.querySelectorAll('.dropdown-toggle.active').forEach(toggle => toggle.classList.remove('active'));
        };

        // Attach click handler to all dropdown toggles
        const toggles = document.querySelectorAll('.dropdown-toggle');
        toggles.forEach(toggle => {
            toggle.removeEventListener('click', toggle._dropdownHandler);
            toggle._dropdownHandler = (e) => {
                e.preventDefault();
                e.stopPropagation();
                const menu = toggle.nextElementSibling;
                if (!menu || !menu.classList.contains('dropdown-menu')) return;
                const isOpen = menu.classList.contains('show');
                closeAllDropdowns();
                if (!isOpen) {
                    menu.classList.add('show');
                    toggle.classList.add('active');
                }
            };
            toggle.addEventListener('click', toggle._dropdownHandler);
        });

        // Close dropdowns when clicking outside
        document.removeEventListener('click', document._dropdownCloseHandler);
        document._dropdownCloseHandler = (e) => {
            if (!e.target.closest('.dropdown')) closeAllDropdowns();
        };
        document.addEventListener('click', document._dropdownCloseHandler);

        // Keyboard accessibility: close on Escape
        document.removeEventListener('keydown', document._dropdownKeyHandler);
        document._dropdownKeyHandler = (e) => {
            if (e.key === 'Escape') closeAllDropdowns();
        };
        document.addEventListener('keydown', document._dropdownKeyHandler);
    }

    setupAppSpecificFeatures() {
        this.initAPIHelpers();
        this.initErrorHandling();
        this.setupGlobalEventListeners();
        // If your UI updates menus dynamically, re-attach listeners:
        const observer = new MutationObserver(() => {
            this.setupMenuListeners();
            this.setupDropdownListeners(); // Re-attach dropdown listeners on DOM change
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    initAPIHelpers() {
        // Add global API helper
        window.apiCall = apiRequest;
        
        // Add error handling for fetch requests
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            notifications.error('An unexpected error occurred. Please try again.');
        });
    }

    initErrorHandling() {
        // Global error handler
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
            notifications.error('An error occurred. Please refresh the page if problems persist.');
        });
    }

    setupGlobalEventListeners() {
        // Enhanced form submission handling
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.tagName === 'FORM') {
                const submitBtn = form.querySelector('input[type="submit"], button[type="submit"]');
                if (submitBtn && !submitBtn.disabled) {
                    // Show loading state (handled by UI Manager)
                    setTimeout(() => {
                        if (submitBtn.disabled) {
                            this.uiManager.hideLoadingState(submitBtn);
                        }
                    }, 30000); // Safety timeout
                }
            }
        });

        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K for search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('input[type="search"], #search-input');
                if (searchInput) {
                    searchInput.focus();
                }
            }
        });
    }

    // Public API for backward compatibility
    showNotification(message, type = 'info') {
        return notifications.show(message, type);
    }

    async apiCall(url, options = {}) {
        return apiRequest(url, options);
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
                UIManager.showLoadingState(btn);
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
            const stats = await apiRequest('/api/dashboard/stats');
            this.updateStatsDisplay(stats);
        } catch (error) {
            console.error('Failed to refresh stats:', error);
        }
    }

    updateStatsDisplay(stats) {
        // Update stat cards
        Object.keys(stats).forEach(key => {
            const element = document.getElementById(`stat-${key}`);
            if (element) {
                element.textContent = stats[key];
                UIManager.highlight(element, 1000);
            }
        });
    }
}

// File upload enhancement
class FileUploadEnhancer {
    constructor() {
        this.init();
    }

    init() {
        const fileInputs = document.querySelectorAll('input[type="file"]');
        fileInputs.forEach(input => this.enhanceFileInput(input));
    }

    enhanceFileInput(input) {
        input.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            
            if (files.length === 0) return;
            
            // Validate files using our utility
            const { validateFiles } = window.PHRM || {};
            if (validateFiles && !validateFiles(files)) {
                input.value = ''; // Clear invalid files
                return;
            }
            
            this.updateFileDisplay(input, files);
        });
    }

    updateFileDisplay(input, files) {
        const display = input.nextElementSibling;
        if (display && display.classList.contains('file-display')) {
            const fileNames = files.map(f => f.name).join(', ');
            display.textContent = fileNames;
        }
    }
}

// Initialize the application
const app = new PHRMApp();
const dashboard = new Dashboard();
const fileUploader = new FileUploadEnhancer();

// Export for global access
window.PHRMApp = PHRMApp;
window.app = app;

// Backward compatibility - expose utilities globally
window.PHRM = {
    notifications,
    apiRequest,
    storage,
    debounce,
    throttle,
    UIManager
};
