/**
 * SmartExam - Extra JavaScript Functionality
 * This file contains additional JavaScript functions for the SmartExam application.
 */

// Wait for the DOM to be fully loaded before executing
document.addEventListener('DOMContentLoaded', function() {
    initializeExtraFunctionality();
});

/**
 * Initialize all extra functionality
 */
function initializeExtraFunctionality() {
    setupTimers();
    setupFormValidation();
    setupNavigationWarnings();
    setupAccessibilityFeatures();
}

/**
 * Sets up exam timers if they exist on the page
 */
function setupTimers() {
    const timerElements = document.querySelectorAll('.exam-timer');
    
    timerElements.forEach(timer => {
        if (timer.dataset.duration) {
            startCountdown(timer, parseInt(timer.dataset.duration));
        }
    });
}

/**
 * Starts a countdown timer
 * @param {HTMLElement} element - The timer element
 * @param {number} duration - Duration in seconds
 */
function startCountdown(element, duration) {
    let remainingTime = duration;
    
    const interval = setInterval(() => {
        remainingTime--;
        
        if (remainingTime <= 0) {
            clearInterval(interval);
            element.classList.add('time-expired');
            triggerTimeAlert();
        }
        
        updateTimerDisplay(element, remainingTime);
    }, 1000);
}

/**
 * Updates the timer display
 * @param {HTMLElement} element - The timer element
 * @param {number} seconds - Remaining seconds
 */
function updateTimerDisplay(element, seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    
    element.textContent = `${padZero(hours)}:${padZero(minutes)}:${padZero(remainingSeconds)}`;
    
    // Add warning class when less than 5 minutes remaining
    if (seconds < 300) {
        element.classList.add('timer-warning');
    }
}

/**
 * Pads a number with leading zero if needed
 * @param {number} num - The number to pad
 * @returns {string} - Padded number string
 */
function padZero(num) {
    return num.toString().padStart(2, '0');
}

/**
 * Shows an alert when time expires
 */
function triggerTimeAlert() {
    const alertContainer = document.querySelector('.alert-container') || document.createElement('div');
    
    if (!document.querySelector('.alert-container')) {
        alertContainer.className = 'alert-container';
        document.body.appendChild(alertContainer);
    }
    
    alertContainer.innerHTML = `
        <div class="alert alert-warning">
            <strong>Time's up!</strong> Please submit your exam now.
            <button type="button" class="close-alert" aria-label="Close">&times;</button>
        </div>
    `;
    
    document.querySelector('.close-alert').addEventListener('click', function() {
        alertContainer.innerHTML = '';
    });
}

/**
 * Sets up form validation for exam submissions
 */
function setupFormValidation() {
    const examForms = document.querySelectorAll('form.exam-form');
    
    examForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!validateExamForm(this)) {
                event.preventDefault();
            }
        });
    });
}

/**
 * Validates an exam form before submission
 * @param {HTMLFormElement} form - The form to validate
 * @returns {boolean} - Whether the form is valid
 */
function validateExamForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            isValid = false;
            highlightInvalidField(field);
        } else {
            removeInvalidHighlight(field);
        }
    });
    
    return isValid;
}

/**
 * Highlights an invalid form field
 * @param {HTMLElement} field - The field to highlight
 */
function highlightInvalidField(field) {
    field.classList.add('invalid-field');
    
    const errorMessage = document.createElement('div');
    errorMessage.className = 'error-message';
    errorMessage.textContent = 'This field is required';
    
    if (!field.nextElementSibling || !field.nextElementSibling.classList.contains('error-message')) {
        field.parentNode.insertBefore(errorMessage, field.nextElementSibling);
    }
}

/**
 * Removes invalid highlighting from a field
 * @param {HTMLElement} field - The field to update
 */
function removeInvalidHighlight(field) {
    field.classList.remove('invalid-field');
    
    if (field.nextElementSibling && field.nextElementSibling.classList.contains('error-message')) {
        field.nextElementSibling.remove();
    }
}

/**
 * Sets up navigation warnings to prevent accidental page exits
 */
function setupNavigationWarnings() {
    const examForms = document.querySelectorAll('form.exam-form');
    
    if (examForms.length > 0) {
        window.addEventListener('beforeunload', function(event) {
            // Cancel the event and show confirmation dialog
            event.preventDefault();
            // Chrome requires returnValue to be set
            event.returnValue = '';
        });
    }
}

/**
 * Sets up accessibility features
 */
function setupAccessibilityFeatures() {
    // Add focus indicators
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Tab') {
            document.body.classList.add('keyboard-navigation');
        }
    });
    
    document.addEventListener('mousedown', function() {
        document.body.classList.remove('keyboard-navigation');
    });
    
    // Add high contrast toggle if it exists
    const contrastToggle = document.querySelector('.contrast-toggle');
    
    if (contrastToggle) {
        contrastToggle.addEventListener('click', function() {
            document.body.classList.toggle('high-contrast');
            
            // Save preference
            const highContrast = document.body.classList.contains('high-contrast');
            localStorage.setItem('high-contrast', highContrast);
        });
        
        // Check saved preference
        if (localStorage.getItem('high-contrast') === 'true') {
            document.body.classList.add('high-contrast');
        }
    }
}

// Add inactivity timeout functionality to automatically log out idle users
document.addEventListener('DOMContentLoaded', function() {
    // Only apply to logged-in users
    if (document.body.classList.contains('logged-in')) {
        // Configuration (15 minutes in milliseconds)
        const idleTimeout = 15 * 60 * 1000; 
        let idleTimer = null;
        
        // Events that reset the idle timer
        const resetEvents = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
        
        // Function to handle idle timeout
        function handleIdle() {
            // Show a warning dialog first
            if (confirm('You have been inactive for a while. Click OK to stay logged in or Cancel to log out.')) {
                // User clicked OK - reset the timer and make an ajax call to ping the server
                resetIdleTimer();
                
                // Send a ping to the server to keep the session alive
                fetch('/api/ping/', { 
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    } 
                })
                .catch(error => console.error('Error pinging server:', error));
            } else {
                // User clicked Cancel - redirect to logout
                window.location.href = '/logout/';
            }
        }
        
        // Function to reset the idle timer
        function resetIdleTimer() {
            if (idleTimer) {
                clearTimeout(idleTimer);
            }
            idleTimer = setTimeout(handleIdle, idleTimeout);
        }
        
        // Helper function to get CSRF token
        function getCsrfToken() {
            const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
            if (tokenElement) {
                return tokenElement.value;
            } else {
                // Fallback: try to get it from cookies
                return document.cookie.split(';')
                    .find(c => c.trim().startsWith('csrftoken='))
                    ?.split('=')[1] || '';
            }
        }
        
        // Add event listeners to reset the timer
        resetEvents.forEach(eventType => {
            document.addEventListener(eventType, resetIdleTimer, false);
        });
        
        // Initialize the timer
        resetIdleTimer();
    }
});

// Function to handle "Try Again" button on connection-limit page
document.addEventListener('DOMContentLoaded', function() {
    const tryAgainBtn = document.querySelector('.connection-limit-reload');
    if (tryAgainBtn) {
        tryAgainBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Add a small delay before reload to allow any pending connections to close
            setTimeout(function() {
                window.location.reload();
            }, 1000);
        });
    }
});