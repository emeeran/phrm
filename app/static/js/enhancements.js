/**
 * Theme Management and Dark Mode Toggle
 */

class ThemeManager {
    constructor() {
        this.currentTheme = this.getStoredTheme() || this.getPreferredTheme();
        this.init();
    }

    init() {
        this.setTheme(this.currentTheme);
        this.createToggleButton();
        this.bindEvents();
    }

    getStoredTheme() {
        return localStorage.getItem('theme');
    }

    getPreferredTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    setTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        this.currentTheme = theme;
        this.updateToggleButton();
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.setTheme(newTheme);

        // Add transition effect
        document.body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);

        // Analytics tracking (if available)
        if (typeof gtag !== 'undefined') {
            gtag('event', 'theme_toggle', {
                'theme': newTheme
            });
        }
    }

    createToggleButton() {
        if (document.querySelector('.theme-toggle')) {
            return; // Button already exists
        }

        const button = document.createElement('button');
        button.className = 'theme-toggle';
        button.setAttribute('aria-label', 'Toggle dark mode');
        button.setAttribute('title', 'Toggle dark mode');
        button.innerHTML = this.getButtonIcon();

        document.body.appendChild(button);
    }

    updateToggleButton() {
        const button = document.querySelector('.theme-toggle');
        if (button) {
            button.innerHTML = this.getButtonIcon();
            button.setAttribute('title', `Switch to ${this.currentTheme === 'light' ? 'dark' : 'light'} mode`);
        }
    }

    getButtonIcon() {
        if (this.currentTheme === 'light') {
            return '<i class="fas fa-moon"></i>'; // Moon icon for dark mode
        } else {
            return '<i class="fas fa-sun"></i>'; // Sun icon for light mode
        }
    }

    bindEvents() {
        // Toggle button click
        document.addEventListener('click', (e) => {
            if (e.target.closest('.theme-toggle')) {
                this.toggleTheme();
            }
        });

        // Keyboard shortcut (Ctrl/Cmd + Shift + D)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
                e.preventDefault();
                this.toggleTheme();
            }
        });

        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!this.getStoredTheme()) {
                    this.setTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }

    // Public method to get current theme
    getCurrentTheme() {
        return this.currentTheme;
    }

    // Public method to set theme programmatically
    setThemeMode(theme) {
        if (['light', 'dark'].includes(theme)) {
            this.setTheme(theme);
        }
    }
}

/**
 * Notification System Frontend
 */
class NotificationUI {
    constructor() {
        this.notifications = [];
        this.container = null;
        this.init();
    }

    init() {
        this.createContainer();
        this.bindEvents();
        this.loadNotifications();
    }

