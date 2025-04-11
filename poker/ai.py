"""
AI player module for the poker game.
Contains AI player implementations with different strategies and difficulty levels.
"""

import random
from typing import Dict, Tuple, List, Any, Optional
from enum import Enum

from .player import Player
from .cards import Card, Hand, HandRank, evaluate_hand

class AIPersonality(Enum):
    """Different AI player personalities."""
    CONSERVATIVE = "Conservative"  # Plays tight, folds often
    AGGRESSIVE = "Aggressive"      # Raises frequently, bluffs more
    BALANCED = "Balanced"          # Mix of styles
    LOOSE = "Loose"                # Plays many hands, calls often
    MANIAC = "Maniac"              # Very aggressive, raises a lot
    TIGHT = "Tight"                # Only plays premium hands

class AISkillLevel(Enum):
    """Skill levels for AI players."""
    ROOKIE = "Rookie"        # Makes basic mistakes, easy to beat
    AMATEUR = "Amateur"      # Some strategy, but still makes mistakes
    INTERMEDIATE = "Intermediate"  # Decent strategy
    ADVANCED = "Advanced"    # Good strategy, harder to beat
    EXPERT = "Expert"        # Very strong, uses advanced concepts

class AIPlayer(Player):
    """
    AI player for the poker game with configurable personality traits and skill level.
    """
    
    def __init__(self, name: str, chips: int = 1000, 
                 personality: AIPersonality = AIPersonality.BALANCED,
                 skill_level: AISkillLevel = AISkillLevel.INTERMEDIATE):
        super().__init__(name, chips)
        self.personality = personality
        self.skill_level = skill_level
        
        # Personality traits (0-100 scale)
        # These values are based on the personality but can be adjusted
        if personality == AIPersonality.CONSERVATIVE:
            self.aggression = 20
            self.bluff_tendency = 15
            self.call_threshold = 75
            self.fold_threshold = 40
        elif personality == AIPersonality.AGGRESSIVE:
            self.aggression = 80
            self.bluff_tendency = 60
            self.call_threshold = 30
            self.fold_threshold = 20
        elif personality == AIPersonality.BALANCED:
            self.aggression = 50
            self.bluff_tendency = 40
            self.call_threshold = 50
            self.fold_threshold = 30
        elif personality == AIPersonality.LOOSE:
            self.aggression = 60
            self.bluff_tendency = 50
            self.call_threshold = 25
            self.fold_threshold = 15
        elif personality == AIPersonality.MANIAC:
            self.aggression = 90
            self.bluff_tendency = 80
            self.call_threshold = 20
            self.fold_threshold = 10
        elif personality == AIPersonality.TIGHT:
            self.aggression = 30
            self.bluff_tendency = 20
            self.call_threshold = 70
            self.fold_threshold = 50
        
        # Adjust traits based on skill level
        self._adjust_for_skill_level()
        
        # Game memory
        self.observed_actions = []
        self.pot_history = []
        self.hand_strength_history = []
        self.hands_played = 0
    
    def _adjust_for_skill_level(self):
        """
        Adjusts AI traits based on skill level.
        Lower skill levels introduce more randomness and mistakes.
        """
        if self.skill_level == AISkillLevel.ROOKIE:
            # Very inconsistent play with large variance
            self.aggression = self._randomize_trait(self.aggression, 30)
            self.bluff_tendency = self._randomize_trait(self.bluff_tendency, 40)
            self.call_threshold = self._randomize_trait(self.call_threshold, 30)
            self.fold_threshold = self._randomize_trait(self.fold_threshold, 30)
        
        elif self.skill_level == AISkillLevel.AMATEUR:
            # Still inconsistent but less random
            self.aggression = self._randomize_trait(self.aggression, 20)
            self.bluff_tendency = self._randomize_trait(self.bluff_tendency, 25)
            self.call_threshold = self._randomize_trait(self.call_threshold, 20)
            self.fold_threshold = self._randomize_trait(self.fold_threshold, 20)
        
        elif self.skill_level == AISkillLevel.INTERMEDIATE:
            # More consistent play with some variance
            self.aggression = self._randomize_trait(self.aggression, 10)
            self.bluff_tendency = self._randomize_trait(self.bluff_tendency, 15)
            self.call_threshold = self._randomize_trait(self.call_threshold, 10)
            self.fold_threshold = self._randomize_trait(self.fold_threshold, 10)
        
        elif self.skill_level == AISkillLevel.ADVANCED:
            # Very small variance, more consistent
            self.aggression = self._randomize_trait(self.aggression, 5)
            self.bluff_tendency = self._randomize_trait(self.bluff_tendency, 10)
            self.call_threshold = self._randomize_trait(self.call_threshold, 5)
            self.fold_threshold = self._randomize_trait(self.fold_threshold, 5)
        
        # Expert level has no randomization - uses the base personality traits consistently
    
    def _randomize_trait(self, base_value: int, variance: int) -> int:
        """
        Randomize a trait value within variance bounds.
        
        Args:
            base_value: The base trait value
            variance: How much the value can vary
            
        Returns:
            Randomized value between max(0, base_value - variance) and min(100, base_value + variance)
        """
        lower_bound = max(0, base_value - variance)
        upper_bound = min(100, base_value + variance)
        return random.randint(lower_bound, upper_bound)
    
    def evaluate_hand_strength(self, community_cards: List[Card]) -> float:
        """
        Evaluates the current hand strength based on hole cards and community cards.
        
        Args:
            community_cards: The community cards on the table
            
        Returns:
            A score between 0-1 representing the relative hand strength
        """
        if not self.hand.cards:
            return 0
        
        # Combine hole cards and community cards
        all_cards = self.hand.cards + community_cards
        
        # If we don't have at least 5 cards (2 hole + 3 community), use pre-flop evaluation
        if len(all_cards) < 5:
            return self._preflop_strength()
        
        # Evaluate the current hand
        hand_result = evaluate_hand(all_cards)
        hand_rank = hand_result[0]
        
        # Base strength on hand rank
        strength = hand_rank.value / 8.0  # HandRank.STRAIGHT_FLUSH.value is 8
        
        # Adjust based on kickers or specific hand characteristics
        if len(community_cards) >= 3:
            # Consider how well our hole cards contribute to the hand
            hole_card_contribution = self._evaluate_hole_contribution(community_cards)
            strength = (strength * 0.8) + (hole_card_contribution * 0.2)
        
        return strength
    
    def _preflop_strength(self) -> float:
        """
        Evaluates the preflop hand strength.
        
        Returns:
            A score between 0-1 representing the preflop hand strength
        """
        if len(self.hand.cards) != 2:
            return 0
        
        card1, card2 = self.hand.cards
        
        # Check if pair
        if card1.rank == card2.rank:
            # Pairs are strong
            # A-A is strongest (value 14), 2-2 is weakest (value 2)
            return 0.5 + ((card1.rank.value - 2) / 24)  # 0.5 to 1.0 range for pairs
        
        # Check if suited
        suited = card1.suit == card2.suit
        
        # Get ranks in high-low order
        high_rank, low_rank = (card1.rank.value, card2.rank.value) if card1.rank.value > card2.rank.value else (card2.rank.value, card1.rank.value)
        
        # Calculate gap between ranks
        gap = high_rank - low_rank - 1
        
        # Base value from high card
        base_value = (high_rank - 2) / 24  # 0 to 0.5 range from high card
        
        # Adjust for connectedness and suited-ness
        if gap == 0:  # Connected
            connectedness = 0.2
        elif gap == 1:  # One-gapper
            connectedness = 0.15
        elif gap == 2:  # Two-gapper
            connectedness = 0.1
        else:
            connectedness = 0
        
        # Suited cards bonus
        suited_bonus = 0.1 if suited else 0
        
        # Broadway bonus (JQK)
        broadway_bonus = 0.1 if low_rank >= 11 else 0
        
        # Calculate final preflop strength
        return base_value + connectedness + suited_bonus + broadway_bonus
    
    def _evaluate_hole_contribution(self, community_cards: List[Card]) -> float:
        """
        Evaluates how much our hole cards contribute to the overall hand.
        
        Args:
            community_cards: The community cards on the table
            
        Returns:
            A score between 0-1 representing how much our hole cards contribute
        """
        # Evaluate the hand with just community cards
        community_hand_result = evaluate_hand(community_cards)
        community_hand_rank = community_hand_result[0]
        
        # Evaluate with hole cards too
        all_cards = self.hand.cards + community_cards
        full_hand_result = evaluate_hand(all_cards)
        full_hand_rank = full_hand_result[0]
        
        # If our hole cards improve the hand rank
        if full_hand_rank.value > community_hand_rank.value:
            return 1.0
        
        # If we're using at least one hole card in the best hand
        # This is a simplification, in a full implementation we'd check if our hole cards
        # are part of the best 5-card hand
        hole_ranks = {card.rank for card in self.hand.cards}
        
        # Check if we have any matching ranks with the community cards
        for card in community_cards:
            if card.rank in hole_ranks:
                return 0.5
        
        # Our hole cards don't seem to contribute much
        return 0.2
    
    def calculate_pot_odds(self, to_call: int, pot_size: int) -> float:
        """
        Calculate the pot odds for a decision.
        
        Args:
            to_call: Amount needed to call
            pot_size: Current pot size
            
        Returns:
            Pot odds as a decimal (e.g., 0.25 means 4:1 odds)
        """
        if to_call == 0:
            return 1.0  # No cost to call
        return pot_size / (pot_size + to_call)
    
    def should_bluff(self, game_state: Dict[str, Any]) -> bool:
        """
        Determine if the AI should bluff based on personality and game state.
        
        Args:
            game_state: Current state of the game
            
        Returns:
            True if the AI should bluff, False otherwise
        """
        # Base bluff chance on personality
        bluff_chance = self.bluff_tendency / 100.0
        
        # Adjust based on position, betting round, etc.
        if game_state.get('betting_round') == 'Pre-Flop':
            bluff_chance *= 0.5  # Less likely to bluff pre-flop
        
        # More likely to bluff late in the hand
        if game_state.get('betting_round') == 'River':
            bluff_chance *= 1.5
        
        # More likely to bluff with fewer players in the hand
        active_players = game_state.get('active_players', 2)
        if active_players <= 2:
            bluff_chance *= 1.5
        
        # Less likely to bluff if many chips needed
        current_bet = game_state.get('current_bet', 0)
        relative_bet_size = current_bet / self.chips if self.chips > 0 else 1
        bluff_chance *= (1 - (relative_bet_size * 0.5))
        
        # Random chance based on adjusted bluff probability
        return random.random() < bluff_chance
    
    def make_decision(self, game_state: Dict[str, Any]) -> Tuple[str, int]:
        """
        Make a poker decision based on current game state and AI personality.
        
        Args:
            game_state: Current state of the game (pot, current bet, community cards, etc.)
            
        Returns:
            Tuple of (action, amount) where action is 'fold', 'check', 'call', 'raise', or 'all_in'
        """
        # Extract relevant information
        community_cards = game_state.get('community_cards', [])
        current_bet = game_state.get('current_bet', 0)
        pot = game_state.get('pot', 0)
        min_raise = game_state.get('min_raise', 10)
        
        # Calculate how much we need to call
        to_call = current_bet - self.current_bet
        
        # Evaluate our hand strength
        hand_strength = self.evaluate_hand_strength(community_cards)
        
        # Store in history for learning
        self.hand_strength_history.append(hand_strength)
        
        # Calculate pot odds
        pot_odds = self.calculate_pot_odds(to_call, pot)
        
        # Check if we can check (no bet to call)
        if to_call == 0:
            # Decision between check and raise
            if hand_strength > (self.aggression / 200):  # Higher aggression means more raising
                # Raise amount based on hand strength and aggression
                raise_amount = int(min_raise + (self.aggression / 100) * min_raise * 2 * hand_strength)
                
                # Cap the raise to what we can afford
                raise_amount = min(raise_amount, self.chips)
                
                # All-in with very strong hands
                if hand_strength > 0.85 and self.aggression > 60:
                    return 'all_in', self.chips
                
                return 'raise', raise_amount
            else:
                return 'check', 0
        
        # If facing a bet, decide whether to fold, call, or raise
        # Compare hand strength to pot odds, adjusted by personality
        if hand_strength > pot_odds or self.should_bluff(game_state):
            # Our hand strength justifies a call, or we're bluffing
            
            # Strong hand or high aggression might lead to a raise
            if hand_strength > (self.fold_threshold / 100) or (random.random() < (self.aggression / 150)):
                # Raise with strong hands or occasionally as a bluff
                if hand_strength > 0.7 or (self.should_bluff(game_state) and random.random() < (self.aggression / 200)):
                    # Calculate raise amount
                    raise_percent = 0.1 + (hand_strength * 0.5) + (random.random() * 0.2)
                    raise_amount = int(current_bet + (min_raise * (1 + raise_percent)))
                    
                    # Cap the raise to what we can afford
                    raise_amount = min(raise_amount, self.chips)
                    
                    # All-in with very strong hands
                    if hand_strength > 0.85 and self.aggression > 60:
                        return 'all_in', self.chips
                    
                    return 'raise', raise_amount
                else:
                    # Just call
                    return 'call', to_call
            else:
                # Just call
                return 'call', to_call
        else:
            # Hand not strong enough, fold unless we're feeling lucky
            if random.random() < (self.bluff_tendency / 150):
                return 'call', to_call
            else:
                return 'fold', 0
    
    def update_after_hand(self, won: bool, final_pot: int, shown_cards: Dict[str, List[Card]]):
        """
        Update AI learning after a hand is complete.
        
        Args:
            won: Whether the AI won the hand
            final_pot: The final pot size
            shown_cards: Cards shown by players who went to showdown
        """
        self.hands_played += 1
        
        # Record pot size
        self.pot_history.append(final_pot)
        
        # Simple learning logic - could be expanded in a real implementation
        if won:
            # If we won, slightly increase aggression and bluff tendency
            self.aggression = min(100, self.aggression + 2)
            self.bluff_tendency = min(100, self.bluff_tendency + 1)
        else:
            # If we lost, slightly decrease and become more cautious
            self.aggression = max(0, self.aggression - 1)
            self.bluff_tendency = max(0, self.bluff_tendency - 2)
        
        # Occasionally randomize traits to avoid getting stuck in patterns
        if self.hands_played % 10 == 0:
            self._adjust_for_skill_level()