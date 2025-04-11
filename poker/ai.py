import random
from typing import List, Optional
from .player import Player
from .cards import Card, evaluate_hand, HandRank

class AIPlayer(Player):
    """
    AI poker player with different playing styles:
    - Conservative: Folds often, only plays strong hands
    - Balanced: Plays a mix of hands with some bluffing
    - Aggressive: Plays many hands and bluffs frequently
    """
    
    STYLES = ["conservative", "balanced", "aggressive"]
    
    def __init__(self, name: str, bankroll: int = 1000, style: str = "balanced"):
        super().__init__(name, bankroll)
        
        if style not in self.STYLES:
            raise ValueError(f"Invalid AI style. Must be one of: {', '.join(self.STYLES)}")
        
        self.style = style
        self.hand_strength = 0  # 0-10 scale, set when evaluating
    
    def evaluate_hand_strength(self, community_cards: List[Card] = None) -> float:
        """
        Evaluate the strength of the current hand on a scale of 0-10.
        Considers community cards if available.
        """
        # If no cards yet, use pre-flop evaluation based on hole cards
        if not community_cards:
            # Simple pre-flop evaluation
            card1, card2 = self.hand.cards
            
            # Check for pairs
            if card1.rank == card2.rank:
                # Pair value from 2-14, scale to 5-9 range
                pair_value = 5 + (card1.value - 2) * 4/12
                self.hand_strength = min(9, pair_value)
                return self.hand_strength
            
            # Check for high cards
            high_card = max(card1.value, card2.value)
            low_card = min(card1.value, card2.value)
            
            # Calculate gap between cards
            gap = high_card - low_card
            
            # Suited cards bonus
            suited_bonus = 1 if card1.suit == card2.suit else 0
            
            # Connectors bonus (cards in sequence)
            connector_bonus = 1 if gap == 1 else 0.5 if gap == 2 else 0
            
            # Base calculation - higher cards are better
            base_strength = (high_card / 14) * 5  # Scale to 0-5 range
            
            # Add bonuses
            self.hand_strength = min(10, base_strength + suited_bonus + connector_bonus)
            
            # Adjust for specific powerful starting hands
            if (card1.rank == 'A' and card2.rank == 'K' and card1.suit == card2.suit):
                self.hand_strength = 9  # AK suited
            elif (card1.rank == 'A' and card2.rank == 'K'):
                self.hand_strength = 8  # AK offsuit
            
            return self.hand_strength
        
        # Post-flop evaluation
        else:
            all_cards = self.hand.cards + community_cards
            
            # Evaluate the hand
            hand_rank, kickers = evaluate_hand(all_cards)
            
            # Map hand ranks to strength scale
            rank_strength = {
                HandRank.HIGH_CARD: 2,
                HandRank.PAIR: 3,
                HandRank.TWO_PAIR: 5,
                HandRank.THREE_OF_A_KIND: 6,
                HandRank.STRAIGHT: 7,
                HandRank.FLUSH: 8,
                HandRank.FULL_HOUSE: 9,
                HandRank.FOUR_OF_A_KIND: 9.5,
                HandRank.STRAIGHT_FLUSH: 9.8,
                HandRank.ROYAL_FLUSH: 10
            }
            
            # Add small adjustments based on kickers
            strength = rank_strength[hand_rank]
            
            # For pairs and such, consider the value of the cards
            if hand_rank in [HandRank.PAIR, HandRank.TWO_PAIR, HandRank.THREE_OF_A_KIND]:
                # Adjust by up to 0.9 based on the rank of the pair/trips
                kicker_adjustment = min(0.9, (kickers[0] - 2) / 12)
                strength += kicker_adjustment
            
            self.hand_strength = strength
            return self.hand_strength
    
    def make_decision(self, game_state: dict) -> tuple:
        """
        AI makes a poker decision based on the current game state.
        
        Returns:
            tuple: (action, amount) where action is one of:
                  'fold', 'check', 'call', 'raise', 'all_in'
        """
        # Extract game state
        current_bet = game_state['current_bet']
        pot = game_state['pot']
        community_cards = game_state['community_cards']
        min_raise = game_state.get('min_raise', current_bet * 2)
        
        # Calculate how much more to call
        to_call = current_bet - self.current_bet
        
        # Evaluate hand strength
        self.evaluate_hand_strength(community_cards)
        
        # If player doesn't have enough chips to call
        if to_call > self.bankroll:
            # Either fold or go all-in
            if self.decide_all_in():
                return ('all_in', 0)
            else:
                return ('fold', 0)
        
        # Adjust thresholds based on AI style
        if self.style == "conservative":
            fold_threshold = 3.5
            call_threshold = 4.5
            raise_threshold = 6.0
            reraise_threshold = 7.5
            allin_threshold = 8.5
            bluff_chance = 0.05
        elif self.style == "balanced":
            fold_threshold = 2.5
            call_threshold = 3.5
            raise_threshold = 5.0
            reraise_threshold = 7.0
            allin_threshold = 8.0
            bluff_chance = 0.15
        else:  # aggressive
            fold_threshold = 1.5
            call_threshold = 2.5
            raise_threshold = 4.0
            reraise_threshold = 6.0
            allin_threshold = 7.5
            bluff_chance = 0.25
        
        # Calculate pot odds ratio for calling
        pot_odds = to_call / (pot + to_call) if to_call > 0 else 0
        
        # Decision making
        if random.random() < bluff_chance:
            # Random bluff
            if to_call == 0:
                # No bet yet, can check or raise
                if random.random() < 0.7:
                    # Bluff with a raise
                    raise_amount = min(min_raise, self.bankroll)
                    return ('raise', raise_amount)
                else:
                    return ('check', 0)
            else:
                # Call or raise as a bluff
                if random.random() < 0.4 and self.bankroll > min_raise:
                    raise_amount = random.randint(min_raise, min(self.bankroll, pot // 2))
                    return ('raise', raise_amount)
                else:
                    return ('call', to_call)
        
        # Regular decision based on hand strength
        if to_call == 0:
            # No one has bet yet
            if self.hand_strength > raise_threshold:
                # Strong hand, raise
                raise_size = calculate_raise_size(self.hand_strength, pot, self.bankroll, self.style)
                return ('raise', raise_size)
            elif self.hand_strength > call_threshold:
                # Decent hand, check
                return ('check', 0)
            else:
                # Weak hand, check and hope to see a cheap flop
                return ('check', 0)
        else:
            # Facing a bet
            if self.hand_strength > allin_threshold and self.bankroll < pot * 3:
                # Very strong hand and relatively small stack, go all-in
                return ('all_in', 0)
            elif self.hand_strength > reraise_threshold:
                # Strong enough to reraise
                raise_size = calculate_raise_size(self.hand_strength, pot, self.bankroll, self.style)
                return ('raise', raise_size)
            elif self.hand_strength > call_threshold:
                # Decent hand worth a call
                return ('call', to_call)
            else:
                # Weak hand, fold
                return ('fold', 0)
    
    def decide_all_in(self) -> bool:
        """Decide whether to go all-in when can't afford to call."""
        # Base decision on hand strength and style
        if self.style == "conservative":
            return self.hand_strength >= 7
        elif self.style == "balanced":
            return self.hand_strength >= 6
        else:  # aggressive
            return self.hand_strength >= 5 or random.random() < 0.2

def calculate_raise_size(hand_strength: float, pot: int, bankroll: int, style: str) -> int:
    """Calculate an appropriate raise size based on hand strength and style."""
    
    # Base calculation on hand strength (0-10 scale)
    if hand_strength > 8.5:  # Monster
        pot_percent = random.uniform(1.0, 1.5)  # 100-150% of pot
    elif hand_strength > 7:  # Very strong
        pot_percent = random.uniform(0.7, 1.0)  # 70-100% of pot
    elif hand_strength > 5:  # Strong
        pot_percent = random.uniform(0.5, 0.8)  # 50-80% of pot
    else:  # Decent
        pot_percent = random.uniform(0.3, 0.6)  # 30-60% of pot
    
    # Adjust based on style
    if style == "conservative":
        pot_percent *= 0.8
    elif style == "aggressive":
        pot_percent *= 1.2
    
    # Calculate raise amount
    raise_amount = int(pot * pot_percent)
    
    # Ensure minimum raise and maximum bankroll
    raise_amount = max(1, min(raise_amount, bankroll))
    
    return raise_amount