    createContainer() {
        // Create notification container if it doesn't exist
        if (!document.querySelector('.notification-container')) {
            const container = document.createElement('div');
            container.className = 'notification-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1050;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        this.container = document.querySelector('.notification-container');
    }

    showNotification(notification) {
        const notificationEl = document.createElement('div');
        notificationEl.className = `alert alert-dismissible fade show notification-${notification.priority}`;
        notificationEl.innerHTML = `
            <div class="d-flex">
                <div class="flex-grow-1">
                    <strong>${notification.title}</strong>
                    <div class="mt-1">${notification.message}</div>
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;

        // Add priority styling
        switch (notification.priority) {
            case 'urgent':
                notificationEl.classList.add('alert-danger');
                break;
            case 'high':
                notificationEl.classList.add('alert-warning');
                break;
            case 'medium':
                notificationEl.classList.add('alert-info');
                break;
            case 'low':
                notificationEl.classList.add('alert-success');
                break;
        }

        this.container.appendChild(notificationEl);

        // Auto-remove after delay (except urgent notifications)
        if (notification.priority !== 'urgent') {
            setTimeout(() => {
                if (notificationEl.parentNode) {
                    notificationEl.remove();
                }
            }, 5000);
        }
    }

    loadNotifications() {
        // This would typically fetch from the server
        // For now, we'll simulate with some sample notifications
        const sampleNotifications = [
            {
                title: 'Medication Reminder',
                message: 'Time to take your morning medication',
                priority: 'high'
            },
            {
                title: 'Health Check Due',
                message: 'Your annual checkup is due soon',
                priority: 'medium'
            }
        ];

        // Show sample notifications after a delay
        setTimeout(() => {
            sampleNotifications.forEach((notification, index) => {
                setTimeout(() => {
                    this.showNotification(notification);
                }, index * 1000);
            });
        }, 2000);
    }

    bindEvents() {
        // Listen for custom notification events
        document.addEventListener('show-notification', (e) => {
            this.showNotification(e.detail);
        });
    }
}

/**
 * Enhanced Search Functionality
 */
class SearchEnhancer {
    constructor() {
        this.searchForm = document.querySelector('#health-records-search');
        this.init();
    }

    init() {
        if (!this.searchForm) return;

        this.enhanceSearchForm();
        this.addSearchSuggestions();
        this.bindEvents();
    }

    enhanceSearchForm() {
        // Add advanced search toggle
        const advancedToggle = document.createElement('button');
        advancedToggle.type = 'button';
        advancedToggle.className = 'btn btn-outline-secondary btn-sm';
        advancedToggle.innerHTML = '<i class="fas fa-sliders-h"></i> Advanced';
        advancedToggle.onclick = () => this.toggleAdvancedSearch();

        this.searchForm.appendChild(advancedToggle);

        // Create advanced search panel
        this.createAdvancedSearchPanel();
    }

    createAdvancedSearchPanel() {
        const panel = document.createElement('div');
        panel.className = 'advanced-search-panel mt-3';
        panel.style.display = 'none';
        panel.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <label class="form-label">Record Type</label>
                            <select class="form-select" name="record_type">
                                <option value="">All Types</option>
                                <option value="Physical Exam">Physical Exam</option>
                                <option value="Lab Results">Lab Results</option>
                                <option value="Imaging">Imaging</option>
                                <option value="Prescription">Prescription</option>
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Provider</label>
                            <input type="text" class="form-control" name="provider" placeholder="Doctor or facility name">
                        </div>
                    </div>
                    <div class="row mt-3">
                        <div class="col-md-6">
                            <label class="form-label">Date From</label>
                            <input type="date" class="form-control" name="date_from">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Date To</label>
                            <input type="date" class="form-control" name="date_to">
                        </div>
                    </div>
                    <div class="mt-3">
                        <div class="form-check">
                            <input class="form-check-input" type="checkbox" name="include_family" id="include_family">
                            <label class="form-check-label" for="include_family">
                                Include family member records
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.searchForm.appendChild(panel);
        this.advancedPanel = panel;
    }

    toggleAdvancedSearch() {
        if (this.advancedPanel.style.display === 'none') {
            this.advancedPanel.style.display = 'block';
        } else {
            this.advancedPanel.style.display = 'none';
        }
    }

    addSearchSuggestions() {
        const searchInput = this.searchForm.querySelector('input[type="search"]');
        if (!searchInput) return;

        // Create suggestions dropdown
        const suggestionsContainer = document.createElement('div');
        suggestionsContainer.className = 'search-suggestions';
        suggestionsContainer.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-top: none;
            border-radius: 0 0 0.375rem 0.375rem;
            box-shadow: 0 0.125rem 0.25rem var(--shadow);
            z-index: 1000;
            display: none;
        `;

        searchInput.parentNode.style.position = 'relative';
        searchInput.parentNode.appendChild(suggestionsContainer);

        // Add search suggestions logic
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.fetchSuggestions(e.target.value, suggestionsContainer);
            }, 300);
        });

        // Hide suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !suggestionsContainer.contains(e.target)) {
                suggestionsContainer.style.display = 'none';
            }
        });
    }

    fetchSuggestions(query, container) {
        if (query.length < 2) {
            container.style.display = 'none';
            return;
        }

        // Sample suggestions - in a real app, this would be an API call
        const suggestions = [
            'blood pressure',
            'diabetes',
            'medication',
            'annual checkup',
            'chest x-ray',
            'lab results'
        ].filter(s => s.toLowerCase().includes(query.toLowerCase()));

        if (suggestions.length > 0) {
            container.innerHTML = suggestions.map(suggestion =>
                `<div class="suggestion-item p-2" style="cursor: pointer;">${suggestion}</div>`
            ).join('');
            container.style.display = 'block';

            // Add click handlers for suggestions
            container.querySelectorAll('.suggestion-item').forEach(item => {
                item.addEventListener('click', () => {
                    document.querySelector('input[type="search"]').value = item.textContent;
                    container.style.display = 'none';
                });
            });
        } else {
            container.style.display = 'none';
        }
    }

    bindEvents() {
        // Add keyboard shortcuts for search
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K to focus search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                const searchInput = document.querySelector('input[type="search"]');
                if (searchInput) {
                    searchInput.focus();
                }
            }
        });
    }
}

/**
 * Performance Monitor
 */
class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.init();
    }

    init() {
        this.trackPageLoad();
        this.trackUserInteractions();
    }

    trackPageLoad() {
        window.addEventListener('load', () => {
            const navigation = performance.getEntriesByType('navigation')[0];
            this.metrics.pageLoad = {
                loadTime: navigation.loadEventEnd - navigation.loadEventStart,
                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                totalTime: navigation.loadEventEnd - navigation.fetchStart
            };
        });
    }

    trackUserInteractions() {
        let interactionCount = 0;
        ['click', 'scroll', 'keydown'].forEach(eventType => {
            document.addEventListener(eventType, () => {
                interactionCount++;
            }, { passive: true });
        });

        // Track interactions every minute
        setInterval(() => {
            this.metrics.interactions = interactionCount;
            interactionCount = 0;
        }, 60000);
    }

    getMetrics() {
        return this.metrics;
    }
}

// Initialize everything when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme management
    window.themeManager = new ThemeManager();

    // Initialize notification system
    window.notificationUI = new NotificationUI();

    // Initialize search enhancements
    window.searchEnhancer = new SearchEnhancer();

    // Initialize performance monitoring
    window.performanceMonitor = new PerformanceMonitor();

    console.log('PHRM enhancements loaded successfully');
});

// Utility functions for external use
window.PHRM = {
    showNotification: (notification) => {
        if (window.notificationUI) {
            window.notificationUI.showNotification(notification);
        }
    },

    setTheme: (theme) => {
        if (window.themeManager) {
            window.themeManager.setThemeMode(theme);
        }
    },

    getPerformanceMetrics: () => {
        if (window.performanceMonitor) {
            return window.performanceMonitor.getMetrics();
        }
        return {};
    }
};
