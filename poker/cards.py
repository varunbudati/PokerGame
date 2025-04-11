import random
from typing import List, Tuple, Dict, Any
from enum import Enum, auto

class Suit(Enum):
    CLUBS = "c"
    DIAMONDS = "d"
    HEARTS = "h"
    SPADES = "s"
    
    def __str__(self):
        return self.value

class Card:
    """A playing card with a suit and rank."""
    
    # Maps card ranks to their values
    RANKS = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
        "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14
    }
    
    def __init__(self, rank: str, suit: Suit):
        self.rank = rank
        self.suit = suit
        self.value = self.RANKS[rank]
    
    def __str__(self):
        return f"{self.rank}{self.suit.value}"
    
    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.rank == other.rank and self.suit == other.suit
    
    def __lt__(self, other):
        return self.value < other.value
    
    @property
    def short_name(self):
        """Return the short name used by card APIs (e.g., 'AS' for Ace of Spades)."""
        if self.rank == "10":
            return f"0{self.suit.value.upper()}"
        return f"{self.rank}{self.suit.value.upper()}"

class Deck:
    """A standard deck of 52 playing cards."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset the deck to a full, unshuffled state."""
        self.cards = []
        
        for suit in Suit:
            for rank in Card.RANKS:
                self.cards.append(Card(rank, suit))
        
        self.shuffle()
    
    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)
    
    def deal(self, num_cards: int = 1) -> List[Card]:
        """Deal a specified number of cards from the deck."""
        if num_cards > len(self.cards):
            raise ValueError(f"Cannot deal {num_cards} cards; only {len(self.cards)} remaining.")
        
        dealt_cards = []
        for _ in range(num_cards):
            dealt_cards.append(self.cards.pop())
        
        return dealt_cards

class Hand:
    """A poker hand, consisting of cards held by a player."""
    
    def __init__(self, cards: List[Card] = None):
        self.cards = cards or []
    
    def add_card(self, card: Card):
        """Add a card to the hand."""
        self.cards.append(card)
    
    def add_cards(self, cards: List[Card]):
        """Add multiple cards to the hand."""
        self.cards.extend(cards)
    
    def clear(self):
        """Remove all cards from the hand."""
        self.cards = []
    
    def __str__(self):
        return ", ".join(str(card) for card in self.cards)

# Hand rankings
class HandRank(Enum):
    HIGH_CARD = auto()
    PAIR = auto()
    TWO_PAIR = auto()
    THREE_OF_A_KIND = auto()
    STRAIGHT = auto()
    FLUSH = auto()
    FULL_HOUSE = auto()
    FOUR_OF_A_KIND = auto()
    STRAIGHT_FLUSH = auto()
    ROYAL_FLUSH = auto()

def rank_to_string(rank: HandRank) -> str:
    """Convert a HandRank enum to a readable string."""
    return {
        HandRank.HIGH_CARD: "High Card",
        HandRank.PAIR: "Pair",
        HandRank.TWO_PAIR: "Two Pair",
        HandRank.THREE_OF_A_KIND: "Three of a Kind",
        HandRank.STRAIGHT: "Straight",
        HandRank.FLUSH: "Flush",
        HandRank.FULL_HOUSE: "Full House",
        HandRank.FOUR_OF_A_KIND: "Four of a Kind",
        HandRank.STRAIGHT_FLUSH: "Straight Flush",
        HandRank.ROYAL_FLUSH: "Royal Flush"
    }[rank]

