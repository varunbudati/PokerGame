import streamlit as st
from poker.game import PokerGame
from poker.player import Player
from poker.cards import Card

# Initialize the game
st.set_page_config(page_title="Poker Game", layout="wide")
st.title("Poker Game")

# Sidebar for game settings
st.sidebar.header("Game Settings")
num_players = st.sidebar.slider("Number of Players", min_value=2, max_value=6, value=4)

# Initialize players and game
players = [Player(f"Player {i+1}") for i in range(num_players)]
game = PokerGame(players)

# Main game area
if st.button("Start Game"):
    game.start_game()
    st.session_state["game"] = game

if "game" in st.session_state:
    game = st.session_state["game"]

    # Display community cards
    st.subheader("Community Cards")
    community_cards = game.get_community_cards()
    st.write(", ".join(str(card) for card in community_cards))

    # Display player information
    st.subheader("Players")
    for player in game.players:
        st.write(f"{player.name}: {player.chips} chips")

    # Player actions
    st.subheader("Actions")
    for player in game.players:
        if player.is_active:
            action = st.radio(f"{player.name}'s Action", ["Fold", "Check", "Call", "Raise", "All-In"], key=player.name)
            if action == "Raise":
                raise_amount = st.number_input(f"Raise Amount for {player.name}", min_value=0, max_value=player.chips, step=1, key=f"raise_{player.name}")
                player.raise_bet(raise_amount)
            elif action == "Fold":
                player.fold()
            elif action == "Check":
                player.check()
            elif action == "Call":
                player.call()
            elif action == "All-In":
                player.all_in()

    # Next round button
    if st.button("Next Round"):
        game.next_round()

# End game
if st.button("End Game"):
    winner = game.determine_winner()
    st.success(f"The winner is {winner.name}!")