import random
import time
import logging
from typing import List, Optional, Dict, Tuple, Any
from enum import Enum, auto

from .cards import Deck, evaluate_hand, rank_to_string
from .player import Player
from .ai import AIPlayer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        self.winning_hand_name = ""
    
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
            "player_cards": self.human_player.hand if self.human_player else [],
            "min_raise": self.minimum_raise,  # Added for UI to know minimum raise
            "hand_complete": self.is_hand_complete()  # Added to help UI know when hand is done
        }
    
    def process_action(self, player, action, amount=0):
        """Process a player action"""
        logging.info(f"Player {player.name} performing action {action} with amount {amount}")
        if player != self.current_player:
            logging.warning(f"It is not {player.name}'s turn.")
            return False
        
        # Process based on action type    
        if action == GameAction.FOLD:
            player.fold()
            logging.info(f"Player {player.name} folded.")
        
        elif action == GameAction.CHECK:
            if self.current_bet > player.current_bet:
                logging.warning(f"Player {player.name} cannot check.")
                return False  # Can't check if there's a bet to call
            player.check()
            logging.info(f"Player {player.name} checked.")
        
        elif action == GameAction.CALL:
            bet_amount = player.call(self.current_bet)
            self.pot += bet_amount
            logging.info(f"Player {player.name} called, betting {bet_amount}.")
        
        elif action == GameAction.RAISE:
            # Ensure minimum raise
            if amount < self.minimum_raise:
                logging.warning(f"Raise amount {amount} is less than minimum raise {self.minimum_raise}.")
                amount = self.minimum_raise
                
            # Calculate actual raise amount (includes matching current bet)
            total_bet = self.current_bet + amount
            
            # Make sure player's total bet is at least that much
            bet_amount = player.raise_bet(total_bet)
            self.pot += bet_amount
            self.current_bet = player.current_bet
            self.minimum_raise = amount  # Set minimum raise for next raise
            logging.info(f"Player {player.name} raised to {self.current_bet}.")
        
        elif action == GameAction.ALL_IN:
            bet_amount = player.all_in()
            self.pot += bet_amount
            logging.info(f"Player {player.name} is all-in with {bet_amount}.")
            
            # Update current bet if this all-in is higher
            if player.current_bet > self.current_bet:
                self.current_bet = player.current_bet
                # Since this is a raise, update minimum raise accordingly
                self.minimum_raise = self.current_bet - player.current_bet
            
            # Check special situations after an all-in
            self._check_all_in_situations(player)
        
        # Update active players list
        self.update_active_players()
        
        # Check if we should move to the next player
        if len(self.active_players) > 1:
            if player in self.active_players:
                # If the player is still active, move to the next player
                self.move_to_next_player()
            else:
                # If current player is no longer active, select the next active player
                self.current_player = next((p for p in self.active_players if not p.is_all_in), self.active_players[0])
        
            # Special case: If all remaining players except one are all-in,
            # we need to complete all betting rounds at once
            active_not_all_in = [p for p in self.active_players if not p.is_all_in and not p.folded]
            if len(active_not_all_in) <= 1:
                logging.info("Only one player not all-in, completing all betting rounds")
                while self.current_state != GameState.SHOWDOWN:
                    # Keep dealing community cards until showdown
                    self.next_round()
        
        logging.info(f"Action processed. Current pot: {self.pot}, current bet: {self.current_bet}")
        return True
    
    def _check_all_in_situations(self, all_in_player):
        """Check if the all-in action should trigger automatic progression"""
        # If only one player is not all-in or folded, complete all betting rounds
        active_not_all_in = [p for p in self.active_players if not p.is_all_in and not p.folded]
        
        if len(active_not_all_in) <= 1:
            logging.info("Only one player not all-in, automatically dealing remaining cards")
            # If we need to move through remaining betting rounds
            if self.current_state != GameState.SHOWDOWN:
                # Create a copy of the active players for later restoration
                original_active_players = list(self.active_players)
                
                # Deal any remaining community cards
                while self.current_state != GameState.SHOWDOWN:
                    self.next_round()
                
                # Restore the active players 
                self.active_players = original_active_players
                
                # Mark this as an automatic showdown
                self.auto_showdown = True

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
            logging.info("Round complete: only one active player")
            return True
            
        active_not_all_in = [p for p in self.active_players if not p.is_all_in]
        if not active_not_all_in:
            logging.info("Round complete: all active players are all-in")
            return True
            
        # Special case: Only one player left who isn't all-in
        if len(active_not_all_in) == 1 and all(p.current_bet >= self.current_bet or p.is_all_in for p in self.active_players):
            logging.info("Round complete: only one player not all-in, and all bets are matched")
            return True
            
        # Normal case: Check if all active players have matched the current bet
        all_matched = all(p.current_bet == self.current_bet or p.is_all_in for p in self.active_players)
        if all_matched:
            logging.info("Round complete: all active players have matched the current bet or are all-in")
        return all_matched
    
    def next_round(self):
        """Move to the next betting round"""
        logging.info(f"Moving from {self.current_state} to next round")
        
        if self.current_state == GameState.PRE_FLOP:
            self.current_state = GameState.FLOP
            # Deal the flop (3 cards)
            self.deal_community_cards(3)
            logging.info("Dealt flop: " + ", ".join(str(card) for card in self.community_cards[-3:]))
        
        elif self.current_state == GameState.FLOP:
            self.current_state = GameState.TURN
            # Deal the turn (1 card)
            self.deal_community_cards(1)
            logging.info(f"Dealt turn: {self.community_cards[-1]}")
        
        elif self.current_state == GameState.TURN:
            self.current_state = GameState.RIVER
            # Deal the river (1 card)
            self.deal_community_cards(1)
            logging.info(f"Dealt river: {self.community_cards[-1]}")
        
        elif self.current_state == GameState.RIVER:
            # After the river, move to showdown
            self.current_state = GameState.SHOWDOWN
            self.showdown()
            logging.info("Moving to showdown")
        
        # Reset betting for the new round
        self.current_bet = 0
        for player in self.active_players:
            player.current_bet = 0
        
        # Reset first player to act - start with player after dealer
        if self.active_players:
            # Find the first active player after the dealer
            start_idx = (self.dealer_index + 1) % len(self.players)
            for i in range(len(self.players)):
                player_idx = (start_idx + i) % len(self.players)
                if self.players[player_idx] in self.active_players:
                    # Get the index in active_players list
                    self.current_player_index = self.active_players.index(self.players[player_idx])
                    self.current_player = self.active_players[self.current_player_index]
                    break
            
        logging.info(f"Current state is now: {self.current_state}")
        return self.current_state
    
    def is_hand_complete(self):
        """Check if the current hand is complete"""
        # Hand is complete when:
        # 1. Only one active player remains, or
        # 2. We've reached showdown
        hand_complete = len(self.active_players) <= 1 or self.current_state == GameState.SHOWDOWN
        logging.info(f"Hand complete check: {hand_complete}, active players: {len(self.active_players)}, state: {self.current_state}")
        return hand_complete
    
    def showdown(self):
        """Handle the showdown phase"""
        logging.info("Entering showdown phase")
        # All remaining players reveal their cards
        for player in self.active_players:
            player.reveal_cards()
            logging.info(f"Player {player.name} reveals: {', '.join(str(card) for card in player.hand)}")
        
        # Hand is complete, will be evaluated by determine_winner
        self.hand_complete = True
    
    def determine_winners(self):
        """
        Returns a list of winner(s) with their hand rankings. If multiple players tie for the best hand,
        they are all returned.
        """
        logging.info("Determining winners...")
        
        # If only one player remains, they are the winner (everyone else folded)
        if len(self.active_players) == 1:
            winner = self.active_players[0]
            winner.hand_name = "Default Win (others folded)"
            self.winning_hand_name = "Default Win (others folded)"
            logging.info(f"Single player remaining: {winner.name} wins by default")
            return [winner]
        
        # Gather non-folded players
        active_players = [p for p in self.players if not p.folded and p.chips > 0]
        if not active_players:
            logging.info("No active players.")
            return []

        best_score = None
        winners = []
        winning_hand_name = ""

        # Evaluate each player's 5-card hand using self.community_cards
        for player in active_players:
            # Make sure player's cards are revealed at showdown
            player.reveal_cards()
            
            # Combine hole cards with community cards
            all_cards = player.hand + self.community_cards
            
            # Evaluate the best 5-card hand
            try:
                hand_value = evaluate_hand(all_cards)
                hand_name = rank_to_string(hand_value)
            except Exception as e:
                logging.error(f"Error evaluating hand for {player.name}: {e}")
                logging.error(f"Cards: {[str(c) for c in all_cards]}")
                continue  # Skip this player if there's an error
            
            logging.info(f"Player {player.name} hand value: {hand_value}, hand name: {hand_name}")
            
            # Store the hand name with the player object
            player.hand_name = hand_name
            
            # Compare with current best hand
            if best_score is None or hand_value > best_score:
                best_score = hand_value
                winners = [player]
                winning_hand_name = hand_name
            elif hand_value == best_score:
                winners.append(player)

        if winners:
            winner_names = ", ".join([winner.name for winner in winners])
            logging.info(f"Winners: {winner_names} with {winning_hand_name}")
        else:
            # Fallback: if we couldn't determine a winner but have active players, pick the first active player
            if active_players:
                winners = [active_players[0]]
                winning_hand_name = "Default Win"
                logging.info(f"No hand evaluation winners, defaulting to: {active_players[0].name}")
        
        # Store the winning hand name in a class attribute
        self.winning_hand_name = winning_hand_name
        return winners

    def finalize_hand(self):
        """
        Splits the pot among all winners returned by determine_winners().
        Enhanced to handle side pots and all-in situations.
        """
        logging.info("Finalizing hand...")
        winners = self.determine_winners()
        if not winners:
            logging.warning("No winners to finalize - this should not happen!")
            return

        # Special handling for all-in situations with side pots
        side_pots = self._calculate_side_pots()
        
        if side_pots:
            logging.info(f"Calculating split with side pots: {side_pots}")
            self._distribute_side_pots(side_pots, winners)
        else:
            # Regular pot splitting for non-all-in situations
            split_amount = self.pot // len(winners)
            logging.info(f"Splitting pot of {self.pot} among {len(winners)} winners, each receiving {split_amount}")
            
            for winner in winners:
                winner.collect_winnings(split_amount)
                logging.info(f"Player {winner.name} collected {split_amount} with {winner.hand_name}")
            
            # Handle any remainder
            remainder = self.pot % len(winners)
            if remainder > 0:
                winners[0].collect_winnings(remainder)
                logging.info(f"Player {winners[0].name} collected remainder of {remainder}")
        
        # Reset the pot
        self.pot = 0
        self.hand_complete = True
        logging.info("Hand finalized.")

    def _calculate_side_pots(self):
        """
        Calculate side pots for all-in situations.
        Returns a list of (pot_amount, eligible_players) tuples.
        """
        if not any(p.is_all_in for p in self.active_players):
            return []  # No all-in players, no side pots
            
        # Sort players by their stake amount
        players_by_stake = sorted(
            [p for p in self.active_players if not p.folded],
            key=lambda player: player.stake
        )
        
        if not players_by_stake:
            return []
            
        side_pots = []
        prev_stake = 0
        
        # Calculate each side pot
        for i, current_player in enumerate(players_by_stake):
            if current_player.is_all_in:
                current_stake = current_player.stake
                # Calculate pot size for this stake level
                pot_size = 0
                for player in self.active_players:
                    contribution = min(current_stake, player.stake) - prev_stake
                    if contribution > 0:
                        pot_size += contribution
                
                # Eligible players are those who contributed to this pot
                eligible_players = [p for p in self.active_players 
                                   if not p.folded and p.stake >= current_stake]
                
                side_pots.append((pot_size, eligible_players))
                prev_stake = current_stake
        
        # If there's a main pot left (players who weren't all in)
        if prev_stake < max(p.stake for p in self.active_players if not p.folded):
            pot_size = 0
            for player in self.active_players:
                contribution = max(0, player.stake - prev_stake)
                pot_size += contribution
                
            eligible_players = [p for p in self.active_players 
                               if not p.folded and p.stake > prev_stake]
            
            side_pots.append((pot_size, eligible_players))
        
        return side_pots

    def _distribute_side_pots(self, side_pots, all_winners):
        """
        Distribute side pots to eligible winners.
        """
        total_distributed = 0
        
        for pot_amount, eligible_players in side_pots:
            # Find winners for this pot
            pot_winners = [w for w in all_winners if w in eligible_players]
            
            if pot_winners:
                split_amount = pot_amount // len(pot_winners)
                remainder = pot_amount % len(pot_winners)
                
                for winner in pot_winners:
                    winner.collect_winnings(split_amount)
                    logging.info(f"Player {winner.name} collected {split_amount} from side pot with {winner.hand_name}")
                    total_distributed += split_amount
                
                # Give remainder to first winner
                if remainder > 0:
                    pot_winners[0].collect_winnings(remainder)
                    logging.info(f"Player {pot_winners[0].name} collected remainder of {remainder}")
                    total_distributed += remainder
            else:
                # Edge case: no eligible winners for this pot
                # This could happen if all eligible players folded
                logging.warning(f"No eligible winners for side pot of {pot_amount}")
        
        if total_distributed != self.pot:
            logging.warning(f"Distribution mismatch: {total_distributed} distributed from pot of {self.pot}")

    def can_check(self):
        """Check if the current player can check"""
        return self.current_player.current_bet >= self.current_bet
    
    def can_call(self):
        """Check if the current player can call"""
        return self.current_bet > self.current_player.current_bet
    
    def update_active_players(self):
        """Update the list of active players (not folded)"""
        self.active_players = [p for p in self.players if not p.folded]
    
    # Helper methods for action validation and state queries
    def get_call_amount(self, player):
        """Amount needed for player to call the current bet"""
        return max(0, self.current_bet - player.current_bet)

    def can_check(self, player):
        """Check if player can check (no bet to call)"""
        return player.current_bet >= self.current_bet

    def can_call(self, player):
        """Check if player can call"""
        return (self.current_bet > player.current_bet) and (player.chips > 0)

    def can_raise(self, player):
        """Check if player can raise"""
        # Player needs enough chips to make at least minimum raise
        call_amount = self.get_call_amount(player)
        return player.chips >= call_amount + self.minimum_raise

    def process_round(self):
        """Process the current round until completion"""
        logging.info(f"Processing round: {self.current_state}")
        
        # Don't process if the hand is already complete
        if self.is_hand_complete():
            logging.info("Hand is already complete, not processing round")
            return
        
        # Process AI actions until the round is complete or human player's turn
        round_in_progress = True
        while round_in_progress and len(self.active_players) > 1:
            # If it's human player's turn, let the UI handle it
            if self.current_player == self.human_player:
                logging.info("Human player's turn, stopping round processing")
                break
            
            # AI players take their actions
            if hasattr(self.current_player, 'decide_action'):
                logging.info(f"AI player {self.current_player.name} is deciding action")
                action, amount = self.current_player.decide_action(self.get_game_state())
                self.process_action(self.current_player, action, amount)
                
                # Check if round is complete after this action
                if self.is_round_complete():
                    logging.info("Round is complete after AI action")
                    round_in_progress = False
            else:
                # Skip players without decide_action method
                self.move_to_next_player()
        
        # If round complete but hand not over, move to next round
        if self.is_round_complete() and not self.is_hand_complete():
            logging.info("Round is complete, moving to next round")
            self.next_round()
            
            # Process the new round if no human player is active
            if not self.human_player or not self.human_player.is_active or self.human_player not in self.active_players:
                logging.info("No active human player, continuing to process rounds")
                self.process_round()