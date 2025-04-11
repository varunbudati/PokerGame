"""
Core poker game module.
Handles game flow, betting rounds, and poker rules.
"""

from typing import List, Dict, Any, Tuple, Optional
import random
from enum import Enum, auto
from .cards import Deck, Card, Hand, HandRank, evaluate_hand
from .player import Player
from .ai import AIPlayer

class GameState(Enum):
    """Game state enum representing the current phase of the poker game."""
    WAITING = auto()
    DEALING = auto()
    PRE_FLOP = auto()
    FLOP = auto()
    TURN = auto() 
    RIVER = auto()
    SHOWDOWN = auto()
    GAME_OVER = auto()

class BettingRound(Enum):
    """Enum representing the current betting round."""
    PRE_FLOP = "Pre-Flop"
    FLOP = "Flop"
    TURN = "Turn"
    RIVER = "River"

class PokerGame:
    """
    Main poker game class that handles Texas Hold'em gameplay.
    """
    
    def __init__(self, players: List[Player], small_blind: int = 5, big_blind: int = 10):
        """
        Initialize a new poker game.
        
        Args:
            players: List of Player objects
            small_blind: Small blind amount
            big_blind: Big blind amount
        """
        self.players = players
        self.num_players = len(players)
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.dealer_idx = 0
        self.current_player_idx = 0
        self.active_player_indices = []
        self.deck = Deck()
        self.community_cards: List[Card] = []
        self.pot = 0
        self.current_bet = 0
        self.min_raise = big_blind
        self.state = GameState.WAITING
        self.betting_round = BettingRound.PRE_FLOP
        self.last_aggressor_idx = None
        self.hand_history = []
        self.winners = []
        self.log_messages = []
        
        # Game stats
        self.hands_played = 0
        self.player_stats = {player.name: {"hands_won": 0, "chips_won": 0} for player in players}
    
    def start_new_hand(self):
        """Start a new hand of poker."""
        self.log_message("Starting a new hand")
        self.hands_played += 1
        
        # Reset game state
        self.deck = Deck()
        self.deck.shuffle()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.min_raise = self.big_blind
        self.state = GameState.DEALING
        self.betting_round = BettingRound.PRE_FLOP
        self.last_aggressor_idx = None
        self.winners = []
        
        # Remove players with no chips
        self.players = [p for p in self.players if p.chips > 0]
        self.num_players = len(self.players)
        
        if self.num_players < 2:
            self.log_message("Not enough players to start a hand")
            self.state = GameState.GAME_OVER
            return
        
        # Rotate dealer position
        self.dealer_idx = (self.dealer_idx + 1) % self.num_players
        
        # Reset player hands and bets
        for player in self.players:
            player.reset_hand()
            player.current_bet = 0
            player.has_folded = False
            player.has_acted = False
        
        # Set active players
        self.active_player_indices = list(range(self.num_players))
        
        # Deal cards
        self._deal_hole_cards()
        
        # Post blinds
        self._post_blinds()
        
        # Set current player to UTG (under the gun) position
        self.current_player_idx = (self.dealer_idx + 3) % self.num_players
        if self.num_players < 3:
            self.current_player_idx = (self.dealer_idx + 1) % self.num_players
        
        self.current_player_idx = self._next_active_player(self.current_player_idx)
        
        self.state = GameState.PRE_FLOP
    
    def _deal_hole_cards(self):
        """Deal two hole cards to each player."""
        for _ in range(2):
            for player_idx in range(self.num_players):
                player = self.players[player_idx]
                card = self.deck.deal_card()
                if card:
                    player.hand.add_card(card)
    
    def _post_blinds(self):
        """Post small and big blinds."""
        # Small blind
        sb_pos = (self.dealer_idx + 1) % self.num_players
        sb_player = self.players[sb_pos]
        sb_amount = min(self.small_blind, sb_player.chips)
        sb_player.bet(sb_amount)
        self.pot += sb_amount
        self.log_message(f"{sb_player.name} posts small blind: {sb_amount}")
        
        # Big blind
        bb_pos = (self.dealer_idx + 2) % self.num_players
        if self.num_players < 3:
            bb_pos = (self.dealer_idx) % self.num_players
        
        bb_player = self.players[bb_pos]
        bb_amount = min(self.big_blind, bb_player.chips)
        bb_player.bet(bb_amount)
        self.pot += bb_amount
        self.current_bet = bb_amount
        self.log_message(f"{bb_player.name} posts big blind: {bb_amount}")
    
    def _next_active_player(self, current_idx: int) -> int:
        """
        Find the next active player after the current index.
        
        Args:
            current_idx: Current player index
            
        Returns:
            Index of the next active player
        """
        next_idx = (current_idx + 1) % self.num_players
        while next_idx != current_idx:
            if next_idx in self.active_player_indices and not self.players[next_idx].has_folded:
                return next_idx
            next_idx = (next_idx + 1) % self.num_players
        
        # If we get here, there's only one active player
        return current_idx
    
    def get_current_player(self) -> Player:
        """Get the current player."""
        return self.players[self.current_player_idx]
    
    def get_game_state(self) -> Dict[str, Any]:
        """
        Get the current game state.
        
        Returns:
            Dictionary with current game state information
        """
        return {
            "state": self.state,
            "betting_round": self.betting_round,
            "pot": self.pot,
            "community_cards": self.community_cards.copy(),
            "current_bet": self.current_bet,
            "min_raise": self.min_raise,
            "active_players": len(self.active_player_indices),
            "current_player_idx": self.current_player_idx,
            "dealer_idx": self.dealer_idx
        }
    
    def handle_player_action(self, action: str, amount: int = 0) -> bool:
        """
        Handle a player's action.
        
        Args:
            action: Action string ('fold', 'check', 'call', 'raise', 'all_in')
            amount: Bet amount for 'raise' action
            
        Returns:
            True if action was processed successfully, False otherwise
        """
        if self.state in [GameState.GAME_OVER, GameState.SHOWDOWN]:
            return False
            
        current_player = self.get_current_player()
        to_call = self.current_bet - current_player.current_bet
        
        valid_action = False
        
        if action == 'fold':
            self._fold(self.current_player_idx)
            valid_action = True
            
        elif action == 'check':
            if to_call == 0:
                self.log_message(f"{current_player.name} checks")
                current_player.has_acted = True
                valid_action = True
            else:
                return False  # Cannot check when there's a bet to call
                
        elif action == 'call':
            if to_call > 0:
                call_amount = min(to_call, current_player.chips)
                current_player.bet(call_amount)
                self.pot += call_amount
                self.log_message(f"{current_player.name} calls {call_amount}")
                current_player.has_acted = True
                valid_action = True
            else:
                return False  # Nothing to call
                
        elif action == 'raise':
            # Validate raise amount
            if amount < self.current_bet + self.min_raise:
                # Must be at least current bet + minimum raise
                if current_player.chips <= self.current_bet + self.min_raise:
                    # Not enough chips for a proper raise, convert to all-in
                    return self.handle_player_action('all_in', 0)
                return False
                
            if amount > current_player.chips:
                # Cannot bet more than player has
                return False
            
            # Process the raise
            current_player.bet(amount)
            old_bet = self.current_bet
            self.current_bet = amount
            self.min_raise = self.current_bet - old_bet  # Set min raise to the last raise amount
            self.pot += amount
            self.last_aggressor_idx = self.current_player_idx
            self.log_message(f"{current_player.name} raises to {amount}")
            
            # Reset has_acted for all players except the raiser
            for i, player in enumerate(self.players):
                if i != self.current_player_idx and i in self.active_player_indices and not player.has_folded:
                    player.has_acted = False
            
            current_player.has_acted = True
            valid_action = True
            
        elif action == 'all_in':
            all_in_amount = current_player.chips
            if all_in_amount > self.current_bet:
                # All-in is a raise
                old_bet = self.current_bet
                self.current_bet = all_in_amount
                self.min_raise = self.current_bet - old_bet
                self.last_aggressor_idx = self.current_player_idx
                
                # Reset has_acted for all players except the all-in player
                for i, player in enumerate(self.players):
                    if i != self.current_player_idx and i in self.active_player_indices and not player.has_folded:
                        player.has_acted = False
            
            current_player.bet(all_in_amount)
            self.pot += all_in_amount
            self.log_message(f"{current_player.name} goes all-in for {all_in_amount}")
            current_player.has_acted = True
            valid_action = True
        
        # Move to the next player if action was valid
        if valid_action:
            # Check if betting round is over
            if self._is_betting_round_over():
                self._advance_game_state()
            else:
                self.current_player_idx = self._next_active_player(self.current_player_idx)
            
            return True
        
        return False
    
    def _fold(self, player_idx: int):
        """Fold a player's hand."""
        player = self.players[player_idx]
        player.has_folded = True
        if player_idx in self.active_player_indices:
            self.active_player_indices.remove(player_idx)
        self.log_message(f"{player.name} folds")
        
        # Check if only one player remains
        if len(self.active_player_indices) == 1:
            self._handle_single_player_remaining()
    
    def _is_betting_round_over(self) -> bool:
        """
        Check if the current betting round is over.
        
        Returns:
            True if betting round is over, False otherwise
        """
        # Count active players who haven't acted or haven't matched the current bet
        for i in self.active_player_indices:
            player = self.players[i]
            if not player.has_acted or player.current_bet < self.current_bet:
                return False
        
        return True
    
    def _advance_game_state(self):
        """Advance the game state to the next betting round or showdown."""
        if self.state == GameState.PRE_FLOP:
            self._deal_flop()
            self.state = GameState.FLOP
            self.betting_round = BettingRound.FLOP
        
        elif self.state == GameState.FLOP:
            self._deal_turn()
            self.state = GameState.TURN
            self.betting_round = BettingRound.TURN
        
        elif self.state == GameState.TURN:
            self._deal_river()
            self.state = GameState.RIVER
            self.betting_round = BettingRound.RIVER
        
        elif self.state == GameState.RIVER:
            self._handle_showdown()
            return
        
        # Reset for the next betting round
        self._reset_betting_round()
    
    def _reset_betting_round(self):
        """Reset for a new betting round."""
        self.current_bet = 0
        self.min_raise = self.big_blind
        self.last_aggressor_idx = None
        
        # Reset has_acted for all players
        for player in self.players:
            player.has_acted = False
        
        # Set current player to first active player after dealer
        self.current_player_idx = (self.dealer_idx + 1) % self.num_players
        self.current_player_idx = self._next_active_player(self.current_player_idx)
    
    def _deal_flop(self):
        """Deal the flop (first three community cards)."""
        # Burn a card
        self.deck.deal_card()
        
        # Deal three cards to the community
        for _ in range(3):
            card = self.deck.deal_card()
            if card:
                self.community_cards.append(card)
        
        self.log_message(f"Flop: {' '.join(str(card) for card in self.community_cards)}")
    
    def _deal_turn(self):
        """Deal the turn (fourth community card)."""
        # Burn a card
        self.deck.deal_card()
        
        # Deal the turn card
        card = self.deck.deal_card()
        if card:
            self.community_cards.append(card)
            self.log_message(f"Turn: {str(card)}")
    
    def _deal_river(self):
        """Deal the river (fifth community card)."""
        # Burn a card
        self.deck.deal_card()
        
        # Deal the river card
        card = self.deck.deal_card()
        if card:
            self.community_cards.append(card)
            self.log_message(f"River: {str(card)}")
    
    def _handle_single_player_remaining(self):
        """Handle the case where only one player remains (everyone else folded)."""
        if len(self.active_player_indices) == 1:
            winner_idx = self.active_player_indices[0]
            winner = self.players[winner_idx]
            self._award_pot([winner_idx])
            self.state = GameState.SHOWDOWN
    
    def _handle_showdown(self):
        """Handle the showdown where remaining players compare hands."""
        self.state = GameState.SHOWDOWN
        
        if len(self.active_player_indices) <= 1:
            if len(self.active_player_indices) == 1:
                self._handle_single_player_remaining()
            return
        
        # Evaluate hands and find winners
        best_hand_score = -1
        best_players = []
        
        for idx in self.active_player_indices:
            player = self.players[idx]
            all_cards = player.hand.cards + self.community_cards
            hand_result = evaluate_hand(all_cards)
            hand_score = self._calculate_hand_score(hand_result)
            
            self.log_message(f"{player.name} shows: {' '.join(str(card) for card in player.hand.cards)} - {hand_result[0].name}")
            
            if hand_score > best_hand_score:
                best_hand_score = hand_score
                best_players = [idx]
            elif hand_score == best_hand_score:
                best_players.append(idx)
        
        # Award pot to winners
        self._award_pot(best_players)
    
    def _calculate_hand_score(self, hand_result: Tuple[HandRank, List[int]]) -> float:
        """
        Calculate a numeric score for a hand result for easy comparison.
        
        Args:
            hand_result: Tuple of (HandRank, [kicker values])
            
        Returns:
            Numeric score for the hand
        """
        rank, kickers = hand_result
        
        # Base score from hand rank
        score = rank.value * 1000000
        
        # Add kickers in decreasing importance
        for i, kicker in enumerate(kickers):
            score += kicker * (10 ** (4 - i))
            
        return score
    
    def _award_pot(self, winner_indices: List[int]):
        """
        Award the pot to the winners.
        
        Args:
            winner_indices: List of indices of winning players
        """
        if not winner_indices:
            return
        
        num_winners = len(winner_indices)
        pot_per_player = self.pot // num_winners
        remainder = self.pot % num_winners
        
        for idx in winner_indices:
            winner = self.players[idx]
            # Add remainder to first winner if pot doesn't divide evenly
            extra = remainder if idx == winner_indices[0] else 0
            amount_won = pot_per_player + extra
            
            winner.add_chips(amount_won)
            self.winners.append((winner.name, amount_won))
            
            # Update stats
            self.player_stats[winner.name]["hands_won"] += 1
            self.player_stats[winner.name]["chips_won"] += amount_won
            
            self.log_message(f"{winner.name} wins {amount_won} chips")
            
            # Update AI player if applicable
            if isinstance(winner, AIPlayer):
                shown_cards = {self.players[i].name: self.players[i].hand.cards 
                              for i in self.active_player_indices}
                winner.update_after_hand(True, self.pot, shown_cards)
        
        # Update AI players who lost
        for idx in self.active_player_indices:
            player = self.players[idx]
            if idx not in winner_indices and isinstance(player, AIPlayer):
                shown_cards = {self.players[i].name: self.players[i].hand.cards 
                              for i in self.active_player_indices}
                player.update_after_hand(False, self.pot, shown_cards)
        
        self.pot = 0
    
    def get_winners(self) -> List[Tuple[str, int]]:
        """
        Get the list of winners and their winnings.
        
        Returns:
            List of tuples (winner_name, amount_won)
        """
        return self.winners
    
    def log_message(self, message: str):
        """
        Add a message to the game log.
        
        Args:
            message: Message to add to the log
        """
        self.log_messages.append(message)
        print(message)  # For debugging/console play
    
    def get_logs(self) -> List[str]:
        """
        Get the game log.
        
        Returns:
            List of log messages
        """
        return self.log_messages
    
    def get_player_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get player statistics.
        
        Returns:
            Dictionary of player stats
        """
        return self.player_stats