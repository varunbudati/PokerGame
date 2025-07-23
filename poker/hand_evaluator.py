import logging
from collections import Counter
import itertools
from typing import List, Tuple, Dict, Any

class HandEvaluator:
    """
    Advanced poker hand evaluation with detailed score breakdowns and descriptive hand names.
    """
    
    HAND_TYPES = [
        "High Card", "One Pair", "Two Pair", "Three of a Kind", 
        "Straight", "Flush", "Full House", "Four of a Kind", 
        "Straight Flush", "Royal Flush"
    ]
    
    CARD_VALUES = [
        "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", 
        "Ten", "Jack", "Queen", "King", "Ace"
    ]
    
    @classmethod
    def evaluate_hand(cls, player_cards, community_cards):
        """
        Evaluates the best 5-card hand from player's hole cards and community cards.
        Returns tuple: (score, hand_name, best_five_cards)
        """
        all_cards = player_cards + community_cards
        all_hand_combos = list(itertools.combinations(all_cards, 5))
        
        best_score = None
        best_hand = None
        
        # Evaluate each possible 5-card combination
        for hand in all_hand_combos:
            score = cls._score_single_hand(hand)
            if best_score is None or score > best_score:
                best_score = score
                best_hand = hand
        
        # Generate a descriptive hand name
        hand_name = cls.get_hand_description(best_score)
        
        return best_score, hand_name, best_hand
    
    @classmethod
    def _score_single_hand(cls, hand):
        """
        Scores a single 5-card hand.
        Returns a tuple where the first element is the hand type (0-9)
        and subsequent elements are tie-breaker values.
        """
        suits = [card.suit for card in hand]
        values = [card.value for card in hand]
        value_counts = Counter(values)
        
        # Sort values in descending order for high card comparison
        sorted_values = sorted(values, reverse=True)
        
        # Initialize score components
        hand_type = 0  # High card by default
        primary = 0
        secondary = 0
        kickers = sorted_values[:5]  # Default kickers
        
        # Check for flush
        is_flush = len(set(suits)) == 1
        
        # Check for straight
        unique_values = sorted(set(values))
        is_straight = False
        straight_high = None
        
        # Regular straight
        if len(unique_values) >= 5:
            for i in range(len(unique_values) - 4):
                if unique_values[i:i+5] == list(range(unique_values[i], unique_values[i]+5)):
                    is_straight = True
                    straight_high = unique_values[i+4]
                    break
        
        # A-5 straight (wheel)
        if 12 in values and all(v in values for v in [0, 1, 2, 3]):
            is_straight = True
            straight_high = 3  # 5-high straight
        
        # Determine hand type and score components
        
        # Royal Flush
        if is_straight and is_flush and sorted_values[0] == 12 and sorted_values[4] == 8:
            hand_type = 9
            return (hand_type, [])
            
        # Straight Flush
        if is_straight and is_flush:
            hand_type = 8
            return (hand_type, [straight_high])
            
        # Four of a Kind
        quads = [v for v, count in value_counts.items() if count == 4]
        if quads:
            hand_type = 7
            primary = quads[0]
            kicker = next(v for v in values if v != primary)
            return (hand_type, [primary, kicker])
            
        # Full House
        trips = [v for v, count in value_counts.items() if count == 3]
        pairs = [v for v, count in value_counts.items() if count == 2]
        if trips and pairs:
            hand_type = 6
            return (hand_type, [trips[0], pairs[0]])
        if len(trips) > 1:  # Two sets of trips (rare but possible in 7-card evaluation)
            hand_type = 6
            trips.sort(reverse=True)
            return (hand_type, [trips[0], trips[1]])
            
        # Flush
        if is_flush:
            hand_type = 5
            return (hand_type, sorted_values[:5])
            
        # Straight
        if is_straight:
            hand_type = 4
            return (hand_type, [straight_high])
            
        # Three of a Kind
        if trips:
            hand_type = 3
            kickers = [v for v in sorted_values if v != trips[0]][:2]
            return (hand_type, [trips[0]] + kickers)
            
        # Two Pair
        if len(pairs) >= 2:
            hand_type = 2
            sorted_pairs = sorted(pairs, reverse=True)[:2]
            kicker = next(v for v in sorted_values if v not in sorted_pairs)
            return (hand_type, sorted_pairs + [kicker])
            
        # One Pair
        if pairs:
            hand_type = 1
            kickers = [v for v in sorted_values if v != pairs[0]][:3]
            return (hand_type, [pairs[0]] + kickers)
            
        # High Card
        return (hand_type, sorted_values[:5])
    
    @classmethod
    def get_hand_description(cls, score):
        """
        Converts a hand score tuple to a human-readable description.
        """
        hand_type = score[0]
        values = score[1:]
        
        base_name = cls.HAND_TYPES[hand_type]
        
        # Format depends on hand type
        if hand_type == 0:  # High Card
            return f"{base_name}: {cls.CARD_VALUES[values[0]]} High"
            
        elif hand_type == 1:  # One Pair
            return f"{base_name}: {cls.CARD_VALUES[values[0]]}s"
            
        elif hand_type == 2:  # Two Pair
            return f"{base_name}: {cls.CARD_VALUES[values[0]]}s and {cls.CARD_VALUES[values[1]]}s"
            
        elif hand_type == 3:  # Three of a Kind
            return f"{base_name}: {cls.CARD_VALUES[values[0]]}s"
            
        elif hand_type == 4:  # Straight
            return f"{base_name}: {cls.CARD_VALUES[values[0]]} High"
            
        elif hand_type == 5:  # Flush
            return f"{base_name}: {cls.CARD_VALUES[values[0]]} High"
            
        elif hand_type == 6:  # Full House
            return f"{base_name}: {cls.CARD_VALUES[values[0]]}s over {cls.CARD_VALUES[values[1]]}s"
            
        elif hand_type == 7:  # Four of a Kind
            return f"{base_name}: {cls.CARD_VALUES[values[0]]}s"
            
        elif hand_type == 8:  # Straight Flush
            return f"{base_name}: {cls.CARD_VALUES[values[0]]} High"
            
        elif hand_type == 9:  # Royal Flush
            return base_name
            
        return base_name

    @staticmethod
    def compute_pot_split(pot, players, active_players):
        """
        Computes how to split the pot considering all-in situations.
        Returns a dictionary mapping players to their winnings.
        """
        # Sort players by their stake (bet amount) in ascending order
        sorted_stakes = sorted(set(p.stake for p in active_players))
        pot_splits = {}
        
        # Process each stake level for side pots
        prev_stake = 0
        for stake in sorted_stakes:
            # Calculate pot size at this stake level
            eligible_players = [p for p in active_players if p.stake >= stake]
            pot_size = (stake - prev_stake) * len(eligible_players)
            
            # Find winners at this stake level
            winners = [p for p in eligible_players if not p.folded]
            if winners:
                split = pot_size / len(winners)
                for winner in winners:
                    pot_splits[winner] = pot_splits.get(winner, 0) + split
                    
            prev_stake = stake
        
        return pot_splits
