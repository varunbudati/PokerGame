import random

class Card:
    """Represents a standard playing card"""
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    SUITS = ['h', 'd', 'c', 's']  # hearts, diamonds, clubs, spades
    
    def __init__(self, rank, suit):
        if rank not in self.RANKS:
            raise ValueError(f"Invalid rank: {rank}")
        if suit not in self.SUITS:
            raise ValueError(f"Invalid suit: {suit}")
            
        self.rank = rank
        self.suit = suit
        self.rank_value = self.RANKS.index(rank)
        
    def __str__(self):
        return f"{self.rank}{self.suit}"
    
    def __repr__(self):
        return self.__str__()

class Deck:
    """Represents a standard deck of 52 playing cards"""
    
    def __init__(self):
        self.cards = []
        self.reset()
        
    def reset(self):
        """Reset the deck with all 52 cards"""
        self.cards = [Card(rank, suit) 
                     for suit in Card.SUITS 
                     for rank in Card.RANKS]
        
    def shuffle(self):
        """Shuffle the deck"""
        random.shuffle(self.cards)
        
    def deal(self, num_cards=1):
        """Deal a specific number of cards from the deck"""
        if len(self.cards) < num_cards:
            raise ValueError(f"Not enough cards in deck. {len(self.cards)} remaining.")
            
        dealt_cards = []
        for _ in range(num_cards):
            dealt_cards.append(self.cards.pop())
            
        return dealt_cards if num_cards > 1 else dealt_cards[0]
    
    def __len__(self):
        return len(self.cards)

class Hand:
    """Represents a poker hand"""
    
    def __init__(self, cards=None):
        self.cards = cards or []
        
    def add_card(self, card):
        """Add a card to the hand"""
        self.cards.append(card)
        
    def add_cards(self, cards):
        """Add multiple cards to the hand"""
        self.cards.extend(cards)
        
    def __len__(self):
        return len(self.cards)
    
    def __str__(self):
        return ", ".join(str(card) for card in self.cards)

def evaluate_hand(cards):
    """
    Evaluate a poker hand and return its rank.
    Returns a tuple of (hand_rank_value, [tie_breaker_values])
    where hand_rank_value is:
    9: Royal Flush
    8: Straight Flush
    7: Four of a Kind
    6: Full House
    5: Flush
    4: Straight
    3: Three of a Kind
    2: Two Pair
    1: One Pair
    0: High Card
    """
    if len(cards) < 5:
        raise ValueError("Need at least 5 cards to evaluate a poker hand")
    
    # Convert to simple representation for evaluation
    ranks = [card.rank_value for card in cards]
    suits = [card.suit for card in cards]
    
    # Count frequencies of each rank
    rank_counts = {}
    for rank in ranks:
        if rank in rank_counts:
            rank_counts[rank] += 1
        else:
            rank_counts[rank] = 1
    
    # Check for flush (all same suit)
    is_flush = len(set(suits)) == 1
    
    # Check for straight (5 consecutive ranks)
    sorted_ranks = sorted(set(ranks))
    is_straight = False
    
    # Check normal straight
    if len(sorted_ranks) >= 5:
        for i in range(len(sorted_ranks) - 4):
            if sorted_ranks[i:i+5] == list(range(sorted_ranks[i], sorted_ranks[i]+5)):
                is_straight = True
                straight_high = sorted_ranks[i+4]
                break
    
    # Check A-5 straight (Ace counts as 1)
    if 12 in ranks and all(r in ranks for r in [0, 1, 2, 3]):
        is_straight = True
        straight_high = 3  # 5 high straight
    
    # Determine hand rank
    if is_straight and is_flush:
        # Check for royal flush (10-A of same suit)
        royal_ranks = [8, 9, 10, 11, 12]  # 10, J, Q, K, A
        is_royal = all(r in ranks for r in royal_ranks)
        
        if is_royal:
            return (9, [])  # Royal Flush
        else:
            return (8, [straight_high])  # Straight Flush
            
    # Four of a Kind
    if 4 in rank_counts.values():
        four_rank = [r for r, c in rank_counts.items() if c == 4][0]
        kickers = [r for r in ranks if r != four_rank]
        kicker = max(kickers)
        return (7, [four_rank, kicker])
    
    # Full House
    if 3 in rank_counts.values() and 2 in rank_counts.values():
        three_rank = [r for r, c in rank_counts.items() if c == 3][0]
        pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
        return (6, [three_rank, pair_rank])
    
    # Flush
    if is_flush:
        return (5, sorted(ranks, reverse=True)[:5])
    
    # Straight
    if is_straight:
        return (4, [straight_high])
    
    # Three of a Kind
    if 3 in rank_counts.values():
        three_rank = [r for r, c in rank_counts.items() if c == 3][0]
        kickers = sorted([r for r in ranks if r != three_rank], reverse=True)
        return (3, [three_rank] + kickers[:2])
    
    # Two Pair
    pairs = [r for r, c in rank_counts.items() if c == 2]
    if len(pairs) >= 2:
        pairs.sort(reverse=True)
        kickers = [r for r in ranks if r not in pairs]
        return (2, pairs[:2] + [max(kickers)])
    
    # One Pair
    if 2 in rank_counts.values():
        pair_rank = [r for r, c in rank_counts.items() if c == 2][0]
        kickers = sorted([r for r in ranks if r != pair_rank], reverse=True)
        return (1, [pair_rank] + kickers[:3])
    
    # High Card
    return (0, sorted(ranks, reverse=True)[:5])

def rank_to_string(rank_tuple):
    """Convert a hand rank tuple to a human-readable string"""
    hand_names = [
        "High Card",
        "One Pair",
        "Two Pair",
        "Three of a Kind",
        "Straight",
        "Flush",
        "Full House",
        "Four of a Kind",
        "Straight Flush",
        "Royal Flush"
    ]
    
    rank_value = rank_tuple[0]
    return hand_names[rank_value]