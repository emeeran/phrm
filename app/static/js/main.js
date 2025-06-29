/**
 * PHRM - Final Optimized JavaScript Entry Point
 * Consolidated, modular, and performance-optimized
 */

// Import optimized core modules
import { notifications, debounce, throttle, apiRequest, storage } from './core-utils.js';
import UIManager from './ui-manager.js';

class PHRMOptimized {
    constructor() {
        this.uiManager = UIManager;
        this.notifications = notifications;
        this.storage = storage;
        this.init();
    }

    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        // Initialize core systems
        this.initializeBootstrap();
        this.setupGlobalUtilities();
        this.loadConditionalModules();
        
        console.log('✅ PHRM Optimized - All systems initialized');
    }

    initializeBootstrap() {
        // Bootstrap tooltips
        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
            new bootstrap.Tooltip(el);
        });

        // Bootstrap popovers
        document.querySelectorAll('[data-bs-toggle="popover"]').forEach(el => {
            new bootstrap.Popover(el);
        });
    }

    setupGlobalUtilities() {
        // Global API utility
        window.apiCall = apiRequest;
        
        // Global notification system
        window.showNotification = notifications.show;
        
        // Global storage utility
        window.storage = storage;
        
        // Performance-optimized resize handler
        window.addEventListener('resize', throttle(() => {
            this.handleResize();
        }, 250));
    }

    loadConditionalModules() {
        // Chat functionality
        if (document.getElementById('chat-form')) {
            this.loadChatManager();
        }
        
        // Document processing
        if (document.querySelector('[data-document-processing]')) {
            this.loadDocumentProcessor();
        }
        
        // File management
        if (document.querySelector('input[type="file"]')) {
            this.loadFileManager();
        }
        
        // Dashboard charts
        if (document.querySelector('.dashboard-chart')) {
            this.loadDashboardCharts();
        }
    }

    async loadChatManager() {
        try {
            const { ChatManager } = await import('./chat-manager-optimized.js');
            new ChatManager();
        } catch (error) {
            console.warn('Chat manager not available:', error);
        }
    }

    async loadDocumentProcessor() {
        try {
            const { DocumentProcessingManager } = await import('./document-processing.js');
            new DocumentProcessingManager();
        } catch (error) {
            console.warn('Document processor not available:', error);
        }
    }

    async loadFileManager() {
        try {
            const { FileUploadManager } = await import('./file-manager.js');
            document.querySelectorAll('input[type="file"]').forEach(input => {
                if (input.id) {
                    new FileUploadManager(input.id);
                }
            });
        } catch (error) {
            console.warn('File manager not available:', error);
        }
    }

    async loadDashboardCharts() {
        try {
            const module = await import('./dashboard-charts.js');
            if (module.initializeCharts) {
                module.initializeCharts();
            }
        } catch (error) {
            console.warn('Dashboard charts not available:', error);
        }
    }

    handleResize() {
        // Handle responsive changes
        const isMobile = window.innerWidth < 768;
        document.body.classList.toggle('mobile', isMobile);
        
        // Notify UI manager of resize
        if (this.uiManager && this.uiManager.handleResize) {
            this.uiManager.handleResize();
        }
    }
}

// Initialize the optimized application
const phrm = new PHRMOptimized();

// Export for debugging and advanced usage
window.PHRM = phrm;
window.PHRMOptimized = PHRMOptimized;

export default PHRMOptimized;
