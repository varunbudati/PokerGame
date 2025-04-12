/**
 * Interactive Poker Game - Frontend JavaScript
 * ===========================================
 * Handles all frontend game logic, animations, and interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Theme setting
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('pokerTheme') || 'dark';
    body.classList.add(`${savedTheme}-theme`);
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            if (body.classList.contains('dark-theme')) {
                body.classList.remove('dark-theme');
                body.classList.add('light-theme');
                localStorage.setItem('pokerTheme', 'light');
            } else {
                body.classList.remove('light-theme');
                body.classList.add('dark-theme');
                localStorage.setItem('pokerTheme', 'dark');
            }
        });
    }
    
    // Card management
    const cardSuits = {
        'h': '♥',
        'd': '♦',
        'c': '♣',
        's': '♠'
    };
    
    // Create and render a card
    function createCard(cardCode, faceUp = false) {
        const card = document.createElement('div');
        card.className = 'card' + (faceUp ? 'flipped' : '');
        
        const cardInner = document.createElement('div');
        cardInner.className = 'card-inner';
        
        const cardFront = document.createElement('div');
        cardFront.className = 'card-front';
        
        const cardBack = document.createElement('div');
        cardBack.className = 'card-back';
        
        // Only add card content if we have a valid card code
        if (cardCode) {
            const rank = cardCode.charAt(0);
            const suit = cardCode.charAt(1);
            
            const isRed = (suit === 'h' || suit === 'd');
            const suitSymbol = cardSuits[suit] || '';
            
            const topValue = document.createElement('div');
            topValue.className = `card-value ${isRed ? 'red' : 'black'}`;
            topValue.textContent = rank;
            
            const centerSuit = document.createElement('div');
            centerSuit.className = `card-suit ${isRed ? 'red' : 'black'}`;
            centerSuit.innerHTML = suitSymbol;
            
            const bottomValue = document.createElement('div');
            bottomValue.className = `card-value ${isRed ? 'red' : 'black'}`;
            bottomValue.textContent = rank;
            bottomValue.style.transform = 'rotate(180deg)';
            
            cardFront.appendChild(topValue);
            cardFront.appendChild(centerSuit);
            cardFront.appendChild(bottomValue);
        }
        
        cardInner.appendChild(cardFront);
        cardInner.appendChild(cardBack);
        card.appendChild(cardInner);
        
        card.dataset.cardCode = cardCode || '';
        
        return card;
    }
    
    // Flip a card
    function flipCard(cardElement, faceUp = true) {
        if (faceUp) {
            cardElement.classList.add('flipped');
        } else {
            cardElement.classList.remove('flipped');
        }
    }
    
    // Animation for dealing cards
    function dealCardAnimation(cardElement, targetElement, delay = 0) {
        cardElement.style.opacity = '0';
        targetElement.appendChild(cardElement);
        
        setTimeout(() => {
            cardElement.classList.add('deal-animation');
            cardElement.style.opacity = '1';
        }, delay);
        
        return new Promise(resolve => {
            setTimeout(() => {
                cardElement.classList.remove('deal-animation');
                resolve();
            }, delay + 500); // Animation duration
        });
    }
    
    // Chip management
    function createChip(value, color) {
        const chip = document.createElement('div');
        chip.className = `chip ${color}`;
        chip.textContent = value;
        chip.dataset.value = value;
        
        return chip;
    }
    
    // Create chip stack for betting
    function createChipStack(amount) {
        const chipStack = document.createElement('div');
        chipStack.className = 'chip-stack';
        
        // Determine chips to represent the amount
        let remainingAmount = amount;
        const chipValues = [
            {value: 5000, color: 'black'},
            {value: 1000, color: 'gold'},
            {value: 500, color: 'blue'},
            {value: 100, color: 'green'},
            {value: 25, color: 'red'}
        ];
        
        let displayedChips = 0;
        
        for (const chipType of chipValues) {
            if (remainingAmount >= chipType.value && displayedChips < 5) {
                const chip = createChip(chipType.value, chipType.color);
                chipStack.appendChild(chip);
                remainingAmount -= chipType.value;
                displayedChips++;
                
                // Don't show too many chips
                if (displayedChips >= 5) {
                    break;
                }
            }
        }
        
        // Add a chip counter if there's more
        if (remainingAmount > 0 || amount > 5000) {
            const amountDisplay = document.createElement('div');
            amountDisplay.className = 'chip-amount';
            amountDisplay.textContent = `$${amount}`;
            chipStack.appendChild(amountDisplay);
        }
        
        return chipStack;
    }
    
    // Poker hand rank display
    function getHandRankDescription(handRank) {
        switch(handRank) {
            case 'high_card':
                return 'High Card';
            case 'pair':
                return 'Pair';
            case 'two_pair':
                return 'Two Pair';
            case 'three_of_a_kind':
                return 'Three of a Kind';
            case 'straight':
                return 'Straight';
            case 'flush':
                return 'Flush';
            case 'full_house':
                return 'Full House';
            case 'four_of_a_kind':
                return 'Four of a Kind';
            case 'straight_flush':
                return 'Straight Flush';
            case 'royal_flush':
                return 'Royal Flush';
            default:
                return '';
        }
    }
    
    // Display hand rank
    function updateHandRank(handRankElement, rank) {
        if (handRankElement) {
            handRankElement.textContent = getHandRankDescription(rank);
            
            // Clear any existing classes
            handRankElement.className = 'hand-rank';
            
            // Add class based on hand strength
            const rankClasses = {
                'high_card': 'rank-high-card',
                'pair': 'rank-pair',
                'two_pair': 'rank-two-pair',
                'three_of_a_kind': 'rank-three-kind',
                'straight': 'rank-straight',
                'flush': 'rank-flush',
                'full_house': 'rank-full-house',
                'four_of_a_kind': 'rank-four-kind',
                'straight_flush': 'rank-straight-flush',
                'royal_flush': 'rank-royal-flush'
            };
            
            if (rankClasses[rank]) {
                handRankElement.classList.add(rankClasses[rank]);
            }
        }
    }
    
    // Action button controls
    function setupActionButtons(gameState) {
        const foldBtn = document.getElementById('fold-btn');
        const checkBtn = document.getElementById('check-btn');
        const callBtn = document.getElementById('call-btn');
        const raiseBtn = document.getElementById('raise-btn');
        const allInBtn = document.getElementById('all-in-btn');
        const raiseInput = document.getElementById('raise-amount');
        
        // Only enable buttons when it's player's turn
        if (gameState.currentPlayer === 'player') {
            // Enable all buttons first
            [foldBtn, checkBtn, callBtn, raiseBtn, allInBtn].forEach(btn => {
                if (btn) btn.disabled = false;
            });
            
            // Disable check if there's a bet to call
            if (checkBtn && gameState.canCheck === false) {
                checkBtn.disabled = true;
            }
            
            // Update call button text with amount
            if (callBtn) {
                callBtn.textContent = `Call $${gameState.callAmount}`;
                // Disable if can't call
                callBtn.disabled = gameState.callAmount <= 0;
            }
            
            // Set min/max for raise input
            if (raiseInput) {
                raiseInput.min = gameState.minRaise;
                raiseInput.max = gameState.playerChips;
                raiseInput.value = gameState.minRaise;
            }
        } else {
            // Disable all buttons when not player's turn
            [foldBtn, checkBtn, callBtn, raiseBtn, allInBtn].forEach(btn => {
                if (btn) btn.disabled = true;
            });
        }
    }
    
    // Server communication for game state
    function fetchGameState() {
        return fetch('/api/game/state')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch game state');
                }
                return response.json();
            })
            .then(gameState => {
                // Process the game state immediately when received
                if (gameState && gameState.currentPlayer !== 'player' && !gameState.handComplete) {
                    // If it's AI's turn and game is waiting for a response, handle it immediately
                    processAITurn(gameState);
                }
                return gameState;
            })
            .catch(error => {
                console.error('Error fetching game state:', error);
                return null;
            });
    }
    
    // Optimize AI decision processing to reduce delays
    function processAITurn(gameState) {
        if (gameState && gameState.aiDecisionNeeded) {
            // Remove artificial waiting time
            fetch('/api/game/ai-action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({})
            })
            .then(response => {
                if (response.ok) {
                    // Updated state will be fetched on next poll
                    console.log("AI decision processed");
                }
            })
            .catch(error => {
                console.error('Error processing AI action:', error);
            });
        }
    }
    
    // Take player action
    function takeAction(action, amount = 0) {
        const data = { action, amount };
        
        return fetch('/api/game/action', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to perform action');
            }
            return response.json();
        })
        .catch(error => {
            console.error('Error taking action:', error);
            return null;
        });
    }
    
    // Update the UI based on game state
    function updateUI(gameState) {
        if (!gameState) return;
        
        // Update pot
        const potElement = document.getElementById('pot-display');
        if (potElement) {
            potElement.textContent = `Pot: $${gameState.pot}`;
        }
        
        // Update player chips
        const playerChipsElement = document.getElementById('player-chips');
        if (playerChipsElement) {
            playerChipsElement.textContent = `$${gameState.playerChips}`;
        }
        
        // Update player cards
        const playerCardsElement = document.getElementById('player-cards');
        if (playerCardsElement && gameState.playerCards) {
            playerCardsElement.innerHTML = '';
            gameState.playerCards.forEach(cardCode => {
                const card = createCard(cardCode, true); // Player's cards are face up
                playerCardsElement.appendChild(card);
            });
        }
        
        // Update community cards
        const communityCardsElement = document.getElementById('community-cards');
        if (communityCardsElement && gameState.communityCards) {
            communityCardsElement.innerHTML = '';
            gameState.communityCards.forEach(cardCode => {
                const card = createCard(cardCode, true); // Community cards are face up
                communityCardsElement.appendChild(card);
            });
        }
        
        // Update opponents
        gameState.opponents.forEach((opponent, index) => {
            const opponentElement = document.getElementById(`opponent-${index + 1}`);
            if (opponentElement) {
                // Update opponent name and chips
                const nameElement = opponentElement.querySelector('.opponent-name');
                if (nameElement) {
                    nameElement.textContent = opponent.name;
                }
                
                const chipsElement = opponentElement.querySelector('.opponent-chips');
                if (chipsElement) {
                    chipsElement.textContent = `$${opponent.chips}`;
                }
                
                // Update opponent cards
                const cardsElement = opponentElement.querySelector('.opponent-cards');
                if (cardsElement) {
                    cardsElement.innerHTML = '';
                    opponent.cards.forEach(cardCode => {
                        // Only show face up if revealed
                        const card = createCard(cardCode, opponent.cardsRevealed);
                        cardsElement.appendChild(card);
                    });
                }
                
                // Show opponent's action
                const actionElement = opponentElement.querySelector('.opponent-action');
                if (actionElement) {
                    actionElement.textContent = opponent.lastAction || '';
                }
                
                // Highlight active opponent
                opponentElement.classList.toggle('active-player', opponent.isActive);
            }
        });
        
        // Highlight active player
        const playerAreaElement = document.getElementById('player-area');
        if (playerAreaElement) {
            playerAreaElement.classList.toggle('active-player', gameState.currentPlayer === 'player');
        }
        
        // Update player's hand rank if available
        if (gameState.playerHandRank) {
            const handRankElement = document.getElementById('player-hand-rank');
            if (handRankElement) {
                updateHandRank(handRankElement, gameState.playerHandRank);
            }
        }
        
        // Update action buttons based on game state
        setupActionButtons(gameState);
        
        // Update betting round status
        const roundStatusElement = document.getElementById('round-status');
        if (roundStatusElement) {
            roundStatusElement.textContent = gameState.bettingRound || '';
        }
        
        // Display game messages
        if (gameState.message) {
            showGameMessage(gameState.message);
        }
        
        // Handle end of hand
        if (gameState.handComplete) {
            handleHandComplete(gameState);
        }
    }
    
    // Display temporary game messages
    function showGameMessage(message) {
        const messageElement = document.getElementById('game-message');
        if (messageElement) {
            messageElement.textContent = message;
            messageElement.style.opacity = '1';
            
            // Hide after a few seconds
            setTimeout(() => {
                messageElement.style.opacity = '0';
            }, 3000);
        }
    }
    
    // Handle end of hand
    function handleHandComplete(gameState) {
        // Only reveal opponent cards at showdown
        if (gameState.current_state === 'Showdown') {
            gameState.opponents.forEach((opponent, index) => {
                const opponentElement = document.getElementById(`opponent-${index + 1}`);
                if (opponentElement) {
                    const cardsElement = opponentElement.querySelector('.opponent-cards');
                    if (cardsElement) {
                        const cards = cardsElement.querySelectorAll('.card');
                        cards.forEach(card => flipCard(card, true));
                    }
                }
            });
        }
        
        // Highlight winner with animation
        if (gameState.winner) {
            let winnerElement;
            if (gameState.winner.isPlayer) {
                winnerElement = document.getElementById('player-area');
            } else if (typeof gameState.winner.index === 'number') {
                winnerElement = document.getElementById(`opponent-${gameState.winner.index}`);
            }
            
            if (winnerElement) {
                winnerElement.classList.add('win-animation');
                
                // Remove the animation after a few seconds
                setTimeout(() => {
                    winnerElement.classList.remove('win-animation');
                }, 3000);
            }
        }
        
        // Show next hand button
        const nextHandButton = document.getElementById('next-hand-btn');
        if (nextHandButton) {
            nextHandButton.style.display = 'block';
        }
    }
    
    // Start a new hand
    function startNewHand() {
        return fetch('/api/game/new-hand', {
            method: 'POST'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to start new hand');
            }
            return response.json();
        })
        .catch(error => {
            console.error('Error starting new hand:', error);
            return null;
        });
    }
    
    // Setup the game
    function initializeGame() {
        // Fetch initial game state
        fetchGameState().then(gameState => {
            if (gameState) {
                updateUI(gameState);
            }
        });
        
        // Setup action button event listeners
        const foldBtn = document.getElementById('fold-btn');
        if (foldBtn) {
            foldBtn.addEventListener('click', () => {
                takeAction('fold').then(gameState => {
                    if (gameState) {
                        updateUI(gameState);
                    }
                });
            });
        }
        
        const checkBtn = document.getElementById('check-btn');
        if (checkBtn) {
            checkBtn.addEventListener('click', () => {
                takeAction('check').then(gameState => {
                    if (gameState) {
                        updateUI(gameState);
                    }
                });
            });
        }
        
        const callBtn = document.getElementById('call-btn');
        if (callBtn) {
            callBtn.addEventListener('click', () => {
                takeAction('call').then(gameState => {
                    if (gameState) {
                        updateUI(gameState);
                    }
                });
            });
        }
        
        const raiseBtn = document.getElementById('raise-btn');
        const raiseInput = document.getElementById('raise-amount');
        if (raiseBtn && raiseInput) {
            raiseBtn.addEventListener('click', () => {
                const amount = parseInt(raiseInput.value);
                takeAction('raise', amount).then(gameState => {
                    if (gameState) {
                        updateUI(gameState);
                    }
                });
            });
        }
        
        const allInBtn = document.getElementById('all-in-btn');
        if (allInBtn) {
            allInBtn.addEventListener('click', () => {
                takeAction('all-in').then(gameState => {
                    if (gameState) {
                        updateUI(gameState);
                    }
                });
            });
        }
        
        const nextHandBtn = document.getElementById('next-hand-btn');
        if (nextHandBtn) {
            nextHandBtn.addEventListener('click', () => {
                nextHandBtn.style.display = 'none';
                startNewHand().then(gameState => {
                    if (gameState) {
                        updateUI(gameState);
                    }
                });
            });
        }
        
        // Poll for game state updates
        let gameStatePoller = setInterval(() => {
            fetchGameState().then(gameState => {
                if (gameState) {
                    updateUI(gameState);
                }
            });
        }, 2000); // Poll every 2 seconds
        
        // Clean up poller when leaving the page
        window.addEventListener('beforeunload', () => {
            clearInterval(gameStatePoller);
        });
    }
    
    // Initialize on page load
    initializeGame();
});