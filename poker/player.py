from typing import List, Optional
from .cards import Hand

class Player:
    """A poker player with chips, cards, and action tracking."""
    
    def __init__(self, name: str, bankroll: int = 1000):
        self.name = name
        self.bankroll = bankroll
        self.hand = Hand()
        self.current_bet = 0
        self.folded = False
        self.is_all_in = False
        self.last_action = None
    
    def clear_hand(self):
        """Reset the player's hand for a new round."""
        self.hand.clear()
        self.current_bet = 0
        self.folded = False
        self.is_all_in = False
        self.last_action = None
    
    def place_bet(self, amount: int) -> int:
        """Place a bet for the player, returns the actual amount bet."""
        if amount <= 0:
            return 0
        
        # Cap the bet at the player's bankroll
        actual_bet = min(amount, self.bankroll)
        self.bankroll -= actual_bet
        self.current_bet += actual_bet
        
        # Check if player is all in
        if self.bankroll == 0:
            self.is_all_in = True
        
        return actual_bet
    
    def collect_winnings(self, amount: int):
        """Add winnings to the player's bankroll."""
        self.bankroll += amount
    
    def can_bet(self, amount: int) -> bool:
        """Check if the player can make a bet of the specified amount."""
        return self.bankroll >= amount and not self.folded
    
    def fold(self):
        """The player folds their hand."""
        self.folded = True
        self.last_action = "Fold"
    
    def check(self):
        """The player checks (takes no action)."""
        self.last_action = "Check"
    
    def call(self, amount: int) -> int:
        """The player calls the current bet."""
        bet_amount = amount - self.current_bet
        actual_bet = self.place_bet(bet_amount)
        self.last_action = "Call"
        return actual_bet
    
    def raise_bet(self, amount: int) -> int:
        """The player raises the bet to the specified amount."""
        bet_amount = amount - self.current_bet
        actual_bet = self.place_bet(bet_amount)
        self.last_action = f"Raise to {amount}"
        return actual_bet
    
    def all_in(self) -> int:
        """The player goes all-in."""
        actual_bet = self.place_bet(self.bankroll)
        self.is_all_in = True
        self.last_action = "All In"
        return actual_bet
    
    def __str__(self):
        return f"{self.name} (${self.bankroll})"
    
    def __repr__(self):
        return self.__str__()