/**
 * Trading System JavaScript
 * Simple UI interactions using Tailwind CSS
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize basic interactions
    initializeFeatureCards();
    initializeStatusIndicator();
    initializeScrollEffects();
    initializeMobileMenu();
});

/**
 * Initialize feature card interactions
 */
function initializeFeatureCards() {
    const featureCards = document.querySelectorAll('.bg-white.rounded-xl');
    
    featureCards.forEach(card => {
        // Add click effect
        card.addEventListener('click', function() {
            this.classList.add('scale-95');
            setTimeout(() => {
                this.classList.remove('scale-95');
            }, 150);
        });
    });
}

/**
 * Initialize status indicator animation
 */
function initializeStatusIndicator() {
    const statusIndicator = document.querySelector('.animate-pulse');
    if (statusIndicator) {
        // Status indicator is already animated with Tailwind's animate-pulse class
        console.log('Status indicator initialized');
    }
}

/**
 * Initialize scroll-based effects
 */
function initializeScrollEffects() {
    // Simple scroll effects using Tailwind classes
    console.log('Scroll effects initialized');
}

/**
 * Initialize mobile menu toggle
 */
function initializeMobileMenu() {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!mobileMenuButton.contains(event.target) && !mobileMenu.contains(event.target)) {
                mobileMenu.classList.add('hidden');
            }
        });
    }
}

/**
 * Utility function to add smooth scrolling
 */
function smoothScrollTo(element) {
    element.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

/**
 * Add loading states for future API calls
 */
function showLoadingState(element) {
    element.classList.add('opacity-50', 'pointer-events-none');
    element.innerHTML = '<div class="flex items-center justify-center"><div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div></div>';
}

function hideLoadingState(element, originalContent) {
    element.classList.remove('opacity-50', 'pointer-events-none');
    element.innerHTML = originalContent;
}

/**
 * Add notification system for future use
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${
        type === 'success' ? 'bg-green-500 text-white' :
        type === 'error' ? 'bg-red-500 text-white' :
        type === 'warning' ? 'bg-yellow-500 text-black' :
        'bg-blue-500 text-white'
    }`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}
