import random
from .player import Player
from .cards import evaluate_hand

class AIPlayer(Player):
    """AI Poker Player"""
    
    def __init__(self, name, chips=1000, difficulty="Medium"):
        super().__init__(name, chips)
        self.difficulty = difficulty
        self.aggression = self._set_aggression()
        self.bluff_factor = self._set_bluff_factor()
    
    def _set_aggression(self):
        """Set aggression level based on difficulty"""
        if self.difficulty == "Easy":
            return random.uniform(0.1, 0.3)
        elif self.difficulty == "Medium":
            return random.uniform(0.3, 0.6)
        elif self.difficulty == "Hard":
            return random.uniform(0.6, 0.8)
        else:  # Expert
            return random.uniform(0.7, 0.9)
    
    def _set_bluff_factor(self):
        """Set bluff factor based on difficulty"""
        if self.difficulty == "Easy":
            return random.uniform(0.05, 0.15)
        elif self.difficulty == "Medium":
            return random.uniform(0.15, 0.25)
        elif self.difficulty == "Hard":
            return random.uniform(0.25, 0.40)
        else:  # Expert
            return random.uniform(0.30, 0.50)
    
    def decide_action(self, game_state):
        """Decide AI action based on game state and difficulty"""
        # Extract relevant information from game state
        pot = game_state.get('pot', 0)
        current_bet = game_state.get('current_bet', 0)
        community_cards = game_state.get('community_cards', [])
        
        # Calculate how much to call
        to_call = current_bet - self.current_bet
        
        # Calculate pot odds
        pot_odds = to_call / (pot + to_call) if to_call > 0 else 0
        
        # Evaluate hand strength (0 to 1)
        hand_strength = self._evaluate_hand_strength(community_cards)
        
        # Add some randomness based on bluff factor
        if random.random() < self.bluff_factor:
            hand_strength = max(0.7, hand_strength)  # Occasionally pretend to have a good hand
        
        # Decision logic
        if to_call == 0:  # Can check
            # Sometimes raise with a good hand
            if hand_strength > 0.7 and random.random() < self.aggression:
                # Raise proportional to hand strength and pot
                raise_amount = int(min(self.chips, pot * hand_strength * random.uniform(0.1, 0.5)))
                return "raise", max(10, raise_amount)
            else:
                return "check", 0
        else:  # There's a bet to call
            # Fold with weak hands
            if hand_strength < pot_odds * (1 - self.aggression):
                return "fold", 0
                
            # Call with medium hands
            elif hand_strength < 0.6:
                if to_call > self.chips * 0.3 and hand_strength < 0.4:
                    return "fold", 0  # Too expensive for a mediocre hand
                return "call", 0
                
            # Raise with strong hands
            else:
                # All-in with very strong hands
                if hand_strength > 0.85 and random.random() < self.aggression:
                    return "all_in", 0
                    
                # Otherwise raise
                raise_factor = hand_strength * self.aggression * random.uniform(0.5, 1.5)
                raise_amount = int(min(self.chips, (pot + to_call) * raise_factor))
                
                # Ensure minimum raise
                if raise_amount <= to_call:
                    return "call", 0
                
                return "raise", raise_amount
    
    def _evaluate_hand_strength(self, community_cards):
        """Evaluate the strength of the current hand (0 to 1)"""
        # If no community cards, evaluate based on hole cards
        if not community_cards:
            # Evaluate pocket pairs
            if len(self.hand) == 2 and self.hand[0].rank == self.hand[1].rank:
                rank_value = self.hand[0].rank_value
                # Higher pairs are stronger
                return 0.5 + (rank_value / 25.0)
                
            # Evaluate connected cards (straight potential)
            elif len(self.hand) == 2:
                rank_diff = abs(self.hand[0].rank_value - self.hand[1].rank_value)
                if rank_diff <= 1:  # Connected
                    high_card = max(self.hand[0].rank_value, self.hand[1].rank_value)
                    return 0.3 + (high_card / 40.0)
                    
                # Evaluate suited cards (flush potential)
                if self.hand[0].suit == self.hand[1].suit:
                    high_card = max(self.hand[0].rank_value, self.hand[1].rank_value)
                    return 0.25 + (high_card / 50.0)
                
                # High cards
                high_card = max(self.hand[0].rank_value, self.hand[1].rank_value)
                if high_card >= 10:  # 10, J, Q, K, A
                    return 0.2 + ((high_card - 10) / 25.0)
            
            # Low, unconnected, unsuited cards
            return 0.1
        
        # With community cards, do a proper evaluation
        all_cards = self.hand + community_cards
        
        # Get the numerical rank value (0-9)
        hand_value = evaluate_hand(all_cards)
        hand_rank = hand_value[0]
        
        # Scale from 0 to 1 based on hand rank
        # High Card (0) → 0.1 to 0.2
        # Pair (1) → 0.2 to 0.3
        # Two Pair (2) → 0.3 to 0.4
        # etc.
        base_strength = min(0.9, (hand_rank + 1) / 10.0)
        
        # Add a small factor based on kickers
        kicker_factor = sum(hand_value[1][:3]) / 100.0 if hand_value[1] else 0
        
        return base_strength + kicker_factor