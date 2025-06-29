/**
 * PHRM Optimized JavaScript Entry Point
 * Loads all optimized modules and initializes the application
 */

// Import core utilities and managers
import './core-utils.js';
import './ui-manager.js';
import './app-optimized.js';

// Conditionally load page-specific modules
document.addEventListener('DOMContentLoaded', () => {
    // Chat functionality
    if (document.getElementById('chat-form')) {
        import('./chat-manager-optimized.js').then(({ ChatManager }) => {
            new ChatManager();
        });
    }
    
    // Document processing
    if (document.querySelector('[data-document-processing]')) {
        import('./document-processing.js').then(({ DocumentProcessingManager }) => {
            new DocumentProcessingManager();
        });
    }
    
    // File management
    if (document.querySelector('input[type="file"]')) {
        import('./file-manager.js').then(({ FileUploadManager }) => {
            document.querySelectorAll('input[type="file"]').forEach(input => {
                new FileUploadManager(input.id);
            });
        });
    }
    
    console.log('✅ PHRM Optimized JavaScript loaded successfully');
});
