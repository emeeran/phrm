// Dashboard-specific JavaScript for PHRM
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

function initializeDashboard() {
    initializeActionCards();
    initializeRecordItems();
    initializeStatsAnimation();
    initializeLoadingStates();
}

function initializeActionCards() {
    const actionCards = document.querySelectorAll('.action-card');

    actionCards.forEach(card => {
        // Add loading state on click
        card.addEventListener('click', function(e) {
            this.classList.add('loading');

            // Remove loading state after navigation or timeout
            setTimeout(() => {
                this.classList.remove('loading');
            }, 1000);
        });

        // Add ripple effect on mobile
        if (window.innerWidth <= 768) {
            card.addEventListener('touchstart', function(e) {
                this.style.transform = 'scale(0.95)';
            });

            card.addEventListener('touchend', function(e) {
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
            });
        }
    });
}

function initializeRecordItems() {
    const recordItems = document.querySelectorAll('.record-item');

    recordItems.forEach(item => {
        // Make entire record item clickable
        item.addEventListener('click', function(e) {
            if (e.target.tagName !== 'A') {
                const link = this.querySelector('.record-title');
                if (link) {
                    window.location.href = link.href;
                }
            }
        });

        // Add keyboard navigation
        item.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const link = this.querySelector('.record-title');
                if (link) {
                    link.click();
                }
            }
        });

        // Make focusable for accessibility
        item.setAttribute('tabindex', '0');
        item.setAttribute('role', 'button');
    });
}

function initializeStatsAnimation() {
    const statNumbers = document.querySelectorAll('.stat-number');

    // Animate stats on page load
    statNumbers.forEach(stat => {
        const finalValue = parseInt(stat.textContent);
        let currentValue = 0;
        const increment = finalValue / 20;
        const timer = setInterval(() => {
            currentValue += increment;
            if (currentValue >= finalValue) {
                currentValue = finalValue;
                clearInterval(timer);
            }
            stat.textContent = Math.floor(currentValue);
        }, 50);
    });
}

function initializeLoadingStates() {
    // Add loading states to buttons in empty states
    const buttons = document.querySelectorAll('.empty-state .btn');

    buttons.forEach(button => {
        button.addEventListener('click', function() {
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Loading...';
            this.disabled = true;

            // Reset after a short delay (will be replaced by actual navigation)
            setTimeout(() => {
                this.innerHTML = originalText;
                this.disabled = false;
            }, 2000);
        });
    });
}

// Add smooth reveal animation for panels
function revealPanels() {
    const panels = document.querySelectorAll('.records-panel');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    panels.forEach(panel => {
        panel.style.opacity = '0';
        panel.style.transform = 'translateY(20px)';
        panel.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(panel);
    });
}

// Initialize reveal animation after DOM is ready
setTimeout(revealPanels, 100);

// Add utility for refreshing dashboard stats
window.refreshDashboardStats = function() {
    // This would connect to an API endpoint to get updated stats
    console.log('Dashboard stats refresh requested');

    // Simulate loading state
    const statNumbers = document.querySelectorAll('.stat-number');
    statNumbers.forEach(stat => {
        stat.style.opacity = '0.5';
        setTimeout(() => {
            stat.style.opacity = '1';
        }, 500);
    });
};
