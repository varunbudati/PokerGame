import streamlit as st
import time
import random
import json
import os
from PIL import Image
from streamlit_option_menu import option_menu
from streamlit_autorefresh import st_autorefresh
from streamlit_confetti import st_confetti
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
    </style>
    """,
    unsafe_allow_html=True
)

# Header
st.markdown("<div class='header'><h1>Texas Hold'em Poker</h1></div>", unsafe_allow_html=True)

# Poker Table Layout
st.markdown("<div class='poker-table'>", unsafe_allow_html=True)

# Game Info
st.subheader("Game Information")
st.write("Pot: $0")
st.write("Round: Pre-Flop")

# Opponents
st.subheader("Opponents")
for i in range(1, 4):
    st.write(f"Opponent {i}: $1000")

# Player Area
st.subheader("Player Area")
st.write("You: $1000")

# Action Buttons
st.markdown("<div class='action-buttons'>", unsafe_allow_html=True)
if st.button("Fold"):
    st.write("You folded.")
if st.button("Check"):
    st.write("You checked.")
if st.button("Call"):
    st.write("You called.")
if st.button("Raise"):
    st.write("You raised.")
if st.button("All In"):
    st.write("You went all in!")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)