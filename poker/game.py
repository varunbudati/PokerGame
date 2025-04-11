import random
import time
from typing import List, Optional, Dict, Tuple, Any
from enum import Enum, auto

from .cards import Deck, Card, Hand, compare_hands, evaluate_hand
from .player import Player
from .ai import AIPlayer

class GameState(Enum):
    """Possible states of the poker game."""
    WAITING_FOR_PLAYERS = auto()  # Waiting for players to join
    DEALING_CARDS = auto()        # Dealing initial cards
    WAITING_FOR_PLAYER = auto()   # Waiting for human player input
    AI_THINKING = auto()          # AI player is making a decision
    DEALING_FLOP = auto()         # Dealing the flop (first 3 community cards)
    DEALING_TURN = auto()         # Dealing the turn (4th community card)
    DEALING_RIVER = auto()        # Dealing the river (5th community card)
    HAND_COMPLETE = auto()        # Hand is complete, determining winner

class GameAction(Enum):
    """Possible poker actions a player can take."""
    FOLD = auto()
    CHECK = auto()
    CALL = auto()
    RAISE = auto()
    ALL_IN = auto()

class BettingRound(Enum):
    """Poker betting rounds."""
    PRE_FLOP = "Pre-Flop"
    FLOP = "Flop"
    TURN = "Turn"
    RIVER = "River"

