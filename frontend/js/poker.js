/**
 * Interactive Poker Game - Frontend JavaScript
 * Enhances the UI with dynamic effects, animations, and interactivity
 */

// Wait for the document to be ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize game UI components
    initializePokerUI();
    
    // Add event listeners for chip selections
    setupChipSelection();
    
    // Setup sound effects if enabled
    setupSoundEffects();
    
    // Add animation observers
    setupAnimationObservers();
});

/**
 * Initialize the poker game UI components
 */
function initializePokerUI() {
    // Apply theme based on session state
    applyTheme();
    
    // Initialize tooltips
    addTooltips();
    
    // Make cards interactive
    makeCardsInteractive();
    
    // Responsive adjustments
    handleResponsiveLayout();
    
    // Add visual feedback for actions
    setupActionFeedback();
}

/**
 * Apply the current theme to the entire UI
 */
function applyTheme() {
    // Get current theme from streamlit state
    const theme = window.theme || 'dark';
    
    // Apply body class
    document.body.classList.remove('dark', 'light');
    document.body.classList.add(theme);
    
    // Update theme-specific elements
    const themeElements = document.querySelectorAll('[data-theme]');
    themeElements.forEach(el => {
        const darkValue = el.dataset.themeDark || '';
        const lightValue = el.dataset.themeLight || '';
        
        if (theme === 'dark') {
            el.setAttribute(el.dataset.theme, darkValue);
        } else {
            el.setAttribute(el.dataset.theme, lightValue);
        }
    });
}

/**
 * Listen for theme changes from Streamlit
 */
window.addEventListener('message', function(event) {
    const data = event.data;
    
    // If the message contains theme information
    if (data.theme) {
        window.theme = data.theme;
        applyTheme();
    }
});

/**
 * Add tooltips to UI elements
 */
function addTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(el => {
        // Create tooltip element
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.textContent = el.dataset.tooltip;
        
        // Show tooltip on hover
        el.addEventListener('mouseenter', () => {
            document.body.appendChild(tooltip);
            const rect = el.getBoundingClientRect();
            tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
            tooltip.style.top = `${rect.top - tooltip.offsetHeight - 10}px`;
            tooltip.classList.add('visible');
        });
        
        // Hide tooltip when mouse leaves
        el.addEventListener('mouseleave', () => {
            tooltip.classList.remove('visible');
            setTimeout(() => {
                if (tooltip.parentNode) {
                    tooltip.parentNode.removeChild(tooltip);
                }
            }, 300);
        });
    });
}

/**
 * Make playing cards interactive with hover effects
 */
function makeCardsInteractive() {
    const cards = document.querySelectorAll('.playing-card');
    
    cards.forEach(card => {
        // Add hover effect
        card.addEventListener('mouseenter', () => {
            card.classList.add('card-hover');
        });
        
        card.addEventListener('mouseleave', () => {
            card.classList.remove('card-hover');
        });
        
        // Add click sound if enabled
        card.addEventListener('click', () => {
            playSound('card');
        });
    });
}

/**
 * Setup chip selection interaction
 */
function setupChipSelection() {
    const chips = document.querySelectorAll('.chip');
    
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            // Remove selection from other chips
            chips.forEach(c => c.classList.remove('selected'));
            
            // Select this chip
            chip.classList.add('selected');
            
            // Play sound
            playSound('chip');
            
            // Update raise slider value if applicable
            const chipValue = parseInt(chip.dataset.value, 10);
            const raiseSlider = document.getElementById('raise-slider');
            if (raiseSlider) {
                const minRaise = parseInt(raiseSlider.getAttribute('min'), 10);
                const maxRaise = parseInt(raiseSlider.getAttribute('max'), 10);
                
                // Calculate new value based on chip
                let newValue = minRaise + chipValue;
                
                // Ensure it's within bounds
                newValue = Math.min(Math.max(newValue, minRaise), maxRaise);
                
                // Update slider
                raiseSlider.value = newValue;
                
                // Trigger input event to update Streamlit
                const event = new Event('input', { bubbles: true });
                raiseSlider.dispatchEvent(event);
                
                // Update displayed value
                const valueDisplay = document.getElementById('raise-value');
                if (valueDisplay) {
                    valueDisplay.textContent = `$${newValue}`;
                }
            }
        });
    });
}

/**
 * Setup sound effects system
 */
function setupSoundEffects() {
    // Only initialize if sounds are enabled
    const soundEnabled = window.soundEnabled !== false;
    
    if (!soundEnabled) return;
    
    // Preload sound effects
    window.sounds = {
        card: new Audio('frontend/audio/card_slide.mp3'),
        chip: new Audio('frontend/audio/chip_stack.mp3'),
        win: new Audio('frontend/audio/win_sound.mp3'),
        lose: new Audio('frontend/audio/lose_sound.mp3'),
        deal: new Audio('frontend/audio/card_shuffle.mp3'),
        button: new Audio('frontend/audio/button_click.mp3')
    };
    
    // Adjust volume
    Object.values(window.sounds).forEach(sound => {
        sound.volume = 0.5;
    });
}

