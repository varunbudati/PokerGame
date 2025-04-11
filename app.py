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

# Initialize session state variables if they don't exist
if 'game' not in st.session_state:
    st.session_state.game = None
if 'theme' not in st.session_state:
    st.session_state.theme = 'dark'
if 'bankroll' not in st.session_state:
    st.session_state.bankroll = 1000
if 'player_name' not in st.session_state:
    st.session_state.player_name = "Player 1"
if 'game_history' not in st.session_state:
    st.session_state.game_history = []
if 'settings_open' not in st.session_state:
    st.session_state.settings_open = False
if 'sound_enabled' not in st.session_state:
    st.session_state.sound_enabled = True
if 'animation_speed' not in st.session_state:
    st.session_state.animation_speed = 'medium'

# Theme toggle function
def toggle_theme():
    if st.session_state.theme == 'dark':
        st.session_state.theme = 'light'
    else:
        st.session_state.theme = 'dark'

# Custom CSS for both themes
def load_css():
    theme = st.session_state.theme
    
    # Common CSS regardless of theme
    common_css = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
        
        * {
            font-family: 'Poppins', sans-serif;
        }
        
        .card {
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-10px);
        }
        
        .poker-chips {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        
        .chip {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            border: 5px dashed white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .chip:hover {
            transform: scale(1.1);
        }
        
        .player-area, .opponent-area {
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
        }
        
        .action-button {
            margin-right: 10px;
        }
        
        /* Animation classes */
        .deal-animation {
            animation: deal 0.5s ease-out forwards;
        }
        
        .win-animation {
            animation: pulse 1s infinite;
        }
        
        @keyframes deal {
            from {
                opacity: 0;
                transform: translate(-50px, -50px) rotate(-20deg);
            }
            to {
                opacity: 1;
                transform: translate(0, 0) rotate(0);
            }
        }
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(255, 215, 0, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(255, 215, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 215, 0, 0); }
        }
    </style>
    """
    
    # Dark theme CSS
    dark_css = """
    <style>
        .stApp {
            background-color: #1A1A2E;
            color: #E6E6E6;
        }
        
        .poker-table {
            background: linear-gradient(#0F3460, #16213E);
            border: 5px solid #533483;
            border-radius: 150px;
            padding: 30px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.5);
        }
        
        .player-area {
            background-color: rgba(15, 52, 96, 0.7);
            border: 1px solid #533483;
        }
        
        .opponent-area {
            background-color: rgba(83, 52, 131, 0.7);
            border: 1px solid #0F3460;
        }
        
        .chip.red { background: linear-gradient(#E94560, #c91e3a); color: white; }
        .chip.blue { background: linear-gradient(#0F3460, #0a1e38); color: white; }
        .chip.green { background: linear-gradient(#16a34a, #15803d); color: white; }
        .chip.black { background: linear-gradient(#27272a, #18181b); color: white; }
        .chip.gold { background: linear-gradient(#fbbf24, #d97706); color: black; }
    </style>
    """
    
    # Light theme CSS
    light_css = """
    <style>
        .stApp {
            background-color: #F5F5F5;
            color: #333333;
        }
        
        .poker-table {
            background: linear-gradient(#4DA167, #2E6E4C);
            border: 5px solid #805A46;
            border-radius: 150px;
            padding: 30px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        
        .player-area {
            background-color: rgba(77, 161, 103, 0.7);
            border: 1px solid #805A46;
        }
        
        .opponent-area {
            background-color: rgba(128, 90, 70, 0.7);
            border: 1px solid #4DA167;
        }
        
        .chip.red { background: linear-gradient(#ef4444, #dc2626); color: white; }
        .chip.blue { background: linear-gradient(#3b82f6, #2563eb); color: white; }
        .chip.green { background: linear-gradient(#22c55e, #16a34a); color: white; }
        .chip.black { background: linear-gradient(#3f3f46, #27272a); color: white; }
        .chip.gold { background: linear-gradient(#fcd34d, #f59e0b); color: black; }
    </style>
    """
    
    # Load appropriate theme
    if theme == 'dark':
        st.markdown(common_css + dark_css, unsafe_allow_html=True)
    else:
        st.markdown(common_css + light_css, unsafe_allow_html=True)

# Format currency values
def format_money(amount):
    return f"${amount:,.2f}"

# Start a new game
def start_new_game():
    player = Player(st.session_state.player_name, st.session_state.bankroll)
    opponents = [
        AIPlayer("Bob", 1000, "conservative"),
        AIPlayer("Alice", 1000, "aggressive"),
        AIPlayer("Charlie", 1000, "balanced")
    ]
    st.session_state.game = PokerGame(player, opponents, small_blind=5, big_blind=10)
    st.session_state.game.start_hand()

# Game action functions
def player_action(action, amount=0):
    game = st.session_state.game
    if game and game.state != GameState.HAND_COMPLETE:
        if action == GameAction.FOLD:
            game.player_fold()
        elif action == GameAction.CHECK:
            game.player_check()
        elif action == GameAction.CALL:
            game.player_call()
        elif action == GameAction.RAISE:
            game.player_raise(amount)
        elif action == GameAction.ALL_IN:
            game.player_all_in()
        
        if game.state == GameState.HAND_COMPLETE:
            # Record game history
            result = {
                "hand_num": len(st.session_state.game_history) + 1,
                "bankroll": game.player.bankroll,
                "net_change": game.player.bankroll - st.session_state.bankroll,
                "win": game.player.bankroll > st.session_state.bankroll,
                "timestamp": time.time()
            }
            st.session_state.game_history.append(result)
            st.session_state.bankroll = game.player.bankroll
            
            # Show confetti on big wins
            if result["net_change"] > 100:
                st_confetti()

# Sidebar for navigation and controls
with st.sidebar:
    # Theme toggle
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Interactive Poker Game")
    with col2:
        theme_icon = "🌙" if st.session_state.theme == 'light' else "☀️"
        st.button(theme_icon, on_click=toggle_theme, key="theme_toggle")
    
    # Navigation menu
    selected = option_menu(
        "",
        ["Play", "Stats", "Settings", "Help"],
        icons=["joystick", "graph-up", "gear", "question-circle"],
        menu_icon="cast",
        default_index=0,
    )
    
    # Show player stats
    st.write(f"Player: {st.session_state.player_name}")
    st.write(f"Bankroll: {format_money(st.session_state.bankroll)}")
    
    if selected == "Play":
        if st.button("New Game", key="new_game"):
            start_new_game()
    
    elif selected == "Stats":
        st.subheader("Game Statistics")
        if len(st.session_state.game_history) > 0:
            # Create a DataFrame from game history
            history_df = pd.DataFrame(st.session_state.game_history)
            
            # Display win rate
            win_rate = (history_df['win'].sum() / len(history_df)) * 100
            st.metric("Win Rate", f"{win_rate:.1f}%")
            
            # Display net profit/loss
            net_profit = history_df['net_change'].sum()
            st.metric("Net Profit/Loss", format_money(net_profit),
                     delta=f"{'+' if net_profit > 0 else ''}{net_profit:.2f}")
            
            # Show bankroll chart if enough data
            if len(history_df) > 1:
                st.subheader("Bankroll Over Time")
                fig = plt.figure(figsize=(6, 3))
                plt.plot(history_df['hand_num'], history_df['bankroll'])
                plt.xlabel('Hand #')
                plt.ylabel('Bankroll')
                plt.grid(True, alpha=0.3)
                st.pyplot(fig)
        else:
            st.info("Play some hands to see your statistics!")
    
    elif selected == "Settings":
        st.session_state.settings_open = True
        st.subheader("Game Settings")
        
        # Player settings
        st.text_input("Player Name", key="temp_name", value=st.session_state.player_name)
        st.number_input("Starting Bankroll", min_value=100, max_value=10000, value=st.session_state.bankroll, step=100, key="temp_bankroll")
        
        # Game settings
        st.toggle("Sound Effects", value=st.session_state.sound_enabled, key="temp_sound")
        st.selectbox("Animation Speed", options=["slow", "medium", "fast", "off"], index=["slow", "medium", "fast", "off"].index(st.session_state.animation_speed), key="temp_animation")
        
        # Save settings button
        if st.button("Save Settings"):
            st.session_state.player_name = st.session_state.temp_name
            st.session_state.bankroll = st.session_state.temp_bankroll
            st.session_state.sound_enabled = st.session_state.temp_sound
            st.session_state.animation_speed = st.session_state.temp_animation
            st.session_state.settings_open = False
            st.success("Settings saved!")
    
    elif selected == "Help":
        st.subheader("How to Play")
        st.write("""
        1. Click 'New Game' to start
        2. You'll be dealt 2 cards
        3. Choose an action: Fold, Check, Call, Raise, or All In
        4. Try to make the best 5-card hand using your cards and the community cards
        """)
        
        st.subheader("Poker Hand Rankings")
        hand_rankings = {
            "Royal Flush": "A, K, Q, J, 10 of the same suit",
            "Straight Flush": "Five consecutive cards of the same suit",
            "Four of a Kind": "Four cards of the same rank",
            "Full House": "Three of a kind plus a pair",
            "Flush": "Five cards of the same suit",
            "Straight": "Five consecutive cards",
            "Three of a Kind": "Three cards of the same rank",
            "Two Pair": "Two different pairs",
            "Pair": "Two cards of the same rank",
            "High Card": "Highest card in your hand"
        }
        
        for hand, desc in hand_rankings.items():
            st.write(f"**{hand}**: {desc}")

# Load custom CSS based on theme
load_css()

# Main game UI
if selected == "Play":
    st.title("Texas Hold'em Poker")
    
    # Check if a game is in progress
    if st.session_state.game is None:
        # Welcome screen
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("<h2 style='text-align: center;'>Welcome to Interactive Poker!</h2>", unsafe_allow_html=True)
            st.markdown("""
            <div style='text-align: center;'>
                <p>Experience the thrill of Texas Hold'em poker against AI opponents!</p>
                <p>Click "New Game" in the sidebar to begin playing.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            # Display a poker-related image
            st.image("https://images.unsplash.com/photo-1609710228159-0fa9bd7c0827?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1170&q=80", 
                     caption="Ready to test your poker skills?", use_column_width=True)
    
    else:
        # Active game display
        game = st.session_state.game
        
        # Information row
        info_col1, info_col2, info_col3 = st.columns(3)
        with info_col1:
            st.metric("Pot", format_money(game.pot))
        with info_col2:
            st.write(f"Round: {game.betting_round}")
        with info_col3:
            st.write(f"Current Bet: {format_money(game.current_bet)}")
        
        # Poker table container
        st.markdown("<div class='poker-table'>", unsafe_allow_html=True)
        
        # Opponents area
        st.subheader("Opponents")
        opponent_cols = st.columns(len(game.opponents))
        
        for i, opponent in enumerate(game.opponents):
            with opponent_cols[i]:
                st.markdown(f"<div class='opponent-area'>", unsafe_allow_html=True)
                st.write(f"**{opponent.name}**")
                st.write(f"Chips: {format_money(opponent.bankroll)}")
                st.write(f"Bet: {format_money(opponent.current_bet)}")
                
                # Show opponent cards if hand is complete
                if game.state == GameState.HAND_COMPLETE:
                    cards_html = ""
                    for card in opponent.hand.cards:
                        cards_html += f"<img src='https://deckofcardsapi.com/static/img/{card.short_name}.png' width='60' class='card' />"
                    st.markdown(f"<div style='display: flex; gap: 5px;'>{cards_html}</div>", unsafe_allow_html=True)
                else:
                    # Show card backs
                    st.markdown("""
                    <div style='display: flex; gap: 5px;'>
                        <img src='https://deckofcardsapi.com/static/img/back.png' width='60' class='card' />
                        <img src='https://deckofcardsapi.com/static/img/back.png' width='60' class='card' />
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show opponent's last action
                if opponent.last_action:
                    st.write(f"Action: {opponent.last_action}")
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Community cards
        st.subheader("Community Cards")
        if game.community_cards:
            cards_html = ""
            for card in game.community_cards:
                cards_html += f"<img src='https://deckofcardsapi.com/static/img/{card.short_name}.png' width='80' class='card deal-animation' />"
            st.markdown(f"<div style='display: flex; justify-content: center; gap: 10px;'>{cards_html}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='text-align: center;'>Waiting for flop...</p>", unsafe_allow_html=True)
        
        # Player area
        st.subheader("Your Hand")
        st.markdown("<div class='player-area'>", unsafe_allow_html=True)
        
        player_col1, player_col2 = st.columns([2, 3])
        
        with player_col1:
            st.write(f"**{game.player.name}**")
            st.write(f"Chips: {format_money(game.player.bankroll)}")
            st.write(f"Your Bet: {format_money(game.player.current_bet)}")
            
            # Show player's hand
            if game.player.hand:
                cards_html = ""
                for card in game.player.hand.cards:
                    cards_html += f"<img src='https://deckofcardsapi.com/static/img/{card.short_name}.png' width='80' class='card' />"
                st.markdown(f"<div style='display: flex; gap: 10px;'>{cards_html}</div>", unsafe_allow_html=True)
                
                # Show hand strength if community cards are available
                if len(game.community_cards) > 0:
                    combined = game.player.hand.cards + game.community_cards
                    hand_eval = evaluate_hand(combined)
                    st.write(f"Hand: **{rank_to_string(hand_eval[0])}**")
        
        with player_col2:
            # Player actions
            if game.state == GameState.WAITING_FOR_PLAYER and not game.player.folded:
                action_col1, action_col2, action_col3, action_col4 = st.columns(4)
                
                with action_col1:
                    st.button("Fold", on_click=player_action, args=(GameAction.FOLD,), key="fold_button")
                
                with action_col2:
                    # Check if player can check
                    if game.can_check():
                        st.button("Check", on_click=player_action, args=(GameAction.CHECK,), key="check_button")
                    else:
                        st.button("Call", on_click=player_action, args=(GameAction.CALL,), key="call_button")
                
                with action_col3:
                    # Raise amount slider
                    min_raise = game.min_raise()
                    max_raise = min(game.player.bankroll, min_raise * 4)
                    raise_amount = st.slider("Raise Amount", min_value=min_raise, max_value=max_raise, value=min_raise, step=5)
                
                with action_col4:
                    st.button("Raise", on_click=player_action, args=(GameAction.RAISE, raise_amount), key="raise_button")
                    st.button("All In", on_click=player_action, args=(GameAction.ALL_IN,), key="allin_button")
            
            # Show game result if hand is complete
            elif game.state == GameState.HAND_COMPLETE:
                if game.winner == game.player:
                    st.success("You won the hand! 🎉")
                elif game.winners and game.player in game.winners:
                    st.success("You split the pot! 🎉")
                elif game.player.folded:
                    st.info("You folded this hand.")
                else:
                    st.error("You lost this hand.")
                
                # Show winner's hand
                if game.winner and game.winner != game.player:
                    st.write(f"Winner: **{game.winner.name}**")
                    winning_rank = evaluate_hand(game.winner.hand.cards + game.community_cards)
                    st.write(f"Winning hand: **{rank_to_string(winning_rank[0])}**")
                
                # Deal next hand button
                if st.button("Deal Next Hand"):
                    st.session_state.game.start_hand()
                    st.experimental_rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)  # Close poker table div
        
        # Chips for betting (visual only)
        st.markdown("<div class='poker-chips'>", unsafe_allow_html=True)
        st.markdown("<div class='chip red'>$5</div>", unsafe_allow_html=True)
        st.markdown("<div class='chip blue'>$10</div>", unsafe_allow_html=True)
        st.markdown("<div class='chip green'>$25</div>", unsafe_allow_html=True)
        st.markdown("<div class='chip black'>$100</div>", unsafe_allow_html=True)
        st.markdown("<div class='chip gold'>$500</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

elif selected == "Stats":
    st.title("Your Poker Statistics")
    
    if len(st.session_state.game_history) == 0:
        st.info("Play some hands to see your statistics here!")
    else:
        # Create tabs for different stats views
        tab1, tab2, tab3 = st.tabs(["Performance", "Hand History", "Analysis"])
        
        with tab1:
            # Performance metrics
            history_df = pd.DataFrame(st.session_state.game_history)
            
            # Summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                hands_played = len(history_df)
                st.metric("Hands Played", hands_played)
            
            with col2:
                win_rate = (history_df['win'].sum() / len(history_df)) * 100
                st.metric("Win Rate", f"{win_rate:.1f}%")
            
            with col3:
                net_profit = history_df['net_change'].sum()
                profit_per_hand = net_profit / len(history_df) if len(history_df) > 0 else 0
                st.metric("Profit per Hand", format_money(profit_per_hand))
            
            # Bankroll chart
            st.subheader("Bankroll Over Time")
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=history_df['hand_num'],
                y=history_df['bankroll'],
                mode='lines+markers',
                name='Bankroll',
                line=dict(color='#4DA167' if st.session_state.theme == 'light' else '#533483', width=2),
                marker=dict(size=6)
            ))
            
            fig.update_layout(
                title='Your Bankroll Progression',
                xaxis_title='Hand Number',
                yaxis_title='Bankroll ($)',
                height=400,
                template='plotly_white' if st.session_state.theme == 'light' else 'plotly_dark'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            st.subheader("Hand History")
            st.dataframe(
                history_df[['hand_num', 'bankroll', 'net_change', 'win']],
                use_container_width=True,
                hide_index=True
            )
        
        with tab3:
            st.subheader("Performance Analysis")
            st.write("Insights about your poker play:")
            
            # Win/loss streak
            current_streak = 1
            streak_type = history_df.iloc[-1]['win']
            
            for i in range(len(history_df)-2, -1, -1):
                if history_df.iloc[i]['win'] == streak_type:
                    current_streak += 1
                else:
                    break
            
            streak_message = f"You are on a {current_streak} hand {'winning' if streak_type else 'losing'} streak."
            if streak_type:
                st.success(streak_message)
            else:
                st.error(streak_message)
            
            # Most profitable session
            if len(history_df) >= 10:
                history_df['session'] = (history_df.index // 10) + 1
                session_profits = history_df.groupby('session')['net_change'].sum()
                best_session = session_profits.idxmax()
                worst_session = session_profits.idxmin()
                
                st.write(f"Your most profitable session was session {best_session} with {format_money(session_profits[best_session])} in profit.")
                st.write(f"Your worst session was session {worst_session} with {format_money(session_profits[worst_session])} in net change.")

elif selected == "Help":
    st.title("Poker Help & Rules")
    
    st.subheader("How to Play Texas Hold'em")
    
    st.markdown("""
    ### Basic Rules:
    
    1. **The Goal**: Make the best five-card poker hand using your two hole cards and the five community cards.
    
    2. **Game Flow**:
       - Players receive two private cards (hole cards)
       - Five community cards are dealt in stages:
         - The Flop (first three cards)
         - The Turn (fourth card) 
         - The River (fifth card)
       - Betting rounds occur after each stage
    
    3. **Betting Actions**:
       - **Fold**: Give up your hand and forfeit the pot
       - **Check**: Pass the action without betting (only if no one has bet)
       - **Call**: Match the current bet
       - **Raise**: Increase the current bet
       - **All In**: Bet all your remaining chips
    
    4. **Winning the Hand**:
       - Best five-card hand wins
       - If two players have the same hand, they split the pot
    """)
    
    st.subheader("Poker Hand Rankings")
    
    hand_images = {
        "Royal Flush": "https://www.pokernews.com/img/content/royal_flush.png",
        "Straight Flush": "https://www.pokernews.com/img/content/straight_flush.png",
        "Four of a Kind": "https://www.pokernews.com/img/content/four_of_a_kind.png",
        "Full House": "https://www.pokernews.com/img/content/full_house.png",
        "Flush": "https://www.pokernews.com/img/content/flush.png",
        "Straight": "https://www.pokernews.com/img/content/straight.png",
        "Three of a Kind": "https://www.pokernews.com/img/content/three_of_a_kind.png",
        "Two Pair": "https://www.pokernews.com/img/content/two_pair.png",
        "Pair": "https://www.pokernews.com/img/content/pair.png",
        "High Card": "https://www.pokernews.com/img/content/high_card.png"
    }
    
    col1, col2 = st.columns(2)
    
    hands = list(hand_images.items())
    
    for i, (hand, img) in enumerate(hands[:5]):
        with col1:
            st.write(f"**{i+1}. {hand}**")
            st.image(img, width=200)
    
    for i, (hand, img) in enumerate(hands[5:]):
        with col2:
            st.write(f"**{i+6}. {hand}**")
            st.image(img, width=200)
    
    st.subheader("Tips for Beginners")
    st.markdown("""
    - **Start conservative**: Don't play too many hands at the beginning
    - **Position matters**: Being the last to act gives you an advantage
    - **Watch your opponents**: Try to identify patterns in how they play
    - **Manage your bankroll**: Never bet more than you can afford to lose
    - **Know when to fold**: Sometimes the best move is to let a hand go
    """)

# Auto-refresh if game is in progress and waiting for AI (every 2 seconds)
if st.session_state.game and st.session_state.game.state not in [GameState.WAITING_FOR_PLAYER, GameState.HAND_COMPLETE]:
    st_autorefresh(interval=2000, key="game_refresh")
