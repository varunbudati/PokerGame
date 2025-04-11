import random
import time
from typing import List, Optional, Dict, Tuple, Any
from enum import Enum, auto

from .cards import Deck, evaluate_hand, rank_to_string
from .player import Player
from .ai import AIPlayer

class GameState:
    """Represents the current state of a poker game"""
    PRE_FLOP = "Pre-Flop"
    FLOP = "Flop"
    TURN = "Turn"
    RIVER = "River"
    SHOWDOWN = "Showdown"

class GameAction:
    """Possible player actions"""
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    ALL_IN = "all_in"

class PokerGame:
    """Represents a Texas Hold'em poker game"""
    
    def __init__(self, players):
        self.players = players
        self.human_player = next((p for p in players if p.name == "You"), None)
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.current_state = None
        self.current_player_index = 0
        self.current_player = None
        self.current_bet = 0
        self.minimum_raise = 10  # Minimum raise amount
        self.small_blind = 5
        self.big_blind = 10
        self.dealer_index = 0
        self.active_players = []
    
    def start_game(self):
        """Start a new poker game"""
        self.start_new_hand()
    
    def start_new_hand(self):
        """Start a new hand"""
        # Reset game state
        self.deck = Deck()
        self.deck.shuffle()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        
        # Reset player state
        for player in self.players:
            player.reset_for_hand()
        
        # Set dealer position (rotate)
        self.dealer_index = (self.dealer_index + 1) % len(self.players)
        
        # Post blinds
        self.post_blinds()
        
        # Deal hole cards
        self.deal_hole_cards()
        
        # Set initial game state
        self.current_state = GameState.PRE_FLOP
        
        # Set first player to act (after big blind)
        self.active_players = [p for p in self.players if p.is_active and not p.folded]
        self.current_player_index = (self.dealer_index + 3) % len(self.players)
        self.current_player_index %= len(self.active_players)
        self.current_player = self.active_players[self.current_player_index]
        
        return self.get_game_state()
    
    def post_blinds(self):
        """Post small and big blinds"""
        # Small blind position
        sb_index = (self.dealer_index + 1) % len(self.players)
        sb_player = self.players[sb_index]
        sb_amount = sb_player.place_bet(self.small_blind)
        self.pot += sb_amount
        sb_player.last_action = f"Small Blind ${sb_amount}"
        
        # Big blind position
        bb_index = (self.dealer_index + 2) % len(self.players)
        bb_player = self.players[bb_index]
        bb_amount = bb_player.place_bet(self.big_blind)
        self.pot += bb_amount
        bb_player.last_action = f"Big Blind ${bb_amount}"
        
        # Set current bet to big blind
        self.current_bet = self.big_blind
        self.minimum_raise = self.big_blind
    
    def deal_hole_cards(self):
        """Deal two hole cards to each player"""
        for _ in range(2):  # Two cards per player
            for player in self.players:
                card = self.deck.deal()
                player.add_cards([card])
    
    def deal_community_cards(self, count=1):
        """Deal community cards"""
        new_cards = self.deck.deal(count)
        if not isinstance(new_cards, list):
            new_cards = [new_cards]
        self.community_cards.extend(new_cards)
    
    def get_community_cards(self):
        """Get the current community cards"""
        return self.community_cards
    
    def get_game_state(self):
        """Get the current game state"""
        return {
            "current_state": self.current_state,
            "pot": self.pot,
            "current_bet": self.current_bet,
            "dealer_position": self.dealer_index,
            "active_players": len(self.active_players),
            "community_cards": self.community_cards,
            "player_cards": self.human_player.hand if self.human_player else []
        }
    
    def process_action(self, player, action, amount=0):
        """Process a player action"""
        if player != self.current_player:
            return False
            
        if action == GameAction.FOLD:
            player.fold()
        
        elif action == GameAction.CHECK:
            if self.current_bet > player.current_bet:
                return False  # Can't check if there's a bet to call
            player.check()
        
        elif action == GameAction.CALL:
            bet_amount = player.call(self.current_bet)
            self.pot += bet_amount
        
        elif action == GameAction.RAISE:
            # Ensure minimum raise
            if amount < self.minimum_raise:
                amount = self.minimum_raise
                
            # Calculate actual raise amount (includes matching current bet)
            total_bet = self.current_bet - player.current_bet + amount
            
            bet_amount = player.raise_bet(total_bet)
            self.pot += bet_amount
            self.current_bet = player.current_bet
            self.minimum_raise = amount  # Set minimum raise for next raise
        
        elif action == GameAction.ALL_IN:
            bet_amount = player.all_in()
            self.pot += bet_amount
            
            # Update current bet if this all-in is higher
            if player.current_bet > self.current_bet:
                self.current_bet = player.current_bet
        
        # Update active players list
        self.active_players = [p for p in self.players if p.is_active and not p.folded]
        
        # Move to next player
        if len(self.active_players) > 1:
            self.move_to_next_player()
        
        return True
    
    def move_to_next_player(self):
        """Move to the next active player"""
        if not self.active_players:
            return
            
        start_idx = self.active_players.index(self.current_player)
        current_idx = start_idx
        
        while True:
            current_idx = (current_idx + 1) % len(self.active_players)
            next_player = self.active_players[current_idx]
            
            # Skip players who are all-in
            if next_player.is_all_in:
                if current_idx == start_idx:  # We've gone full circle
                    break
                continue
                
            self.current_player = next_player
            break
    
    def is_round_complete(self):
        """Check if the current betting round is complete"""
        # Round is complete when:
        # 1. All active players have equal bets
        # 2. Or only one player is active (rest have folded)
        # 3. Or all active players are all-in
        
        if len(self.active_players) <= 1:
            return True
            
        active_not_all_in = [p for p in self.active_players if not p.is_all_in]
        if not active_not_all_in:
            return True
            
        # Check if all active players have matched the current bet
        return all(p.current_bet == self.current_bet or p.is_all_in for p in self.active_players)
    
    def next_round(self):
        """Move to the next betting round"""
        if self.current_state == GameState.PRE_FLOP:
            self.current_state = GameState.FLOP
            self.deal_community_cards(3)  # Deal flop (3 cards)
        
        elif self.current_state == GameState.FLOP:
            self.current_state = GameState.TURN
            self.deal_community_cards(1)  # Deal turn (1 card)
        
        elif self.current_state == GameState.TURN:
            self.current_state = GameState.RIVER
            self.deal_community_cards(1)  # Deal river (1 card)
        
        elif self.current_state == GameState.RIVER:
            self.current_state = GameState.SHOWDOWN
            self.showdown()
        
        # Reset betting
        self.current_bet = 0
        for player in self.active_players:
            player.current_bet = 0
        
        # Reset first player to act
        if self.active_players:
            self.current_player = self.active_players[0]
        
        return self.current_state
    
    def is_hand_complete(self):
        """Check if the current hand is complete"""
        # Hand is complete when:
        # 1. Only one active player remains, or
        # 2. We've reached showdown
        return len(self.active_players) <= 1 or self.current_state == GameState.SHOWDOWN
    
    def showdown(self):
        """Handle the showdown phase"""
        # All remaining players reveal their cards
        for player in self.active_players:
            player.reveal_cards()
        
        # Hand is complete, will be evaluated by determine_winner
    
    def determine_winner(self):
        """Determine the winner of the hand"""
        if len(self.active_players) == 1:
            winner = self.active_players[0]
            winner.collect_winnings(self.pot)
            return winner
            
        # Compare hands at showdown
        best_hand_value = -1
        winners = []
        
        for player in self.active_players:
            # Combine hole cards with community cards
            all_cards = player.hand + self.community_cards
            
            # Evaluate the best 5-card hand
            hand_value = evaluate_hand(all_cards)
            
            # Compare with current best hand
            if not winners or hand_value > best_hand_value:
                best_hand_value = hand_value
                winners = [player]
            elif hand_value == best_hand_value:
                winners.append(player)
        
        # Split pot among winners
        split_amount = self.pot // len(winners)
        remainder = self.pot % len(winners)
        
        for winner in winners:
            winner.collect_winnings(split_amount)
        
        # Give remainder to first winner (closest to dealer)
        if remainder > 0 and winners:
            winners[0].collect_winnings(remainder)
        
        return winners[0] if winners else None
    
    def can_check(self):
        """Check if the current player can check"""
        return self.current_player.current_bet >= self.current_bet
    
    def can_call(self):
        """Check if the current player can call"""
        return self.current_bet > self.current_player.current_bet
    
    def can_raise(self):
        """Check if the current player can raise"""
        return (self.current_player.chips > 0 and 
                not self.current_player.is_all_in)
    
    def process_round(self):
        """Process the current round until completion"""
        while not self.is_round_complete() and len(self.active_players) > 1:
            # AI players take their actions
            if self.current_player != self.human_player and hasattr(self.current_player, 'decide_action'):
                action, amount = self.current_player.decide_action(self.get_game_state())
                self.process_action(self.current_player, action, amount)
        
        # If round complete but hand not over, move to next round
        if self.is_round_complete() and not self.is_hand_complete():
            self.next_round()
            
            # Continue processing if no human player or human player is inactive
            if not self.human_player or not self.human_player.is_active:
                self.process_round()