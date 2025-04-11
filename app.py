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

    .card {
        display: inline-block;
        width: 80px;
        height: 120px;
        background-color: white;
        border-radius: 5px;
        margin: 0 5px;
        text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    }
    
    .card-red {
        color: #e63946;
    }
    
    .card-black {
        color: #1d3557;
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
    # Function to display cards
    def display_card(card_code):
        if not card_code:
            return "🂠"  # Back of card
            
        rank = card_code[0]
        suit = card_code[1]
        
        suit_symbol = {
            'h': '♥',
            'd': '♦',
            'c': '♣',
            's': '♠'
        }.get(suit, '?')
        
        color_class = "card-red" if suit in ['h', 'd'] else "card-black"
        
        return f"""
        <div class="card">
            <div class="{color_class}">
                <h2>{rank}{suit_symbol}</h2>
            </div>
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
        
        return f"""
        <div class="chip" style="background-color: {color};">
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
                st.rerun()
        
        with col1:
            st.markdown("""
            ### Welcome to Texas Hold'em Poker!
            
            Start a new game by selecting the number of opponents and your starting chips.
            
            Each player will be dealt two cards, and you'll play through betting rounds as community cards are revealed.
            The player with the best five-card hand at the showdown wins!
            """)
            
            # Show sample cards as decoration
            st.markdown("""
            <div style="text-align: center; margin: 30px;">
            """+display_card("As")+display_card("Kh")+display_card("Qd")+display_card("Jc")+display_card("Ts")+"""
            </div>
            """, unsafe_allow_html=True)
    else:
        # Game is running - display game state
        game = st.session_state.game
        
        # Auto-refresh to simulate game updates - every 3 seconds if it's AI's turn
        if game.current_player and game.current_player.name != "You":
            st_autorefresh(interval=3000)
        
        # Check if we need to show the winning animation
        if st.session_state.show_confetti:
            #st_confetti()
            st.success(f"🎉 {st.session_state.winner.name} wins the pot!")
            st.session_state.show_confetti = False
            
        # Game table container
        st.markdown("<div class='poker-table'>", unsafe_allow_html=True)
        
        # Game info
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.subheader(f"Round: {st.session_state.current_round}")
        with col2:
            st.subheader(f"Pot: ${st.session_state.pot}")
        with col3:
            if st.button("Fold Hand", key="fold_hand"):
                # End the current hand
                if game.human_player:
                    game.human_player.fold()
                    
                # Update game state
                game.process_round()
                st.rerun()
            
        # Community cards area
        st.subheader("Community Cards")
        community_cards_html = "<div style='text-align: center; margin: 20px 0;'>"
        
        # Get community cards from game state
        community_cards = game.get_community_cards() if hasattr(game, 'get_community_cards') else []
        
        # Display community cards or placeholders
        if community_cards:
            for card in community_cards:
                community_cards_html += display_card(str(card))
        else:
            for _ in range(5):
                community_cards_html += display_card("")  # Empty card placeholder
                
        community_cards_html += "</div>"
        st.markdown(community_cards_html, unsafe_allow_html=True)
        
        # Player sections
        st.subheader("Players")
        
        # Arrange players in a grid
        cols = st.columns(len(st.session_state.players))
        
        for i, player in enumerate(st.session_state.players):
            with cols[i]:
                # Determine if this player is active
                is_active = game.current_player == player if hasattr(game, 'current_player') else False
                is_winner = st.session_state.winner == player if st.session_state.winner else False
                
                player_class = "player-active" if is_active else ""
                player_class += " winner" if is_winner else ""
                
                st.markdown(f"<div class='{player_class}'>", unsafe_allow_html=True)
                
                # Player name and chips
                st.markdown(f"### {player.name}")
                st.markdown(f"Chips: ${player.chips}")
                
                # Player cards
                player_cards_html = "<div style='text-align: center; margin: 15px 0;'>"
                
                # Show player's cards
                player_cards = player.hand if hasattr(player, 'hand') else []
                
                # Human player can see their cards, AI cards are hidden unless revealed
                if player.name == "You" or getattr(player, 'revealed', False):
                    for card in player_cards:
                        player_cards_html += display_card(str(card))
                else:
                    for _ in range(2):
                        player_cards_html += display_card("")  # Card back
                        
                player_cards_html += "</div>"
                st.markdown(player_cards_html, unsafe_allow_html=True)
                
                # Show last action
                if hasattr(player, 'last_action') and player.last_action:
                    st.markdown(f"**Last Action:** {player.last_action}")
                
                # Player actions - only show for human player when it's their turn
                if player.name == "You" and is_active:
                    st.markdown("<div class='action-buttons'>", unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Check", key=f"check_{i}", disabled=not game.can_check() if hasattr(game, 'can_check') else False):
                            player.check()
                            game.process_action(player, "check")
                            st.rerun()
                            
                        if st.button("Call", key=f"call_{i}", disabled=not game.can_call() if hasattr(game, 'can_call') else False):
                            player.call(game.current_bet if hasattr(game, 'current_bet') else 0)
                            game.process_action(player, "call")
                            st.rerun()
                    
                    with col2:
                        if st.button("Fold", key=f"fold_{i}"):
                            player.fold()
                            game.process_action(player, "fold")
                            st.rerun()
                            
                        # Raise requires a slider to determine amount
                        can_raise = game.can_raise() if hasattr(game, 'can_raise') else True
                        if can_raise:
                            min_raise = game.minimum_raise if hasattr(game, 'minimum_raise') else 10
                            raise_amount = st.slider("Raise Amount", 
                                                    min_value=min_raise, 
                                                    max_value=player.chips,
                                                    value=min_raise,
                                                    key=f"raise_slider_{i}")
                            
                            if st.button("Raise", key=f"raise_{i}"):
                                player.raise_bet(raise_amount)
                                game.process_action(player, "raise", raise_amount)
                                st.rerun()
                                
                    # All-in button at the bottom
                    if st.button("All In", key=f"all_in_{i}", type="primary"):
                        player.all_in()
                        game.process_action(player, "all_in")
                        st.rerun()
                                
                    st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
            
        # Process AI actions if it's their turn
        if game.current_player and game.current_player.name != "You":
            # AI takes action
            time.sleep(1)  # Simulate thinking
            action, amount = game.current_player.decide_action(
                game.get_game_state() if hasattr(game, 'get_game_state') else {}
            )
            game.process_action(game.current_player, action, amount)
            st.rerun()
            
        # Check for end of round/hand
        if game.is_round_complete() if hasattr(game, 'is_round_complete') else False:
            # Move to next round
            next_round = game.next_round()
            st.session_state.current_round = next_round
            st.rerun()
            
        if game.is_hand_complete() if hasattr(game, 'is_hand_complete') else False:
            # End of hand, determine winner
            winner = game.determine_winner()
            st.session_state.winner = winner
            st.session_state.show_confetti = True
            
            # Record game in history
            st.session_state.game_history.append({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "result": "win" if winner.name == "You" else "loss",
                "pot": st.session_state.pot,
                "winner": winner.name
            })
            
            # New hand button
            if st.button("Next Hand", type="primary", use_container_width=True):
                game.start_new_hand()
                st.session_state.winner = None
                st.session_state.pot = 0
                st.session_state.current_round = "Pre-Flop"
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Game controls at the bottom
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("End Game", type="secondary"):
                # Reset game state
                st.session_state.game = None
                st.session_state.players = []
                st.session_state.winner = None
                st.rerun()
                
        with col2:
            # Help button that shows rules in an expander
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