def evaluate_hand(cards: List[Card]) -> Tuple[HandRank, List[int]]:
    """
    Evaluate a poker hand (5-7 cards) and return its ranking.
    
    Returns a tuple of (HandRank, [kickers]) where kickers are used to break ties.
    """
    if len(cards) < 5:
        raise ValueError("Need at least 5 cards to evaluate a poker hand")
    
    # Sort cards by value (descending)
    sorted_cards = sorted(cards, key=lambda x: x.value, reverse=True)
    
    # Get counts of each rank
    rank_counts = {}
    for card in sorted_cards:
        if card.value in rank_counts:
            rank_counts[card.value] += 1
        else:
            rank_counts[card.value] = 1
    
    # Check for flush (all same suit)
    is_flush = all(card.suit == sorted_cards[0].suit for card in sorted_cards)
    
    # Check for straight (sequential values)
    values = [card.value for card in sorted_cards]
    unique_values = sorted(set(values), reverse=True)
    
    # Handle Ace as low (A,2,3,4,5)
    if 14 in unique_values and 2 in unique_values:  # If we have an Ace and a 2
        straight_values = [14, 5, 4, 3, 2]
        has_wheel = all(v in unique_values for v in [14, 2, 3, 4, 5])
    else:
        has_wheel = False
    
    # Check for standard straight
    is_straight = False
    for i in range(len(unique_values) - 4):
        if unique_values[i] - unique_values[i+4] == 4:
            is_straight = True
            straight_high = unique_values[i]
            break
    
    # Handle wheel straight (A,2,3,4,5) differently
    if not is_straight and has_wheel:
        is_straight = True
        straight_high = 5  # 5 is the high card in A,2,3,4,5 for comparison purposes
    
    # Evaluate the hand from best to worst
    if is_straight and is_flush:
        if straight_high == 14:
            return (HandRank.ROYAL_FLUSH, [])
        else:
            return (HandRank.STRAIGHT_FLUSH, [straight_high])
    
    # Check for four of a kind
    four_kind = [v for v, count in rank_counts.items() if count == 4]
    if four_kind:
        kickers = [v for v in unique_values if v != four_kind[0]]
        return (HandRank.FOUR_OF_A_KIND, four_kind + [kickers[0]])
    
    # Check for full house
    three_kind = [v for v, count in rank_counts.items() if count == 3]
    pairs = [v for v, count in rank_counts.items() if count == 2]
    
    if three_kind and pairs:
        return (HandRank.FULL_HOUSE, [three_kind[0], pairs[0]])
    elif len(three_kind) >= 2:
        # Two sets of three of a kind, use the highest as the three of a kind
        three_kind.sort(reverse=True)
        return (HandRank.FULL_HOUSE, [three_kind[0], three_kind[1]])
    
    if is_flush:
        flush_values = [card.value for card in sorted_cards if card.suit == sorted_cards[0].suit]
        flush_values.sort(reverse=True)
        return (HandRank.FLUSH, flush_values[:5])
    
    if is_straight:
        if has_wheel:
            return (HandRank.STRAIGHT, [5])  # Ace-5 straight
        return (HandRank.STRAIGHT, [straight_high])
    
    if three_kind:
        kickers = [v for v in unique_values if v != three_kind[0]]
        return (HandRank.THREE_OF_A_KIND, [three_kind[0]] + kickers[:2])
    
    if len(pairs) >= 2:
        pairs.sort(reverse=True)
        kickers = [v for v in unique_values if v not in pairs[:2]]
        return (HandRank.TWO_PAIR, pairs[:2] + [kickers[0]])
    
    if pairs:
        kickers = [v for v in unique_values if v != pairs[0]]
        return (HandRank.PAIR, [pairs[0]] + kickers[:3])
    
    return (HandRank.HIGH_CARD, unique_values[:5])

def compare_hands(hand1: List[Card], hand2: List[Card]) -> int:
    """
    Compare two poker hands and determine the winner.
    
    Returns:
    - 1 if hand1 wins
    - -1 if hand2 wins
    - 0 if it's a tie
    """
    rank1, kickers1 = evaluate_hand(hand1)
    rank2, kickers2 = evaluate_hand(hand2)
    
    # Compare hand ranks first
    if rank1.value > rank2.value:
        return 1
    if rank1.value < rank2.value:
        return -1
    
    # If ranks are the same, compare kickers
    for k1, k2 in zip(kickers1, kickers2):
        if k1 > k2:
            return 1
        if k1 < k2:
            return -1
    
    # If all kickers match, it's a tie
    return 0