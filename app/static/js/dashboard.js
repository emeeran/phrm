// Dashboard-specific JavaScript for PHRM
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

function initializeDashboard() {
    initializeActionCards();
    initializeRecordItems();
    initializeStatsAnimation();
    initializeLoadingStates();
    initializeRAGFunctionality();
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

function initializeRAGFunctionality() {
    const startVectorizationBtn = document.getElementById('start-vectorization-btn');

    if (startVectorizationBtn) {
        startVectorizationBtn.addEventListener('click', function() {
            startVectorization();
        });
    }

    // Auto-refresh RAG status if processing
    if (window.ragStatus && window.ragStatus.is_processing) {
        // Check status every 30 seconds
        setInterval(checkRAGStatus, 30000);
    }
}

function startVectorization() {
    const btn = document.getElementById('start-vectorization-btn');
    if (!btn) return;

    // Update button state
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Starting...';

    fetch('/api/rag/start-vectorization', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Replace the empty state with processing message
            const emptyState = btn.closest('.empty-state');
            if (emptyState) {
                emptyState.innerHTML = `
                    <i class="fas fa-spinner fa-spin text-primary"></i>
                    <p><strong>Processing Reference Books</strong></p>
                    <p class="small">This may take several minutes for large files. The page will automatically update when complete.</p>
                `;
            }

            // Start checking status
            setTimeout(() => {
                checkRAGStatus();
                setInterval(checkRAGStatus, 30000);
            }, 5000);
        } else {
            // Reset button on error
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-cogs me-1"></i>Start Processing Reference Books';
            alert('Failed to start processing: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error starting vectorization:', error);
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-cogs me-1"></i>Start Processing Reference Books';
        alert('Failed to start processing. Please try again.');
    });
}

function checkRAGStatus() {
    fetch('/api/rag/status')
    .then(response => response.json())
    .then(data => {
        if (data.success && data.status) {
            const status = data.status;

            // If processing is complete and we have processed files, reload the page
            if (!status.is_processing && status.processed_files_count > 0) {
                location.reload();
            }
        }
    })
    .catch(error => {
        console.error('Error checking RAG status:', error);
    });
}

function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute('content') : '';
}
