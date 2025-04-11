"""
Interactive Texas Hold'em Poker Game - Core Logic
================================================

This package contains the core logic for the interactive poker game,
including card handling, player behavior, AI opponents, and game state management.
"""

# This file makes the 'poker' directory a Python package

from .cards import Card, Deck, Hand, HandRank, compare_hands, evaluate_hand, rank_to_string
from .player import Player
from .ai import AIPlayer
from .game import PokerGame, GameState, GameAction, BettingRound

__all__ = [
    'Card', 'Deck', 'Hand', 'HandRank', 'compare_hands', 'evaluate_hand', 'rank_to_string',
    'Player', 'AIPlayer',
    'PokerGame', 'GameState', 'GameAction', 'BettingRound'
]