class PokerGame:
    """
    Texas Hold'em poker game engine that manages game state, betting rounds,
    and determines winners.
    """
    
    def __init__(self, player: Player, opponents: List[AIPlayer], small_blind: int = 5, big_blind: int = 10):
        self.player = player
        self.opponents = opponents
        self.all_players = [player] + opponents
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.button_idx = 0  # Dealer button position
        self.deck = Deck()
        self.community_cards: List[Card] = []
        self.pot = 0
        self.current_bet = 0
        self.min_raise_amount = big_blind
        self.state = GameState.WAITING_FOR_PLAYERS
        self.betting_round = BettingRound.PRE_FLOP
        self.active_player_idx = 0
        self.winner = None
        self.winners = []
        self.last_raise_idx = -1
    
    def start_hand(self):
        """Start a new hand of poker."""
        # Reset game state
        for p in self.all_players:
            p.clear_hand()
        
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.min_raise_amount = self.big_blind
        self.state = GameState.DEALING_CARDS
        self.betting_round = BettingRound.PRE_FLOP
        self.winner = None
        self.winners = []
        
        # Rotate button
        self.button_idx = (self.button_idx + 1) % len(self.all_players)
        
        # Post blinds
        sb_idx = (self.button_idx + 1) % len(self.all_players)
        bb_idx = (self.button_idx + 2) % len(self.all_players)
        
        small_blind_player = self.all_players[sb_idx]
        big_blind_player = self.all_players[bb_idx]
        
        # Post small blind
        sb_amount = small_blind_player.place_bet(self.small_blind)
        self.pot += sb_amount
        
        # Post big blind
        bb_amount = big_blind_player.place_bet(self.big_blind)
        self.pot += bb_amount
        self.current_bet = self.big_blind
        
        # Deal hole cards
        for p in self.all_players:
            p.hand.add_cards(self.deck.deal(2))
        
        # Set the active player to the one after the big blind
        self.active_player_idx = (bb_idx + 1) % len(self.all_players)
        self.last_raise_idx = bb_idx  # Last raise was the big blind
        
        # Start the first betting round
        self.process_betting_round()
    
    def process_betting_round(self):
        """Process the current betting round."""
        # If the human player is active, wait for input
        if self.all_players[self.active_player_idx] == self.player:
            self.state = GameState.WAITING_FOR_PLAYER
            return
        
        # Otherwise, make AI decision
        self.state = GameState.AI_THINKING
        self.ai_make_move()
    
    def ai_make_move(self):
        """Have the current AI player make a move."""
        current_ai = self.all_players[self.active_player_idx]
        
        # If AI has folded or is all-in, move to next player
        if current_ai.folded or current_ai.is_all_in:
            self.next_player()
            return
        
        # Get game state info for AI
        game_state = {
            'current_bet': self.current_bet,
            'pot': self.pot,
            'community_cards': self.community_cards,
            'min_raise': self.min_raise_amount,
            'betting_round': self.betting_round
        }
        
        # Simulate AI thinking
        time.sleep(random.uniform(0.5, 1.5))
        
        # Make decision
        action, amount = current_ai.make_decision(game_state)
        
        # Execute AI action
        if action == 'fold':
            current_ai.fold()
        elif action == 'check':
            current_ai.check()
        elif action == 'call':
            call_amount = self.current_bet - current_ai.current_bet
            added_to_pot = current_ai.call(self.current_bet)
            self.pot += added_to_pot
        elif action == 'raise':
            # How much more on top of matching the current bet
            extra_amount = amount
            total_raise = self.current_bet + extra_amount
            
            # Update minimum raise
            self.min_raise_amount = extra_amount
            self.current_bet = total_raise
            
            # Record this raise
            self.last_raise_idx = self.active_player_idx
            
            # Execute the raise
            added_to_pot = current_ai.raise_bet(total_raise)
            self.pot += added_to_pot
        elif action == 'all_in':
            added_to_pot = current_ai.all_in()
            
            # If this all-in is a raise, update current bet and last raiser
            if current_ai.current_bet > self.current_bet:
                self.current_bet = current_ai.current_bet
                self.last_raise_idx = self.active_player_idx
            
            self.pot += added_to_pot
        
        # Move to next player
        self.next_player()
    
    def next_player(self):
        """Move to the next active player."""
        # Find the next active player
        next_idx = (self.active_player_idx + 1) % len(self.all_players)
        
        # Skip folded players and all-in players
        while (self.all_players[next_idx].folded or 
               self.all_players[next_idx].is_all_in) and next_idx != self.active_player_idx:
            next_idx = (next_idx + 1) % len(self.all_players)
        
        # If we've gone all the way around back to the active player
        # or reached the last raise player, end the betting round
        if next_idx == self.active_player_idx or next_idx == self.last_raise_idx:
            # End of betting round
            self.advance_betting_round()
            return
        
        # Update active player
        self.active_player_idx = next_idx
        
        # Process the next player
        self.process_betting_round()
    
    def advance_betting_round(self):
        """Move to the next betting round or determine the winner."""
        # Count active (non-folded) players
        active_players = [p for p in self.all_players if not p.folded]
        
        # If only one player left, they win
        if len(active_players) == 1:
            self.winner = active_players[0]
            self.winner.collect_winnings(self.pot)
            self.state = GameState.HAND_COMPLETE
            return
        
        # Reset for next betting round
        for p in self.all_players:
            # Keep folded status but reset current bet
            if not p.folded:
                p.current_bet = 0
        
        self.current_bet = 0
        self.min_raise_amount = self.big_blind
        
        # Determine which betting round comes next
        if self.betting_round == BettingRound.PRE_FLOP:
            self.betting_round = BettingRound.FLOP
            self.state = GameState.DEALING_FLOP
            # Deal the flop
            self.community_cards.extend(self.deck.deal(3))
        elif self.betting_round == BettingRound.FLOP:
            self.betting_round = BettingRound.TURN
            self.state = GameState.DEALING_TURN
            # Deal the turn
            self.community_cards.extend(self.deck.deal(1))
        elif self.betting_round == BettingRound.TURN:
            self.betting_round = BettingRound.RIVER
            self.state = GameState.DEALING_RIVER
            # Deal the river
            self.community_cards.extend(self.deck.deal(1))
        else:
            # End of hand, determine winner
            self.determine_winner()
            self.state = GameState.HAND_COMPLETE
            return
        
        # Start next betting round with player after button
        self.active_player_idx = (self.button_idx + 1) % len(self.all_players)
        self.last_raise_idx = -1  # Reset last raise
        
        # Skip folded or all-in players
        while (self.all_players[self.active_player_idx].folded or 
               self.all_players[self.active_player_idx].is_all_in) and self.active_player_idx != self.button_idx:
            self.active_player_idx = (self.active_player_idx + 1) % len(self.all_players)
        
        # Start the next betting round
        self.process_betting_round()
    
    def determine_winner(self):
        """Evaluate all hands and determine the winner(s)."""
        active_players = [p for p in self.all_players if not p.folded]
        
        if len(active_players) == 1:
            # Only one player left, they win
            self.winner = active_players[0]
            self.winners = [self.winner]
        else:
            # Compare hands to find winner(s)
            best_hand_rank = -1
            best_players = []
            
            for p in active_players:
                # Combine hole cards with community cards
                all_cards = p.hand.cards + self.community_cards
                rank_result = evaluate_hand(all_cards)
                hand_rank = rank_result[0].value  # Get the enum value
                
                # Check if this is the best hand so far
                if hand_rank > best_hand_rank:
                    best_hand_rank = hand_rank
                    best_players = [p]
                elif hand_rank == best_hand_rank:
                    # Potential tie, compare kickers
                    if len(best_players) > 0:
                        comparison = compare_hands(all_cards, best_players[0].hand.cards + self.community_cards)
                        if comparison > 0:
                            # This hand is better
                            best_players = [p]
                        elif comparison == 0:
                            # True tie
                            best_players.append(p)
                    else:
                        best_players.append(p)
            
            # Assign winner(s)
            if len(best_players) == 1:
                self.winner = best_players[0]
                self.winners = best_players
            else:
                self.winner = None
                self.winners = best_players
        
        # Distribute pot
        self.award_pot()
    
    def award_pot(self):
        """Award the pot to the winner(s)."""
        if len(self.winners) == 1:
            # Single winner takes all
            self.winners[0].collect_winnings(self.pot)
        elif len(self.winners) > 1:
            # Split pot among winners
            share = self.pot // len(self.winners)
            remainder = self.pot % len(self.winners)
            
            for p in self.winners:
                p.collect_winnings(share)
            
            # Give remainder to the first winner (closest to button)
            if remainder > 0:
                self.winners[0].collect_winnings(remainder)
    
    # Player action methods
    def player_fold(self):
        """Human player folds."""
        if self.state != GameState.WAITING_FOR_PLAYER:
            return
        
        self.player.fold()
        self.next_player()
    
    def player_check(self):
        """Human player checks."""
        if self.state != GameState.WAITING_FOR_PLAYER:
            return
        
        if self.current_bet > self.player.current_bet:
            # Can't check, must call or raise
            return
        
        self.player.check()
        self.next_player()
    
    def player_call(self):
        """Human player calls the current bet."""
        if self.state != GameState.WAITING_FOR_PLAYER:
            return
        
        call_amount = self.current_bet - self.player.current_bet
        
        if call_amount <= 0:
            # Nothing to call, treat as check
            self.player_check()
            return
        
        added_to_pot = self.player.call(self.current_bet)
        self.pot += added_to_pot
        
        self.next_player()
    
    def player_raise(self, total_bet: int):
        """Human player raises to the specified amount."""
        if self.state != GameState.WAITING_FOR_PLAYER:
            return
        
        # Ensure raise amount is at least min raise
        if total_bet < self.current_bet + self.min_raise_amount:
            total_bet = self.current_bet + self.min_raise_amount
        
        # Update current bet and last raiser
        self.current_bet = total_bet
        self.last_raise_idx = self.active_player_idx
        
        # Update minimum raise for the next raise
        self.min_raise_amount = total_bet - self.player.current_bet
        
        # Execute the raise
        added_to_pot = self.player.raise_bet(total_bet)
        self.pot += added_to_pot
        
        self.next_player()
    
    def player_all_in(self):
        """Human player goes all-in."""
        if self.state != GameState.WAITING_FOR_PLAYER:
            return
        
        added_to_pot = self.player.all_in()
        
        # If all-in amount is a raise, update current bet and last raiser
        if self.player.current_bet > self.current_bet:
            self.current_bet = self.player.current_bet
            self.last_raise_idx = self.active_player_idx
        
        self.pot += added_to_pot
        self.next_player()
    
    def can_check(self) -> bool:
        """Check if the current player can check (no bet to call)."""
        return self.player.current_bet == self.current_bet
    
    def min_raise(self) -> int:
        """Get the minimum raise amount."""
        return self.current_bet + self.min_raise_amount