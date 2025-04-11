class Player:
    """Represents a poker player"""
    
    def __init__(self, name, chips=1000):
        self.name = name
        self.chips = chips
        self.hand = []
        self.is_active = True
        self.current_bet = 0
        self.is_all_in = False
        self.last_action = None
        self.folded = False
        self.revealed = False
    
    def reset_for_hand(self):
        """Reset player state for a new hand"""
        self.hand = []
        self.is_active = True
        self.current_bet = 0
        self.is_all_in = False
        self.last_action = None
        self.folded = False
        self.revealed = False
    
    def add_cards(self, cards):
        """Add cards to player's hand"""
        self.hand.extend(cards)
    
    def place_bet(self, amount):
        """Place a bet of a specific amount"""
        if amount > self.chips:
            amount = self.chips
            self.is_all_in = True
            
        self.chips -= amount
        self.current_bet += amount
        return amount
    
    def fold(self):
        """Fold the hand"""
        self.is_active = False
        self.folded = True
        self.last_action = "Fold"
    
    def check(self):
        """Check (bet nothing)"""
        self.last_action = "Check"
    
    def call(self, call_amount):
        """Call a bet"""
        amount_to_call = call_amount - self.current_bet
        bet_amount = self.place_bet(amount_to_call)
        self.last_action = f"Call ${bet_amount}"
        return bet_amount
    
    def raise_bet(self, raise_amount):
        """Raise the bet"""
        bet_amount = self.place_bet(raise_amount)
        self.last_action = f"Raise ${bet_amount}"
        return bet_amount
    
    def all_in(self):
        """Go all-in"""
        bet_amount = self.place_bet(self.chips)
        self.last_action = f"All-In ${bet_amount}"
        return bet_amount
    
    def collect_winnings(self, amount):
        """Collect winnings from the pot"""
        self.chips += amount
    
    def reveal_cards(self):
        """Reveal the player's cards"""
        self.revealed = True