/**
 * Play a sound effect
 * @param {string} soundName - Name of the sound to play
 */
function playSound(soundName) {
    if (!window.sounds || window.soundEnabled === false) return;
    
    const sound = window.sounds[soundName];
    if (sound) {
        sound.currentTime = 0;
        sound.play().catch(e => console.error("Error playing sound:", e));
    }
}

/**
 * Setup animation observers to trigger animations when elements enter viewport
 */
function setupAnimationObservers() {
    if (!window.IntersectionObserver) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                observer.unobserve(entry.target);
            }
        });
    }, {
        root: null,
        threshold: 0.1,
        rootMargin: '0px'
    });
    
    // Observe elements with animate class
    document.querySelectorAll('.animate-on-view').forEach(el => {
        observer.observe(el);
    });
}

/**
 * Setup responsive layout adjustments
 */
function handleResponsiveLayout() {
    // Initial check
    adjustLayout();
    
    // Listen for window resize
    window.addEventListener('resize', adjustLayout);
}

/**
 * Adjust layout based on window size
 */
function adjustLayout() {
    const isMobile = window.innerWidth < 768;
    
    if (isMobile) {
        document.body.classList.add('mobile-view');
    } else {
        document.body.classList.remove('mobile-view');
    }
    
    // Adjust card sizes
    const cards = document.querySelectorAll('.playing-card');
    const cardSize = isMobile ? '60px' : '90px';
    cards.forEach(card => {
        card.style.width = cardSize;
    });
    
    // Adjust chip sizes
    const chips = document.querySelectorAll('.chip');
    const chipSize = isMobile ? '50px' : '60px';
    chips.forEach(chip => {
        chip.style.width = chipSize;
        chip.style.height = chipSize;
    });
}

/**
 * Setup visual feedback for poker actions
 */
function setupActionFeedback() {
    // Action buttons click effects
    const actionButtons = document.querySelectorAll('.action-button');
    
    actionButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Add click class
            button.classList.add('clicked');
            
            // Play button sound
            playSound('button');
            
            // Remove class after animation
            setTimeout(() => {
                button.classList.remove('clicked');
            }, 300);
        });
    });
    
    // Handle win/lose animations
    const winElements = document.querySelectorAll('.win-animation');
    if (winElements.length > 0) {
        playSound('win');
    }
    
    const loseElements = document.querySelectorAll('.lose-animation');
    if (loseElements.length > 0) {
        playSound('lose');
    }
}

/**
 * Update game stats visualizations
 * @param {Object} stats - Game statistics data
 */
function updateStats(stats) {
    if (!stats) return;
    
    // Update bankroll chart
    if (stats.bankrollHistory && window.Plotly) {
        const chartElement = document.getElementById('bankroll-chart');
        if (chartElement) {
            const data = [{
                x: stats.bankrollHistory.hands,
                y: stats.bankrollHistory.values,
                type: 'scatter',
                mode: 'lines+markers',
                line: { color: document.body.classList.contains('dark') ? '#533483' : '#4DA167' }
            }];
            
            const layout = {
                title: 'Bankroll History',
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: {
                    color: document.body.classList.contains('dark') ? '#E6E6E6' : '#333333'
                },
                margin: { t: 40, r: 30, b: 40, l: 50 }
            };
            
            Plotly.newPlot(chartElement, data, layout);
        }
    }
    
    // Update win rate gauge
    if (stats.winRate !== undefined && window.Plotly) {
        const gaugeElement = document.getElementById('win-rate-gauge');
        if (gaugeElement) {
            const data = [{
                type: 'indicator',
                mode: 'gauge+number',
                value: stats.winRate,
                title: { text: 'Win Rate %' },
                gauge: {
                    axis: { range: [0, 100] },
                    bar: { color: document.body.classList.contains('dark') ? '#533483' : '#4DA167' },
                    bgcolor: 'rgba(255, 255, 255, 0.1)',
                    borderwidth: 2,
                    bordercolor: document.body.classList.contains('dark') ? '#0F3460' : '#805A46'
                }
            }];
            
            const layout = {
                paper_bgcolor: 'rgba(0,0,0,0)',
                font: {
                    color: document.body.classList.contains('dark') ? '#E6E6E6' : '#333333'
                },
                margin: { t: 40, r: 30, b: 20, l: 30 }
            };
            
            Plotly.newPlot(gaugeElement, data, layout);
        }
    }
}

// Expose for Streamlit to call
window.updateStats = updateStats;