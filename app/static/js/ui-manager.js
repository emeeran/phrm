/**
 * PHRM Unified UI Manager
 * Consolidated UI enhancement and interaction management
 */

import { notifications, debounce, throttle, $, $$, timer } from './core-utils.js';

class UIManager {
    constructor() {
        this.intersectionObserver = null;
        this.initialized = false;
        this.components = new Map();
        
        // Bind methods
        this.init = this.init.bind(this);
        this.handleResize = this.handleResize.bind(this);
        
        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', this.init);
        } else {
            this.init();
        }
    }
    
    init() {
        if (this.initialized) return;
        
        const initTimer = timer('UI Manager Initialization');
        
        // Core UI enhancements
        this.setupIntersectionObserver();
        this.enhanceCards();
        this.enhanceButtons();
        this.setupRippleEffects();
        this.initTooltips();
        this.setupLoadingStates();
        this.initAccessibility();
        this.setupResponsive();
        this.initAnimations();
        
        // Component-specific initialization
        this.initForms();
        this.initModals();
        this.initTabs();
        this.initDropdowns();
        
        this.initialized = true;
        initTimer.end();
        
        console.log('✅ UI Manager initialized successfully');
    }
    
    // ========================================================================
    // CORE UI ENHANCEMENTS
    // ========================================================================
    
    setupIntersectionObserver() {
        if (!window.IntersectionObserver) return;
        
        this.intersectionObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    if (entry.target.dataset.animationDelay) {
                        entry.target.style.animationDelay = entry.target.dataset.animationDelay;
                    }
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });
        
        // Observe elements for animation
        $$('.card-modern, .action-card-modern, .stat-card-modern, [data-animate]').forEach(card => {
            card.classList.add('animate-ready');
            this.intersectionObserver.observe(card);
        });
    }
    
    enhanceCards() {
        $$('.card-modern, .stat-card-modern').forEach(card => {
            // Add hover effects
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-2px) scale(1.02)';
                card.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.15)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = '';
                card.style.boxShadow = '';
            });
            
            // Add click ripple effect
            card.addEventListener('click', (e) => {
                if (!card.querySelector('.ripple')) {
                    this.createRipple(e, card);
                }
            });
        });
    }
    
    enhanceButtons() {
        $$('.btn-modern-primary, .btn-modern-outline, .btn').forEach(button => {
            // Enhanced button interactions
            button.addEventListener('mousedown', () => {
                button.style.transform = 'scale(0.95)';
            });
            
            button.addEventListener('mouseup', () => {
                button.style.transform = '';
            });
            
            button.addEventListener('mouseleave', () => {
                button.style.transform = '';
            });
            
            // Add ripple effect to buttons
            button.addEventListener('click', (e) => {
                this.createRipple(e, button);
            });
        });
    }
    
    setupRippleEffects() {
        $$('[data-ripple], .btn, .card-clickable').forEach(element => {
            element.addEventListener('click', (e) => {
                this.createRipple(e, element);
            });
        });
    }
    
    createRipple(event, element) {
        // Don't create ripple if element is disabled
        if (element.disabled || element.classList.contains('disabled')) return;
        
        const ripple = document.createElement('span');
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.className = 'ripple-effect';
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 600ms ease-out;
            pointer-events: none;
            z-index: 1000;
        `;
        
        // Ensure element can contain the ripple
        const position = getComputedStyle(element).position;
        if (position === 'static') {
            element.style.position = 'relative';
        }
        element.style.overflow = 'hidden';
        
        element.appendChild(ripple);
        
        // Remove ripple after animation
        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 600);
    }
    
    initTooltips() {
        // Initialize Bootstrap tooltips if available
        if (window.bootstrap && bootstrap.Tooltip) {
            $$('[data-bs-toggle="tooltip"]').forEach(element => {
                new bootstrap.Tooltip(element);
            });
        }
        
        // Custom tooltip implementation for better control
        $$('[data-tooltip]').forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target, e.target.dataset.tooltip);
            });
            
            element.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
    }
    
    showTooltip(element, text) {
        this.hideTooltip(); // Remove any existing tooltip
        
        const tooltip = document.createElement('div');
        tooltip.className = 'custom-tooltip';
        tooltip.textContent = text;
        tooltip.style.cssText = `
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.875rem;
            z-index: 10000;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s ease;
        `;
        
        document.body.appendChild(tooltip);
        
        // Position tooltip
        const rect = element.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        tooltip.style.left = `${rect.left + rect.width / 2 - tooltipRect.width / 2}px`;
        tooltip.style.top = `${rect.top - tooltipRect.height - 5}px`;
        
        // Show with animation
        requestAnimationFrame(() => {
            tooltip.style.opacity = '1';
        });
        
        this.activeTooltip = tooltip;
    }
    
    hideTooltip() {
        if (this.activeTooltip) {
            this.activeTooltip.style.opacity = '0';
            setTimeout(() => {
                if (this.activeTooltip && this.activeTooltip.parentNode) {
                    this.activeTooltip.parentNode.removeChild(this.activeTooltip);
                }
                this.activeTooltip = null;
            }, 200);
        }
    }
    
    setupLoadingStates() {
        // Auto-loading states for forms
        $$('form').forEach(form => {
            form.addEventListener('submit', () => {
                const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                if (submitBtn && !submitBtn.disabled) {
                    this.showLoadingState(submitBtn);
                }
            });
        });
        
        // Loading states for buttons with data-loading attribute
        $$('[data-loading]').forEach(button => {
            button.addEventListener('click', () => {
                if (!button.disabled) {
                    this.showLoadingState(button);
                }
            });
        });
    }
    
    showLoadingState(element) {
        if (element.dataset.originalText) return; // Already in loading state
        
        element.dataset.originalText = element.textContent || element.value;
        element.disabled = true;
        
        const loadingText = element.dataset.loading || 'Loading...';
        const spinner = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>';
        
        if (element.tagName === 'INPUT') {
            element.value = loadingText;
        } else {
            element.innerHTML = spinner + loadingText;
        }
        
        element.classList.add('loading');
    }
    
    hideLoadingState(element) {
        if (!element.dataset.originalText) return; // Not in loading state
        
        element.disabled = false;
        
        if (element.tagName === 'INPUT') {
            element.value = element.dataset.originalText;
        } else {
            element.textContent = element.dataset.originalText;
        }
        
        delete element.dataset.originalText;
        element.classList.remove('loading');
    }
    
    // ========================================================================
    // ACCESSIBILITY ENHANCEMENTS
    // ========================================================================
    
    initAccessibility() {
        // Skip to main content link
        this.addSkipLink();
        
        // Enhanced focus management
        this.setupFocusManagement();
        
        // ARIA enhancements
        this.enhanceARIA();
        
        // Keyboard navigation
        this.setupKeyboardNavigation();
    }
    
    addSkipLink() {
        if ($('.skip-to-main')) return; // Already exists
        
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.className = 'skip-to-main';
        skipLink.textContent = 'Skip to main content';
        skipLink.style.cssText = `
            position: absolute;
            top: -40px;
            left: 6px;
            background: var(--bs-primary, #0d6efd);
            color: white;
            padding: 8px;
            text-decoration: none;
            border-radius: 4px;
            z-index: 10000;
            transition: top 0.3s;
        `;
        
        skipLink.addEventListener('focus', () => {
            skipLink.style.top = '6px';
        });
        
        skipLink.addEventListener('blur', () => {
            skipLink.style.top = '-40px';
        });
        
        document.body.insertBefore(skipLink, document.body.firstChild);
    }
    
    setupFocusManagement() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });
        
        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });
    }
    
    enhanceARIA() {
        // Add ARIA labels to buttons without accessible text
        $$('button, [role="button"]').forEach(button => {
            if (!button.textContent.trim() && !button.getAttribute('aria-label')) {
                console.warn('Button without accessible label detected:', button);
            }
        });
        
        // Enhance form labels
        $$('input, select, textarea').forEach(input => {
            if (!input.getAttribute('aria-label') && !$(`label[for="${input.id}"]`) && !input.closest('label')) {
                const placeholder = input.placeholder;
                if (placeholder) {
                    input.setAttribute('aria-label', placeholder);
                }
            }
        });
    }
    
    setupKeyboardNavigation() {
        // Escape key handling for modals and dropdowns
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                // Close modals
                const openModal = $('.modal.show');
                if (openModal && window.bootstrap) {
                    bootstrap.Modal.getInstance(openModal)?.hide();
                }
                
                // Close dropdowns
                const openDropdown = $('.dropdown-menu.show');
                if (openDropdown) {
                    openDropdown.classList.remove('show');
                }
                
                // Hide tooltips
                this.hideTooltip();
            }
        });
    }
    
    // ========================================================================
    // RESPONSIVE DESIGN
    // ========================================================================
    
    setupResponsive() {
        // Debounced resize handler
        const debouncedResize = debounce(this.handleResize, 250);
        window.addEventListener('resize', debouncedResize);
        
        // Initial responsive setup
        this.handleResize();
    }
    
    handleResize() {
        const isMobile = window.innerWidth < 768;
        const isTablet = window.innerWidth >= 768 && window.innerWidth < 1024;
        const isDesktop = window.innerWidth >= 1024;
        
        // Update body classes
        document.body.classList.toggle('mobile', isMobile);
        document.body.classList.toggle('tablet', isTablet);
        document.body.classList.toggle('desktop', isDesktop);
        
        // Responsive navigation
        const navbar = $('.navbar-collapse');
        if (navbar && isMobile) {
            navbar.classList.remove('show');
        }
        
        // Emit resize event for other components
        document.dispatchEvent(new CustomEvent('phrm:resize', {
            detail: { isMobile, isTablet, isDesktop }
        }));
    }
    
    // ========================================================================
    // ANIMATIONS
    // ========================================================================
    
    initAnimations() {
        // Add CSS animation classes
        const style = document.createElement('style');
        style.textContent = `
            .animate-ready {
                opacity: 0;
                transform: translateY(20px);
                transition: opacity 0.6s ease, transform 0.6s ease;
            }
            
            .animate-in {
                opacity: 1 !important;
                transform: translateY(0) !important;
            }
            
            .ripple-effect {
                animation: ripple 600ms ease-out;
            }
            
            @keyframes ripple {
                to {
                    transform: scale(4);
                    opacity: 0;
                }
            }
            
            .loading {
                opacity: 0.7;
                cursor: not-allowed;
            }
            
            .keyboard-navigation *:focus {
                outline: 2px solid var(--bs-primary, #0d6efd) !important;
                outline-offset: 2px !important;
            }
        `;
        
        if (!$('#ui-manager-styles')) {
            style.id = 'ui-manager-styles';
            document.head.appendChild(style);
        }
    }
    
    // ========================================================================
    // COMPONENT INITIALIZATION
    // ========================================================================
    
    initForms() {
        // Enhanced form validation
        $$('form[novalidate]').forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.showFormErrors(form);
                }
                form.classList.add('was-validated');
            });
        });
        
        // Real-time validation
        $$('input, select, textarea').forEach(input => {
            input.addEventListener('blur', () => {
                if (input.checkValidity()) {
                    input.classList.remove('is-invalid');
                    input.classList.add('is-valid');
                } else {
                    input.classList.remove('is-valid');
                    input.classList.add('is-invalid');
                }
            });
        });
    }
    
    showFormErrors(form) {
        const firstInvalidInput = form.querySelector(':invalid');
        if (firstInvalidInput) {
            firstInvalidInput.focus();
            firstInvalidInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    
    initModals() {
        // Auto-focus first input in modals
        $$('.modal').forEach(modal => {
            modal.addEventListener('shown.bs.modal', () => {
                const firstInput = modal.querySelector('input, select, textarea, button');
                if (firstInput) {
                    firstInput.focus();
                }
            });
        });
    }
    
    initTabs() {
        // Save active tab state
        $$('[data-bs-toggle="tab"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                const tabId = e.target.getAttribute('href') || e.target.dataset.bsTarget;
                if (tabId) {
                    localStorage.setItem('activeTab', tabId);
                }
            });
        });
        
        // Restore active tab
        const activeTab = localStorage.getItem('activeTab');
        if (activeTab) {
            const tab = $(`[href="${activeTab}"], [data-bs-target="${activeTab}"]`);
            if (tab && window.bootstrap) {
                new bootstrap.Tab(tab).show();
            }
        }
    }
    
    initDropdowns() {
        // Enhanced dropdown functionality
        $$('.dropdown-toggle').forEach(toggle => {
            toggle.addEventListener('click', (e) => {
                const dropdown = toggle.nextElementSibling;
                if (dropdown && dropdown.classList.contains('dropdown-menu')) {
                    e.preventDefault();
                    dropdown.classList.toggle('show');
                }
            });
        });
        
        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.dropdown')) {
                $$('.dropdown-menu.show').forEach(menu => {
                    menu.classList.remove('show');
                });
            }
        });
    }
    
    // ========================================================================
    // PUBLIC API
    // ========================================================================
    
    // Component registration
    registerComponent(name, component) {
        this.components.set(name, component);
        if (typeof component.init === 'function') {
            component.init();
        }
    }
    
    getComponent(name) {
        return this.components.get(name);
    }
    
    // Utility methods
    highlight(element, duration = 2000) {
        element.style.boxShadow = '0 0 10px rgba(0, 123, 255, 0.5)';
        element.style.transition = 'box-shadow 0.3s ease';
        
        setTimeout(() => {
            element.style.boxShadow = '';
        }, duration);
    }
    
    scrollTo(element, offset = 100) {
        const elementPosition = element.offsetTop - offset;
        window.scrollTo({
            top: elementPosition,
            behavior: 'smooth'
        });
    }
    
    // Cleanup
    destroy() {
        if (this.intersectionObserver) {
            this.intersectionObserver.disconnect();
        }
        
        this.hideTooltip();
        this.components.clear();
        this.initialized = false;
    }
}

// Create and export singleton instance
const uiManager = new UIManager();

// Export for global access
export default uiManager;
export { UIManager };

// Global assignment for backward compatibility
window.UIManager = uiManager;
