import random
from .player import Player
from .cards import evaluate_hand

class AIPlayer(Player):
    """AI Poker Player"""
    
    def __init__(self, name, chips=1000, difficulty="Medium"):
        super().__init__(name, chips)
        self.difficulty = difficulty
        self.aggression = self._set_aggression()
        self.bluff_factor = self._set_bluff_factor()
    
    def _set_aggression(self):
        """Set aggression level based on difficulty"""
        if self.difficulty == "Easy":
            return random.uniform(0.1, 0.3)
        elif self.difficulty == "Medium":
            return random.uniform(0.3, 0.6)
        elif self.difficulty == "Hard":
            return random.uniform(0.6, 0.8)
        else:  # Expert
            return random.uniform(0.7, 0.9)
    
    def _set_bluff_factor(self):
        """Set bluff factor based on difficulty"""
        if self.difficulty == "Easy":
            return random.uniform(0.05, 0.15)
        elif self.difficulty == "Medium":
            return random.uniform(0.15, 0.25)
        elif self.difficulty == "Hard":
            return random.uniform(0.25, 0.40)
        else:  # Expert
            return random.uniform(0.30, 0.50)
    
    def decide_action(self, game_state):
        """Decide AI action based on game state and difficulty"""
        # Extract relevant information from game state
        pot = game_state.get('pot', 0)
        current_bet = game_state.get('current_bet', 0)
        community_cards = game_state.get('community_cards', [])
        
        # Calculate how much to call
        to_call = current_bet - self.current_bet
        
        # Calculate pot odds (ratio of call amount to potential win)
        pot_odds = to_call / (pot + to_call) if to_call > 0 else 0
        
        # Evaluate hand strength (0 to 1)
        hand_strength = self._evaluate_hand_strength(community_cards)
        
        # Position advantage (being dealer or close to dealer is advantageous)
        position_factor = game_state.get('position_advantage', 0.0)
        
        # Evaluate opponents
        opponent_reads = self._evaluate_opponents(game_state)
        
        # Calculate expected value of each possible action
        ev_fold = 0  # EV of folding is always 0
        ev_call = self._calculate_call_ev(hand_strength, pot_odds, pot, to_call)
        ev_raise = self._calculate_raise_ev(hand_strength, pot, to_call, opponent_reads)
        ev_check = hand_strength * 0.7 if to_call == 0 else -1
        
        # Adjust EVs based on position and game state
        round_factor = 1.0
        if game_state.get('betting_round') == 'pre-flop':
            round_factor = 1.2  # Slightly more aggressive pre-flop
        elif game_state.get('betting_round') == 'river':
            round_factor = 0.9  # Slightly more cautious on river
        
        ev_call *= (1 + position_factor)
        ev_raise *= (1 + position_factor) * round_factor
        
        # Apply difficulty-based randomness
        randomness = 0.5 - self.difficulty_level * 0.1  # Lower difficulty = more randomness
        ev_call *= random.uniform(1 - randomness, 1 + randomness)
        ev_raise *= random.uniform(1 - randomness, 1 + randomness)
        ev_check *= random.uniform(1 - randomness, 1 + randomness)
        
        # Decision logic
        if to_call == 0:  # Can check
            # Sometimes bluff
            if random.random() < self.bluff_factor and hand_strength < 0.3:
                raise_amount = int(min(self.chips, pot * random.uniform(0.1, 0.3)))
                return "raise", max(10, raise_amount)
                
            if ev_raise > ev_check and random.random() < self.aggression:
                # Raise proportional to hand strength and pot
                raise_factor = hand_strength * (0.5 + self.aggression * 0.5)
                raise_amount = int(min(self.chips, pot * raise_factor))
                return "raise", max(10, raise_amount)
            else:
                return "check", 0
        else:  # There's a bet to call
            # Calculate whether all-in makes sense
            all_in_threshold = 0.85 - (0.1 * (1 - self.aggression))
            
            # Go all-in with very strong hands or as a calculated risk
            if (hand_strength > all_in_threshold and self.chips <= to_call * 3) or \
               (hand_strength > 0.92 and random.random() < self.aggression * 1.5):
                return "all_in", 0
            
            # Determine best action based on EV
            if ev_fold >= ev_call and ev_fold >= ev_raise:
                # Only fold if the EV of calling is significantly negative
                # or if the call is too expensive relative to hand strength
                if ev_call < -0.1 * pot or (to_call > self.chips * 0.2 and hand_strength < 0.4):
                    return "fold", 0
                # Otherwise call as a defensive play
                return "call", 0
            elif ev_call >= ev_raise:
                if to_call > self.chips * 0.4 and hand_strength < 0.5:
                    # Too expensive for a mediocre hand
                    return "fold", 0
                return "call", 0
            else:
                # Calculate optimal raise amount
                if hand_strength > 0.7:
                    # Big hand, bigger raise
                    raise_factor = 0.3 + (hand_strength - 0.7) * 2
                else:
                    # Medium hand or bluff, smaller raise
                    raise_factor = 0.1 + hand_strength * 0.2
                
                # Apply aggression multiplier
                raise_factor *= (0.5 + self.aggression)
                
                # Calculate actual raise amount
                raise_amount = int(min(self.chips, (pot + to_call) * raise_factor))
                
                # Make sure it's a valid raise (greater than minimum)
                min_raise = game_state.get('min_raise', to_call + 10)
                if raise_amount <= min_raise:
                    return "call", 0
                
                return "raise", raise_amount

    def _calculate_call_ev(self, hand_strength, pot_odds, pot, to_call):
        """Calculate expected value of calling"""
        if to_call == 0:
            return 0  # Can't call if there's nothing to call
            
        # Basic EV calculation: win_probability * pot - call_amount
        win_probability = hand_strength  # Simplified - assuming hand strength = win probability
        ev = win_probability * pot - to_call
        
        # Adjust for pot odds
        if win_probability > pot_odds:
            return ev + (win_probability - pot_odds) * pot * 0.5
        else:
            return ev

    def _calculate_raise_ev(self, hand_strength, pot, to_call, opponent_reads):
        """Calculate expected value of raising"""
        # Base EV on the assumption that raising has 3 possible outcomes:
        # 1. Everyone folds (win pot)
        # 2. Get called and win (win bigger pot)
        # 3. Get called and lose (lose chips)
        
        fold_probability = 0.3 * (1 - hand_strength)  # Better hand = less likely opponents fold
        
        # Adjust based on opponent tendencies
        if opponent_reads.get('tight_players', 0) > 0:
            fold_probability += 0.1
        if opponent_reads.get('aggressive_players', 0) > 0:
            fold_probability -= 0.1
            
        # Calculate EV for fold scenario
        ev_fold_scenario = fold_probability * pot
        
        # Calculate EV for call scenarios
        call_probability = 1 - fold_probability
        win_probability = hand_strength
        
        ev_call_win = win_probability * call_probability * (pot + to_call * 2)
        ev_call_lose = (1 - win_probability) * call_probability * (to_call * -1)
        
        return ev_fold_scenario + ev_call_win + ev_call_lose
        
    def _evaluate_opponents(self, game_state):
        """Analyze opponents based on observed behavior"""
        result = {
            'tight_players': 0,     # Players who fold often
            'loose_players': 0,     # Players who call/raise often
            'aggressive_players': 0, # Players who raise often
            'passive_players': 0    # Players who check/call often
        }
        
        # Process opponent actions if available
        if 'opponents' in game_state:
            for opponent in game_state.get('opponents', []):
                actions = opponent.get('actions', [])
                if not actions:
                    continue
                
                # Count action frequencies
                fold_count = actions.count('fold')
                call_count = actions.count('call')
                raise_count = actions.count('raise')
                check_count = actions.count('check')
                total = len(actions)
                
                if total > 2:  # Only analyze if we have enough data
                    if fold_count / total > 0.4:
                        result['tight_players'] += 1
                    else:
                        result['loose_players'] += 1
                        
                    if (raise_count / total) > 0.3:
                        result['aggressive_players'] += 1
                    else:
                        result['passive_players'] += 1
                        
        return result
        
    @property
    def difficulty_level(self):
        """Return numeric difficulty level from 0 to 1"""
        return {
            "Easy": 0.2,
            "Medium": 0.5,
            "Hard": 0.8,
            "Expert": 1.0
        }.get(self.difficulty, 0.5)
    
    def _evaluate_hand_strength(self, community_cards):
        """Evaluate the strength of the current hand (0 to 1)"""
        # If no community cards, evaluate based on hole cards
        if not community_cards:
            # Evaluate pocket pairs
            if len(self.hand) == 2 and self.hand[0].rank == self.hand[1].rank:
                rank_value = self.hand[0].rank_value
                # Higher pairs are stronger
                return 0.5 + (rank_value / 25.0)
                
            # Evaluate connected cards (straight potential)
            elif len(self.hand) == 2:
                rank_diff = abs(self.hand[0].rank_value - self.hand[1].rank_value)
                if rank_diff <= 1:  # Connected
                    high_card = max(self.hand[0].rank_value, self.hand[1].rank_value)
                    return 0.3 + (high_card / 40.0)
                    
                # Evaluate suited cards (flush potential)
                if self.hand[0].suit == self.hand[1].suit:
                    high_card = max(self.hand[0].rank_value, self.hand[1].rank_value)
                    return 0.25 + (high_card / 50.0)
                
                # High cards
                high_card = max(self.hand[0].rank_value, self.hand[1].rank_value)
                if high_card >= 10:  # 10, J, Q, K, A
                    return 0.2 + ((high_card - 10) / 25.0)
            
            # Low, unconnected, unsuited cards
            return 0.1
        
        # With community cards, do a proper evaluation
        all_cards = self.hand + community_cards
        
        # Get the numerical rank value (0-9)
        hand_value = evaluate_hand(all_cards)
        hand_rank = hand_value[0]
        
        # Scale from 0 to 1 based on hand rank
        # High Card (0) → 0.1 to 0.2
        # Pair (1) → 0.2 to 0.3
        # Two Pair (2) → 0.3 to 0.4
        # etc.
        base_strength = min(0.9, (hand_rank + 1) / 10.0)
        
        # Add a small factor based on kickers
        kicker_factor = sum(hand_value[1][:3]) / 100.0 if hand_value[1] else 0
        
        return base_strength + kicker_factor