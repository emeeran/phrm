/**
 * PHRM Modern UI Enhancement Library
 * Provides interactive animations, micro-interactions, and enhanced UX
 */

class ModernUIManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupAnimationObserver();
        this.enhanceCards();
        this.setupRippleEffects();
        this.enhanceButtons();
        this.setupLoadingStates();
        this.initTooltips();
        this.setupGlassEffects();
        this.initMinimalistInteractions();
    }

    /**
     * Set up intersection observer for scroll animations
     */
    setupAnimationObserver() {
        if (!window.IntersectionObserver) return;

        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    entry.target.style.animationDelay = `${Math.random() * 0.3}s`;
                }
            });
        }, observerOptions);

        // Observe cards and action items
        document.querySelectorAll('.card-modern, .action-card-modern, .stat-card-modern').forEach(card => {
            card.classList.add('animate-ready');
            observer.observe(card);
        });
    }

    /**
     * Enhance card interactions
     */
    enhanceCards() {
        document.querySelectorAll('.card-modern, .stat-card-modern').forEach(card => {
            card.addEventListener('mouseenter', () => {
                this.addHoverGlow(card);
            });

            card.addEventListener('mouseleave', () => {
                this.removeHoverGlow(card);
            });
        });
    }

    /**
     * Add glow effect on hover
     */
    addHoverGlow(element) {
        element.style.boxShadow = '0 20px 40px rgba(102, 126, 234, 0.2)';
    }

    /**
     * Remove glow effect
     */
    removeHoverGlow(element) {
        element.style.boxShadow = '';
    }

    /**
     * Add ripple effects to buttons and clickable elements
     */
    setupRippleEffects() {
        document.querySelectorAll('.btn-modern, .action-card-modern').forEach(element => {
            element.addEventListener('click', (e) => {
                this.createRipple(e, element);
            });
        });
    }

    /**
     * Create ripple effect
     */
    createRipple(event, element) {
        const ripple = document.createElement('span');
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;

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

        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);

        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    /**
     * Enhance button interactions
     */
    enhanceButtons() {
        document.querySelectorAll('.btn-modern-primary, .btn-modern-outline').forEach(button => {
            button.addEventListener('mouseenter', () => {
                button.style.transform = 'translateY(-2px) scale(1.02)';
            });

            button.addEventListener('mouseleave', () => {
                button.style.transform = '';
            });

            button.addEventListener('mousedown', () => {
                button.style.transform = 'translateY(-1px) scale(0.98)';
            });

            button.addEventListener('mouseup', () => {
                button.style.transform = 'translateY(-2px) scale(1.02)';
            });
        });
    }

    /**
     * Setup loading states for forms and actions
     */
    setupLoadingStates() {
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => {
                const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
                if (submitButton) {
                    this.showLoadingState(submitButton);
                }
            });
        });
    }

    /**
     * Show loading state on element
     */
    showLoadingState(element) {
        const originalContent = element.innerHTML;
        element.setAttribute('data-original-content', originalContent);
        element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
        element.disabled = true;
        element.classList.add('loading-modern');

        // Restore after 10 seconds as fallback
        setTimeout(() => {
            this.hideLoadingState(element);
        }, 10000);
    }

    /**
     * Hide loading state
     */
    hideLoadingState(element) {
        const originalContent = element.getAttribute('data-original-content');
        if (originalContent) {
            element.innerHTML = originalContent;
            element.disabled = false;
            element.classList.remove('loading-modern');
            element.removeAttribute('data-original-content');
        }
    }

    /**
     * Initialize enhanced tooltips
     */
    initTooltips() {
        // Create custom tooltip container
        if (!document.getElementById('modern-tooltip-container')) {
            const container = document.createElement('div');
            container.id = 'modern-tooltip-container';
            container.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                pointer-events: none;
                z-index: 10000;
            `;
            document.body.appendChild(container);
        }

        document.querySelectorAll('[data-tooltip]').forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target, e.target.getAttribute('data-tooltip'));
            });

            element.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
    }

    /**
     * Show custom tooltip
     */
    showTooltip(element, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'modern-tooltip';
        tooltip.textContent = text;
        tooltip.style.cssText = `
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            position: absolute;
            z-index: 10001;
            opacity: 0;
            transform: translateY(10px);
            transition: all 0.3s ease;
            pointer-events: none;
            white-space: nowrap;
        `;

        const container = document.getElementById('modern-tooltip-container');
        container.appendChild(tooltip);

        const rect = element.getBoundingClientRect();
        tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
        tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;

        // Animate in
        requestAnimationFrame(() => {
            tooltip.style.opacity = '1';
            tooltip.style.transform = 'translateY(0)';
        });
    }

    /**
     * Hide tooltip
     */
    hideTooltip() {
        const container = document.getElementById('modern-tooltip-container');
        const tooltip = container.querySelector('.modern-tooltip');
        if (tooltip) {
            tooltip.style.opacity = '0';
            tooltip.style.transform = 'translateY(10px)';
            setTimeout(() => tooltip.remove(), 300);
        }
    }

    /**
     * Setup glass morphism effects
     */
    setupGlassEffects() {
        // Apply glass effect to modals and dropdowns
        document.querySelectorAll('.modal-content, .dropdown-menu').forEach(element => {
            element.classList.add('glass-effect');
        });
    }

    /**
     * Show success notification
     */
    showSuccessNotification(message, duration = 5000) {
        this.showNotification(message, 'success', duration);
    }

    /**
     * Show error notification
     */
    showErrorNotification(message, duration = 7000) {
        this.showNotification(message, 'error', duration);
    }

    /**
     * Show info notification
     */
    showInfoNotification(message, duration = 4000) {
        this.showNotification(message, 'info', duration);
    }

    /**
     * Show notification with modern styling
     */
    showNotification(message, type = 'info', duration = 5000) {
        // Create notification container if it doesn't exist
        let container = document.getElementById('modern-notifications');
        if (!container) {
            container = document.createElement('div');
            container.id = 'modern-notifications';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }

        const notification = document.createElement('div');
        const colors = {
            success: 'var(--success-gradient)',
            error: 'var(--danger-gradient)',
            warning: 'var(--warning-gradient)',
            info: 'var(--primary-gradient)'
        };

        notification.style.cssText = `
            background: ${colors[type] || colors.info};
            color: white;
            padding: 16px 20px;
            border-radius: 12px;
            margin-bottom: 10px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
            transform: translateX(400px);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            font-weight: 500;
            font-size: 14px;
            line-height: 1.5;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        `;

        notification.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="background: none; border: none; color: white; cursor: pointer; opacity: 0.8; font-size: 18px; margin-left: 12px;">
                    ×
                </button>
            </div>
        `;

        container.appendChild(notification);

        // Animate in
        requestAnimationFrame(() => {
            notification.style.transform = 'translateX(0)';
        });

        // Auto remove
        setTimeout(() => {
            notification.style.transform = 'translateX(400px)';
            setTimeout(() => notification.remove(), 400);
        }, duration);
    }

    /**
     * Smooth scroll to element
     */
    scrollToElement(selector, offset = 100) {
        const element = document.querySelector(selector);
        if (element) {
            const top = element.offsetTop - offset;
            window.scrollTo({
                top: top,
                behavior: 'smooth'
            });
        }
    }

    /**
     * Add pulsing animation to element
     */
    addPulse(element, duration = 2000) {
        element.style.animation = `pulse ${duration}ms ease-in-out infinite`;
        setTimeout(() => {
            element.style.animation = '';
        }, duration * 3);
    }

    /**
     * Highlight element with glow effect
     */
    highlightElement(element, duration = 3000) {
        const originalBoxShadow = element.style.boxShadow;
        element.style.boxShadow = '0 0 20px rgba(102, 126, 234, 0.6)';
        element.style.transition = 'box-shadow 0.3s ease';

        setTimeout(() => {
            element.style.boxShadow = originalBoxShadow;
        }, duration);
    }

    /**
     * Initialize ultra-minimalist interactions
     */
    initMinimalistInteractions() {
        this.initSmartScrollEffects();
        this.initGestureSupport();
        this.initAdvancedNotifications();
        this.initProgressIndicators();
        this.initSmartSearch();
        this.initContentAnimations();
        this.initAccessibilityEnhancements();
    }

    /**
     * Smart scroll effects for minimalist design
     */
    initSmartScrollEffects() {
        let lastScrollY = window.scrollY;
        let isScrolling = false;

        const header = document.querySelector('.header-minimal, .navbar');
        if (header) {
            window.addEventListener('scroll', () => {
                if (!isScrolling) {
                    requestAnimationFrame(() => {
                        const currentScrollY = window.scrollY;
                        const scrollDifference = currentScrollY - lastScrollY;

                        // Auto-hide header on scroll down, show on scroll up
                        if (scrollDifference > 10 && currentScrollY > 100) {
                            header.style.transform = 'translateY(-100%)';
                        } else if (scrollDifference < -10 || currentScrollY <= 100) {
                            header.style.transform = 'translateY(0)';
                        }

                        // Add backdrop blur based on scroll position
                        const blurAmount = Math.min(currentScrollY / 100 * 10, 10);
                        header.style.backdropFilter = `blur(${blurAmount}px)`;

                        lastScrollY = currentScrollY;
                        isScrolling = false;
                    });
                }
                isScrolling = true;
            }, { passive: true });
        }

        // Parallax effect for hero sections
        const heroElements = document.querySelectorAll('.hero-section, .hero-minimal');
        heroElements.forEach(hero => {
            window.addEventListener('scroll', () => {
                const scrolled = window.pageYOffset;
                const rate = scrolled * -0.5;
                hero.style.transform = `translateY(${rate}px)`;
            }, { passive: true });
        });
    }

    /**
     * Gesture support for mobile interactions
     */
    initGestureSupport() {
        let startX, startY, currentX, currentY;
        let isSwipeGesture = false;

        // Swipe to dismiss notifications
        document.addEventListener('touchstart', (e) => {
            if (e.target.closest('.notification')) {
                startX = e.touches[0].clientX;
                startY = e.touches[0].clientY;
                isSwipeGesture = true;
            }
        }, { passive: true });

        document.addEventListener('touchmove', (e) => {
            if (!isSwipeGesture) return;
            
            currentX = e.touches[0].clientX;
            currentY = e.touches[0].clientY;
            
            const notification = e.target.closest('.notification');
            if (notification) {
                const deltaX = currentX - startX;
                if (Math.abs(deltaX) > 50) {
                    notification.style.transform = `translateX(${deltaX}px)`;
                    notification.style.opacity = Math.max(0.3, 1 - Math.abs(deltaX) / 200);
                }
            }
        }, { passive: true });

        document.addEventListener('touchend', (e) => {
            if (!isSwipeGesture) return;
            
            const notification = e.target.closest('.notification');
            if (notification) {
                const deltaX = currentX - startX;
                if (Math.abs(deltaX) > 100) {
                    // Dismiss notification
                    notification.style.transform = `translateX(${deltaX > 0 ? '100%' : '-100%'})`;
                    setTimeout(() => notification.remove(), 300);
                } else {
                    // Restore position
                    notification.style.transform = 'translateX(0)';
                    notification.style.opacity = '1';
                }
            }
            isSwipeGesture = false;
        });

        // Pull to refresh gesture
        let isPulling = false;
        let pullDistance = 0;

        document.addEventListener('touchstart', (e) => {
            if (window.scrollY === 0) {
                startY = e.touches[0].clientY;
                isPulling = true;
            }
        }, { passive: true });

        document.addEventListener('touchmove', (e) => {
            if (!isPulling || window.scrollY > 0) return;
            
            currentY = e.touches[0].clientY;
            pullDistance = Math.max(0, currentY - startY);
            
            if (pullDistance > 50) {
                document.body.style.transform = `translateY(${Math.min(pullDistance / 3, 50)}px)`;
                document.body.style.transition = 'none';
            }
        }, { passive: true });

        document.addEventListener('touchend', () => {
            if (isPulling && pullDistance > 100) {
                // Trigger refresh
                window.location.reload();
            } else {
                document.body.style.transform = '';
                document.body.style.transition = 'transform 0.3s ease';
            }
            isPulling = false;
            pullDistance = 0;
        });
    }

    /**
     * Advanced notification system
     */
    initAdvancedNotifications() {
        // Create notification container if it doesn't exist
        if (!document.getElementById('notification-container')) {
            const container = document.createElement('div');
            container.id = 'notification-container';
            container.style.cssText = `
                position: fixed;
                top: 2rem;
                right: 2rem;
                z-index: 10000;
                pointer-events: none;
            `;
            document.body.appendChild(container);
        }

        // Enhanced notification function
        window.showNotification = (message, type = 'info', duration = 5000, actions = []) => {
            const container = document.getElementById('notification-container');
            const notification = document.createElement('div');
            
            notification.className = `notification notification-${type} show`;
            notification.style.cssText = `
                pointer-events: auto;
                margin-bottom: 1rem;
                animation: slideInRight 0.3s ease-out;
            `;

            let actionsHtml = '';
            if (actions.length > 0) {
                actionsHtml = `
                    <div style="margin-top: 0.75rem; display: flex; gap: 0.5rem;">
                        ${actions.map(action => `
                            <button class="btn-minimal" onclick="${action.onClick}" style="padding: 0.25rem 0.75rem; font-size: 0.875rem;">
                                ${action.text}
                            </button>
                        `).join('')}
                    </div>
                `;
            }

            notification.innerHTML = `
                <div style="display: flex; align-items: flex-start; justify-content: space-between;">
                    <div style="flex: 1;">
                        <div style="font-weight: 500; margin-bottom: 0.25rem;">${message}</div>
                        ${actionsHtml}
                    </div>
                    <button class="btn-icon" onclick="this.closest('.notification').remove()" style="margin-left: 1rem;">
                        <span>&times;</span>
                    </button>
                </div>
            `;

            container.appendChild(notification);

            // Auto-dismiss
            if (duration > 0) {
                setTimeout(() => {
                    notification.style.animation = 'slideOutRight 0.3s ease-in';
                    setTimeout(() => notification.remove(), 300);
                }, duration);
            }

            return notification;
        };

        // Progress notification
        window.showProgressNotification = (message, progress = 0) => {
            const notification = window.showNotification('', 'info', 0);
            notification.innerHTML = `
                <div>
                    <div style="font-weight: 500; margin-bottom: 0.75rem;">${message}</div>
                    <div class="progress-minimal">
                        <div class="progress-bar-minimal" style="width: ${progress}%"></div>
                    </div>
                    <div style="font-size: 0.875rem; color: var(--gray-600); margin-top: 0.5rem;">${progress}%</div>
                </div>
            `;
            return notification;
        };
    }

    /**
     * Smart progress indicators
     */
    initProgressIndicators() {
        // Auto-progress bars
        document.querySelectorAll('[data-auto-progress]').forEach(bar => {
            const duration = parseInt(bar.dataset.autoProgress) || 3000;
            const progressBar = bar.querySelector('.progress-bar-minimal');
            
            if (progressBar) {
                let progress = 0;
                const interval = setInterval(() => {
                    progress += 100 / (duration / 100);
                    progressBar.style.width = `${Math.min(progress, 100)}%`;
                    
                    if (progress >= 100) {
                        clearInterval(interval);
                        bar.dispatchEvent(new CustomEvent('progress-complete'));
                    }
                }, 100);
            }
        });

        // Form progress tracking
        const forms = document.querySelectorAll('form[data-progress-tracker]');
        forms.forEach(form => {
            const fields = form.querySelectorAll('input[required], select[required], textarea[required]');
            const progressBar = form.querySelector('.progress-bar-minimal');
            
            if (progressBar && fields.length > 0) {
                const updateProgress = () => {
                    const completed = Array.from(fields).filter(field => {
                        return field.value.trim() !== '';
                    }).length;
                    
                    const progress = (completed / fields.length) * 100;
                    progressBar.style.width = `${progress}%`;
                };

                fields.forEach(field => {
                    field.addEventListener('input', updateProgress);
                    field.addEventListener('change', updateProgress);
                });

                updateProgress(); // Initial check
            }
        });
    }

    /**
     * Smart search functionality
     */
    initSmartSearch() {
        const searchInputs = document.querySelectorAll('.search-input-minimal');
        
        searchInputs.forEach(input => {
            let searchTimeout;
            
            // Debounced search
            input.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    this.performSearch(e.target.value, e.target);
                }, 300);
            });

            // Search suggestions
            const suggestionContainer = document.createElement('div');
            suggestionContainer.className = 'search-suggestions';
            suggestionContainer.style.cssText = `
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: white;
                border: 1px solid var(--gray-200);
                border-radius: 0.5rem;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                max-height: 200px;
                overflow-y: auto;
                z-index: 1000;
                display: none;
            `;
            
            input.parentElement.style.position = 'relative';
            input.parentElement.appendChild(suggestionContainer);

            // Hide suggestions on outside click
            document.addEventListener('click', (e) => {
                if (!input.parentElement.contains(e.target)) {
                    suggestionContainer.style.display = 'none';
                }
            });
        });
    }

    /**
     * Perform search with smart filtering
     */
    performSearch(query, input) {
        const searchables = document.querySelectorAll('[data-searchable]');
        const suggestions = input.parentElement.querySelector('.search-suggestions');
        
        if (!query.trim()) {
            searchables.forEach(item => item.style.display = '');
            suggestions.style.display = 'none';
            return;
        }

        const matches = [];
        searchables.forEach(item => {
            const searchText = item.dataset.searchable.toLowerCase();
            const queryLower = query.toLowerCase();
            
            if (searchText.includes(queryLower)) {
                item.style.display = '';
                matches.push({
                    element: item,
                    text: item.textContent.trim(),
                    relevance: this.calculateRelevance(searchText, queryLower)
                });
            } else {
                item.style.display = 'none';
            }
        });

        // Show search suggestions
        if (suggestions && matches.length > 0) {
            const topMatches = matches
                .sort((a, b) => b.relevance - a.relevance)
                .slice(0, 5);

            suggestions.innerHTML = topMatches
                .map(match => `
                    <div class="search-suggestion" style="padding: 0.75rem; cursor: pointer; border-bottom: 1px solid var(--gray-100);" 
                         onclick="this.closest('.search-container-minimal').querySelector('input').value = '${match.text}'; this.parentElement.style.display = 'none';">
                        ${match.text}
                    </div>
                `).join('');
            
            suggestions.style.display = 'block';
        } else if (suggestions) {
            suggestions.style.display = 'none';
        }
    }

    /**
     * Calculate search relevance score
     */
    calculateRelevance(text, query) {
        let score = 0;
        
        // Exact match
        if (text === query) score += 100;
        
        // Starts with query
        if (text.startsWith(query)) score += 50;
        
        // Contains query
        if (text.includes(query)) score += 25;
        
        // Word boundaries
        const words = query.split(' ');
        words.forEach(word => {
            if (text.includes(word)) score += 10;
        });
        
        return score;
    }

    /**
     * Content animations for smooth interactions
     */
    initContentAnimations() {
        // Staggered animations for lists
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry, index) => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }, index * 100);
                }
            });
        }, observerOptions);

        // Animate list items
        document.querySelectorAll('.list-group-item-minimal, .card-minimal, .data-card').forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(20px)';
            item.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(item);
        });

        // Smooth state transitions
        document.querySelectorAll('[data-animate-state]').forEach(element => {
            const observer = new MutationObserver(() => {
                element.style.transition = 'all 0.3s ease';
            });
            
            observer.observe(element, {
                attributes: true,
                attributeFilter: ['class', 'style']
            });
        });
    }

    /**
     * Enhanced accessibility features
     */
    initAccessibilityEnhancements() {
        // Skip to main content link
        if (!document.querySelector('.skip-to-main')) {
            const skipLink = document.createElement('a');
            skipLink.href = '#main-content';
            skipLink.className = 'skip-to-main';
            skipLink.textContent = 'Skip to main content';
            skipLink.style.cssText = `
                position: absolute;
                top: -40px;
                left: 6px;
                background: var(--primary);
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

        // Enhanced focus management
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });

        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });

        // Announce dynamic content changes
        const announcer = document.createElement('div');
        announcer.setAttribute('aria-live', 'polite');
        announcer.setAttribute('aria-atomic', 'true');
        announcer.style.cssText = `
            position: absolute;
            left: -10000px;
            width: 1px;
            height: 1px;
            overflow: hidden;
        `;
        document.body.appendChild(announcer);

        // Function to announce messages
        window.announceToScreenReader = (message) => {
            announcer.textContent = message;
            setTimeout(() => {
                announcer.textContent = '';
            }, 1000);
        };

        // Enhance button interactions
        document.querySelectorAll('button, [role="button"]').forEach(button => {
            if (!button.hasAttribute('aria-label') && !button.textContent.trim()) {
                console.warn('Button without accessible label detected:', button);
            }
        });

        // Auto-focus management for modals
        document.addEventListener('show.bs.modal', (e) => {
            const modal = e.target;
            const focusableElements = modal.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            
            if (focusableElements.length > 0) {
                setTimeout(() => {
                    focusableElements[0].focus();
                }, 100);
            }
        });
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }

    @keyframes pulse {
        0%, 100% { 
            opacity: 1; 
            transform: scale(1); 
        }
        50% { 
            opacity: 0.7; 
            transform: scale(1.05); 
        }
    }

    .animate-ready {
        opacity: 0;
        transform: translateY(30px);
        transition: all 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }

    .animate-in {
        opacity: 1 !important;
        transform: translateY(0) !important;
    }

    .loading-modern {
        position: relative;
        pointer-events: none;
    }

    .loading-modern::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(255, 255, 255, 0.8);
        z-index: 1;
        border-radius: inherit;
    }

    .glass-effect {
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }

    /* Enhanced button states */
    .btn-modern:active {
        transform: scale(0.95) !important;
    }

    /* Smooth transitions for all interactive elements */
    .action-card-modern,
    .stat-card-modern,
    .card-modern,
    .btn-modern,
    .btn-modern-primary,
    .btn-modern-outline {
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }

    /* Focus states for accessibility */
    .btn-modern:focus,
    .btn-modern-primary:focus,
    .btn-modern-outline:focus,
    .action-card-modern:focus {
        outline: 3px solid rgba(102, 126, 234, 0.3);
        outline-offset: 2px;
    }

    /* Scroll behavior */
    html {
        scroll-behavior: smooth;
    }

    /* Selection styling */
    ::selection {
        background: rgba(102, 126, 234, 0.3);
        color: inherit;
    }
`;

document.head.appendChild(style);

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.modernUI = new ModernUIManager();
    });
} else {
    window.modernUI = new ModernUIManager();
}

// Export for use in other scripts
window.ModernUIManager = ModernUIManager;
