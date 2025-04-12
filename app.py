import streamlit as st
import time
import random
import json
import os
from PIL import Image
from streamlit_option_menu import option_menu
from streamlit_autorefresh import st_autorefresh
#from streamlit_confetti import st_confetti
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# Import our poker logic modules
from poker.cards import Deck, Hand, evaluate_hand, rank_to_string
from poker.player import Player
from poker.game import PokerGame, GameState, GameAction
from poker.ai import AIPlayer

# App configuration
st.set_page_config(
    page_title="Interactive Poker Game",
    page_icon="♠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Define styles
st.markdown(
    """
    <style>
    :root {
        --primary-color: #1f3b4d;
        --secondary-color: #2a9d8f;
        --accent-color: #e9c46a;
        --dark-bg: #264653;
        --light-bg: #f4f1de;
        --text-light: #f2f2f2;
        --text-dark: #242424;
    }

    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: var(--dark-bg);
        color: var(--text-light);
    }

    .header {
        background-color: var(--primary-color);
        color: white;
        padding: 1rem;
        text-align: center;
    }

    .poker-table {
        background-color: #2f7561;
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem auto;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
    }

    .card-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 10px;
        min-height: 110px;
    }

    .chip {
        display: inline-block;
        width: 60px;
        height: 60px;
        border-radius: 30px;
        text-align: center;
        line-height: 60px;
        margin: 0 3px;
        font-weight: bold;
        box-shadow: 0 3px 5px rgba(0,0,0,0.5);
    }

    .action-buttons button {
        margin: 0.5rem;
        padding: 0.6rem 1.2rem;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        cursor: pointer;
    }

    .action-buttons .fold {
        background-color: #e76f51;
        color: white;
    }

    .action-buttons .check {
        background-color: #2a9d8f;
        color: white;
    }

    .action-buttons .call {
        background-color: #e9c46a;
        color: var(--text-dark);
    }

    .action-buttons .raise {
        background-color: #f4a261;
        color: var(--text-dark);
    }

    .action-buttons .all-in {
        background-color: #e63946;
        color: white;
    }
    
    .player-active {
        border: 2px solid var(--accent-color);
        padding: 10px;
        border-radius: 10px;
    }
    
    .winner {
        background-color: rgba(233, 196, 106, 0.3);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(233, 196, 106, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(233, 196, 106, 0); }
        100% { box-shadow: 0 0 0 0 rgba(233, 196, 106, 0); }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize session state if needed
if "game" not in st.session_state:
    st.session_state.game = None
if "players" not in st.session_state:
    st.session_state.players = []
if "current_round" not in st.session_state:
    st.session_state.current_round = "Pre-Flop"
if "pot" not in st.session_state:
    st.session_state.pot = 0
if "winner" not in st.session_state:
    st.session_state.winner = None
if "show_confetti" not in st.session_state:
    st.session_state.show_confetti = False
if "game_history" not in st.session_state:
    st.session_state.game_history = []

# Header
st.markdown("<div class='header'><h1>Texas Hold'em Poker</h1></div>", unsafe_allow_html=True)

# Sidebar Navigation
with st.sidebar:
    selected = option_menu(
        "Game Menu", 
        ["Play", "Settings", "History", "Help"],
        icons=['controller', 'gear', 'clock-history', 'question-circle'],
        menu_icon="suit-spade", 
        default_index=0
    )
    
    # Game settings in sidebar
    if selected == "Settings":
        st.header("Game Settings")
        
        # Theme selector
        theme = st.selectbox("Theme", ["Dark Mode", "Light Mode"])
        
        # AI difficulty
        ai_difficulty = st.select_slider(
            "AI Difficulty",
            options=["Beginner", "Intermediate", "Advanced", "Expert"]
        )
        
        # Starting chips
        starting_chips = st.number_input("Starting Chips", min_value=100, max_value=10000, value=1000, step=100)
        
        # Sound effects toggle
        sound_effects = st.toggle("Sound Effects", value=True)
        
        # Save settings button
        if st.button("Save Settings"):
            st.success("Settings saved!")

    elif selected == "History":
        st.header("Game History")
        
        if not st.session_state.game_history:
            st.info("No games played yet.")
        else:
            history_df = pd.DataFrame(st.session_state.game_history)
            st.dataframe(history_df)
            
            # Simple stats
            st.subheader("Statistics")
            wins = sum(1 for game in st.session_state.game_history if game.get("result") == "win")
            losses = sum(1 for game in st.session_state.game_history if game.get("result") == "loss")
            
            col1, col2 = st.columns(2)
            col1.metric("Wins", wins)
            col2.metric("Losses", losses)
            
            # Win/Loss chart
            fig = go.Figure(data=[
                go.Bar(name="Games", x=["Wins", "Losses"], y=[wins, losses])
            ])
            fig.update_layout(title="Win/Loss Record")
            st.plotly_chart(fig)
            
    elif selected == "Help":
        st.header("How to Play")
        st.markdown("""
        ### Texas Hold'em Rules
        
        1. **Setup**: Each player is dealt two private cards (hole cards)
        2. **Betting Rounds**: Players bet in clockwise order
        3. **Community Cards**: Five community cards are dealt in three stages:
           - **The Flop**: First three cards
           - **The Turn**: Fourth card
           - **The River**: Fifth card
        4. **Showdown**: Players make their best five-card hand using any combination of their hole cards and the community cards
        5. **Winner**: The player with the best hand wins the pot
        
        ### Hand Rankings (Highest to Lowest)
        
        1. Royal Flush
        2. Straight Flush
        3. Four of a Kind
        4. Full House
        5. Flush
        6. Straight
        7. Three of a Kind
        8. Two Pair
        9. One Pair
        10. High Card
        """)

# Main game area (display only if "Play" is selected)
if selected == "Play":
    # Function to display cards using inline styles
    def display_card(card_code):
        if not card_code or len(card_code) < 2:
            # Return HTML for a face-down card
            return """
            <div style="
                display: inline-block;
                width: 70px;
                height: 100px;
                background-image: linear-gradient(to bottom right, #1a4536, #2f7561);
                border: 1px solid #aaa;
                border-radius: 5px;
                margin: 0 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                vertical-align: top;
            "></div>
            """

        rank = card_code[0]
        suit = card_code[1]

        suit_symbol = {'h': '♥', 'd': '♦', 'c': '♣', 's': '♠'}.get(suit, '?')
        color = "red" if suit in ['h', 'd'] else "black"

        # Use inline styles for better control within Streamlit markdown
        return f"""
        <div style="
            display: inline-block;
            width: 70px;
            height: 100px;
            background-color: white;
            border: 1px solid #ccc;
            border-radius: 5px;
            margin: 0 5px;
            padding: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            position: relative;
            color: {color};
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 16px;
            font-weight: bold;
            vertical-align: top;
        ">
            <div style="position: absolute; top: 5px; left: 5px;">{rank}</div>
            <div style="position: absolute; top: 5px; right: 5px;">{suit_symbol}</div>
            <div style="
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                font-size: 30px;
            ">{suit_symbol}</div>
            <div style="position: absolute; bottom: 5px; left: 5px; transform: rotate(180deg);">{suit_symbol}</div>
            <div style="position: absolute; bottom: 5px; right: 5px; transform: rotate(180deg);">{rank}</div>
        </div>
        """

    # Function to display chips
    def display_chip(value):
        color = {
            5000: "black",
            1000: "purple",
            500: "blue",
            100: "green",
            25: "red",
            5: "white"
        }.get(value, "gray")
        
        text_color = "white" if color in ["black", "blue", "purple", "green", "red"] else "black"
        
        return f"""
        <div class="chip" style="background-color: {color}; color: {text_color};">
            ${value}
        </div>
        """

    # Game initialization
    if st.session_state.game is None:
        # Start new game button
        col1, col2 = st.columns([3, 1])
        
        with col2:
            num_opponents = st.selectbox("Number of Opponents", [1, 2, 3, 4, 5], index=2)
            starting_chips = st.number_input("Starting Chips", min_value=100, max_value=10000, value=1000, step=100)
            
            if st.button("Start New Game", use_container_width=True):
                # Show loading animation
                with st.spinner("🎲 Setting up the poker table..."):
                    # Create player
                    human_player = Player("You", starting_chips)
                    
                    # Create AI opponents
                    ai_players = [
                        AIPlayer(f"AI Player {i+1}", starting_chips, difficulty="Medium") 
                        for i in range(num_opponents)
                    ]
                    
                    # Initialize all players
                    all_players = [human_player] + ai_players
                    st.session_state.players = all_players
                    
                    # Create game
                    st.session_state.game = PokerGame(all_players)
                    st.session_state.game.start_game()
                    st.session_state.pot = 0
                    st.session_state.current_round = "Pre-Flop"
                    
                    # Small delay to show the loading message
                    time.sleep(0.8)
                    
                st.rerun()
        
        with col1:
            st.markdown("""
            ### Welcome to Texas Hold'em Poker!
            
            Start a new game by selecting the number of opponents and your starting chips.
            
            Each player will be dealt two cards, and you'll play through betting rounds as community cards are revealed.
            The player with the best five-card hand at the showdown wins!
            """)
            
            # Show sample cards as decoration
            welcome_cards_html = """
            <div style="text-align: center; margin: 30px;">
            """+display_card("As")+display_card("Kh")+display_card("Qd")+display_card("Jc")+display_card("Ts")+"""
            </div>
            """
            st.html(welcome_cards_html)
    else:
        # Game is running - display game state
        game = st.session_state.game
        
        # Auto-refresh to simulate game updates - every 3 seconds if it's AI's turn
        if game.current_player and game.current_player.name != "You" and not game.is_hand_complete():
            st_autorefresh(interval=3000, key="ai_refresh")
        
        # Check if we need to show the winning animation
        if st.session_state.show_confetti:
            #st_confetti()
            if st.session_state.winner:
                st.success(f"🎉 {st.session_state.winner.name} wins the pot!")
            else:
                st.info("The hand is complete. No winner determined.")
            st.session_state.show_confetti = False
            
        # Game table container
        st.markdown("<div class='poker-table'>", unsafe_allow_html=True)
        
        # Game info
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.subheader(f"Round: {game.current_state}")
            # Update the session state round
            st.session_state.current_round = game.current_state
        with col2:
            st.subheader(f"Pot: ${game.pot}")
            # Update the session state pot
            st.session_state.pot = game.pot
        with col3:
            if st.button("Fold Hand", key="fold_hand"):
                # End the current hand
                if game.human_player and game.human_player in game.active_players:
                    game.process_action(game.human_player, "fold")
                    
                # Update game state
                game.process_round()
                st.rerun()
            
        # Community cards area
        st.subheader("Community Cards")
        community_cards_html = "<div class='card-container'>"
        
        # Get community cards from game state
        community_cards = game.get_community_cards() if hasattr(game, 'get_community_cards') else []
        
        # Display community cards or placeholders
        num_displayed = 0
        if community_cards:
            for card in community_cards:
                community_cards_html += display_card(str(card))
                num_displayed += 1
                
        for _ in range(5 - num_displayed):
            community_cards_html += display_card(None)
            
        community_cards_html += "</div>"
        st.html(community_cards_html)
        
        # Player sections
        st.subheader("Players")
        
        # Arrange players in a grid
        num_players = len(st.session_state.players)
        cols = st.columns(num_players)
        
        for i, player in enumerate(st.session_state.players):
            with cols[i]:
                # Determine if this player is active
                is_active = game.current_player == player if hasattr(game, 'current_player') else False
                is_winner = st.session_state.winner == player if st.session_state.winner else False
                is_folded = getattr(player, 'is_folded', False)
                
                player_class = "player-active" if is_active and not is_folded else ""
                player_class += " winner" if is_winner else ""
                player_class += " player-folded" if is_folded else ""
                
                st.markdown(f"<div class='player-box {player_class}' style='padding: 10px; border-radius: 8px; background-color: rgba(0,0,0,0.1); margin-bottom: 10px; {'opacity: 0.6;' if is_folded else ''}'>", unsafe_allow_html=True)
                
                # Player name and chips
                st.markdown(f"<h5>{player.name}</h5>", unsafe_allow_html=True)
                st.markdown(f"Chips: ${player.chips}")
                
                # Player cards
                player_cards_html = "<div class='card-container'>"
                
                # Show player's cards
                player_cards = player.hand if hasattr(player, 'hand') else []

                # Only show AI player cards at showdown or when they've been explicitly revealed
                # Human player's cards are always visible to them
                show_cards = (player.name == "You" or  # Always show the human player's cards
                              getattr(player, 'revealed', False) or  # Show revealed cards
                              (game.current_state == GameState.SHOWDOWN) or  # Show all cards at showdown
                              (getattr(player, 'is_active', False) and game.is_hand_complete()))  # Show active player cards when hand is complete

                if show_cards and not is_folded:
                    if isinstance(player_cards, list) and all(isinstance(c, object) for c in player_cards):
                        for card in player_cards:
                            player_cards_html += display_card(str(card))
                        for _ in range(2 - len(player_cards)):
                            player_cards_html += display_card(None)
                    else:
                        player_cards_html += display_card(None)
                        player_cards_html += display_card(None)
                else:
                    player_cards_html += display_card(None)
                    player_cards_html += display_card(None)
                    
                player_cards_html += "</div>"
                st.html(player_cards_html)
                
                # Show last action or folded status
                if is_folded:
                    st.markdown("**Folded**")
                elif hasattr(player, 'last_action') and player.last_action:
                    st.markdown(f"**Action:** {player.last_action}")
                
                # Player actions - only show for human player when it's their turn
                if player.name == "You" and is_active and not is_folded:
                    st.markdown("<div class='action-buttons'>", unsafe_allow_html=True)
                    
                    action_cols = st.columns(3)
                    
                    # Fixed method calls - pass the player parameter
                    can_check = game.can_check(player) if hasattr(game, 'can_check') else False
                    can_call = game.can_call(player) if hasattr(game, 'can_call') else False
                    call_amount = game.get_call_amount(player) if hasattr(game, 'get_call_amount') else 0
                    can_raise = game.can_raise(player) if hasattr(game, 'can_raise') else True
                    
                    with action_cols[0]:
                        if st.button("Fold", key=f"fold_{i}", use_container_width=True):
                            # Process action and check if round is complete
                            if game.process_action(player, "fold"):
                                # Only move to next round if this completes the current round
                                if game.is_round_complete() and not game.is_hand_complete():
                                    with st.spinner("Moving to next round..."):
                                        game.next_round()
                                elif game.is_hand_complete():
                                    # If hand is complete, make sure winners are determined
                                    game.determine_winners()
                                st.rerun()
                                
                        if st.button("Check", key=f"check_{i}", disabled=not can_check, use_container_width=True):
                            if game.process_action(player, "check"):
                                # Check if the round is complete after this check
                                if game.is_round_complete() and not game.is_hand_complete():
                                    with st.spinner("Moving to next round..."):
                                        next_state = game.next_round()
                                        st.success(f"Moving to {next_state} round")
                                st.rerun()
                    
                    with action_cols[1]:
                        if st.button(f"Call ${call_amount}", key=f"call_{i}", disabled=not can_call or call_amount <= 0, use_container_width=True):
                            if game.process_action(player, GameAction.CALL):
                                if game.is_round_complete() and not game.is_hand_complete():
                                    with st.spinner("Moving to next round..."):
                                        next_state = game.next_round()
                                        st.success(f"Moving to {next_state} round")
                                st.rerun()
                                
                        if st.button("All In", key=f"all_in_{i}", type="primary", use_container_width=True):
                            # Process all-in action
                            result = game.process_action(player, GameAction.ALL_IN)
                            if result:
                                with st.spinner("Going all-in..."):
                                    # When player goes all-in, we should automatically deal all remaining cards
                                    # and move to showdown if the round is complete
                                    if game.is_round_complete():
                                        st.success("All-in! Dealing remaining cards...")
                                        # Continue dealing cards until showdown
                                        while game.current_state != GameState.SHOWDOWN and not game.is_hand_complete():
                                            game.next_round()
                                    
                                    # If hand is complete, determine winner
                                    if game.is_hand_complete():
                                        winners = game.determine_winners()
                                        st.session_state.winner = winners[0] if len(winners) == 1 else "Tie"
                                        if len(winners) > 1:
                                            st.session_state.winners = winners
                                        game.finalize_hand()
                            st.rerun()
                    
                    with action_cols[2]:
                        if can_raise:
                            min_raise = game.minimum_raise if hasattr(game, 'minimum_raise') else 10
                            max_raise = player.chips
                            if min_raise > max_raise:
                                min_raise = max_raise
                            
                            # Calculate a better default raise amount based on pot size and current bet
                            default_raise = min(max(min_raise, int(game.pot * 0.5)), max_raise)
                            
                            if max_raise >= min_raise:
                                raise_amount = st.number_input("Raise By", 
                                                            min_value=min_raise, 
                                                            max_value=max_raise,
                                                            value=default_raise,
                                                            step=10,
                                                            key=f"raise_amount_{i}",
                                                            help="Amount to raise beyond the current bet")
                                
                                if st.button("Raise", key=f"raise_{i}", use_container_width=True, disabled=(raise_amount > max_raise)):
                                    # Process the raise action
                                    if game.process_action(player, GameAction.RAISE, raise_amount):
                                        # Update the pot amount in session state
                                        st.session_state.pot = game.pot
                                        
                                        # Check if round complete after raise
                                        if game.is_round_complete() and not game.is_hand_complete():
                                            with st.spinner("Moving to next round..."):
                                                next_state = game.next_round()
                                                st.success(f"Moving to {next_state} round")
                                        
                                        # Small delay to allow state update
                                        time.sleep(0.2)
                                        st.rerun()
                            else:
                                st.markdown("<small>Cannot raise - insufficient chips</small>", unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
            
        # Process AI actions if it's their turn
        if game.current_player and game.current_player != game.human_player and not game.is_hand_complete():
            with st.spinner(f"{game.current_player.name} is thinking..."):
                # Small delay to make AI seem more realistic
                time.sleep(0.3)
                
                try:
                    # Get AI action
                    action, amount = game.current_player.decide_action(
                        game.get_game_state() if hasattr(game, 'get_game_state') else {}
                    )
                    
                    # Process the action
                    result = game.process_action(game.current_player, action, amount)
                    
                    # After AI action, check if round is complete
                    if result and game.is_round_complete() and not game.is_hand_complete():
                        with st.spinner("🃏 Dealing community cards for next round..."):
                            # This will reveal the appropriate community cards
                            next_round = game.next_round()
                            st.info(f"Moving to {next_round} round")
                    
                    # If it's still not the human player's turn, continue processing
                    if game.current_player and game.current_player != game.human_player and not game.is_hand_complete():
                        game.process_round()
                except Exception as e:
                    st.error(f"Error during AI action: {e}")
                    import traceback
                    st.error(traceback.format_exc())
            
            # Always rerun to update the UI
            st.rerun()
        
        # Check for hand completion
        if game.is_hand_complete():
            # Only handle hand completion if not already handled
            if not st.session_state.winner:
                with st.spinner("Determining the winner..."):
                    # Get all winners
                    winners = game.determine_winners()
                    
                    # Update session state
                    if winners:
                        if len(winners) == 1:
                            st.session_state.winner = winners[0]
                            st.session_state.winning_hand_name = getattr(winners[0], 'hand_name', 'Unknown Hand')
                        else:
                            # Handle multiple winners
                            st.session_state.winner = "Tie"
                            st.session_state.winners = winners
                            st.session_state.winning_hand_name = getattr(game, 'winning_hand_name', 'Unknown Hand')
                    else:
                        # Fallback in case no winners were determined
                        if len(game.active_players) > 0:
                            st.session_state.winner = game.active_players[0]
                            st.session_state.winning_hand_name = "Default Win"
                    
                    # Show confetti animation
                    st.session_state.show_confetti = bool(winners)
                    
                    # Finalize the hand to distribute the pot
                    game.finalize_hand()
                    
                    # Record game history
                    game_result = "win" if st.session_state.winner == game.human_player else "loss"
                    game_data = {
                        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "result": game_result,
                        "pot_size": st.session_state.pot,
                        "num_players": len(st.session_state.players),
                        "winner": st.session_state.winner.name if hasattr(st.session_state.winner, 'name') else "Tie"
                    }
                    st.session_state.game_history.append(game_data)
            
            # Show appropriate winner message
            if st.session_state.winner == "Tie":
                winner_names = ", ".join(w.name for w in st.session_state.winners)
                st.success(f"🏆 It's a tie! Players {winner_names} split the pot of ${st.session_state.pot} with {st.session_state.winning_hand_name}!")
            elif st.session_state.winner:
                st.success(f"🏆 {st.session_state.winner.name} wins the pot of ${st.session_state.pot} with {st.session_state.winning_hand_name}!")
            else:
                st.info("Hand complete with no winner.")

            # Next hand button
            if st.button("Next Hand", type="primary", key="next_hand_button", use_container_width=True):
                with st.spinner("🎲 Dealing new hand..."):
                    # Reset session state
                    st.session_state.winner = None
                    if "winners" in st.session_state:
                        del st.session_state.winners
                    st.session_state.show_confetti = False
                    
                    # Start a new hand
                    game.start_new_hand()
                    
                    # Small delay to show spinner
                    time.sleep(0.5)
                
                # Rerun to update UI with new hand
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
            
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("End Game", type="secondary"):
                st.session_state.game = None
                st.session_state.players = []
                st.session_state.winner = None
                st.rerun()
                
        with col2:
            with st.expander("Hand Rankings"):
                st.markdown("""
                1. **Royal Flush**: A, K, Q, J, 10, all the same suit
                2. **Straight Flush**: Five cards in a sequence, all in the same suit
                3. **Four of a Kind**: Four cards of the same rank
                4. **Full House**: Three of a kind with a pair
                5. **Flush**: Any five cards of the same suit, not in sequence
                6. **Straight**: Five cards in a sequence, not of the same suit
                7. **Three of a Kind**: Three cards of the same rank
                8. **Two Pair**: Two pairs of cards of the same rank
                9. **Pair**: Two cards of the same rank
                10. **High Card**: When no other hand is made, highest card plays
                """)