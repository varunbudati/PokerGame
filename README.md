# Interactive Poker Game

A fully interactive Texas Hold'em poker game built with Streamlit and modern web technologies. This game features realistic gameplay, AI opponents, and a visually appealing interface with dark and light mode options.

## Features

- **Beautiful Card Animations**: Smooth, realistic card dealing and movements
- **Intelligent AI Opponents**: Play against computer players with different skill levels and playstyles
- **Dark/Light Mode**: Toggle between themes for comfortable viewing in any environment
- **Realistic Poker Chips**: Visual chip stacks that accurately represent your bankroll
- **Hand Analysis**: Get insights into winning probabilities and hand strengths
- **Game History**: Track your performance over time with detailed statistics
- **Responsive Design**: Play on desktop or tablet devices with adaptive layouts
- **Sound Effects**: Optional ambient casino sounds and game event audio

## Installation

```bash
# Clone this repository
git clone https://github.com/yourusername/poker-game.git

# Navigate to the project directory
cd poker-game

# Install required packages
pip install -r requirements.txt

# Run the game
streamlit run app.py
```

## How to Play

1. **Starting the Game**: Launch the application and configure your game settings
2. **Betting Round**: Click on chips or use the slider to place your bets
3. **Game Actions**: Choose from options like Check, Call, Raise, or Fold
4. **Hand Evaluation**: After the final betting round, hands are compared and a winner is declared
5. **New Round**: Cards are reshuffled and a new round begins

## Game Rules

This game follows standard Texas Hold'em poker rules:

- Each player is dealt two private cards (hole cards)
- Five community cards are dealt face-up in three stages:
  - The Flop: First three community cards
  - The Turn: Fourth community card
  - The River: Fifth community card
- Players make the best five-card poker hand using any combination of their hole cards and the community cards
- Betting rounds occur before the flop and after each community card is revealed
- Hand rankings follow standard poker rules (Royal Flush > Straight Flush > Four of a Kind > etc.)

## Integration with Your Website

This poker game can be easily embedded into your existing website:

1. Host the Streamlit app
2. Use an iframe to embed the game in your website:
```html
<iframe
  src="https://your-streamlit-app-url"
  width="100%"
  height="800px"
  frameborder="0">
</iframe>
```

## License

[MIT License](LICENSE)

## Credits

- Card designs: [Playing Cards IO](https://playingcards.io/)
- Poker chip designs: Custom created
- Sound effects: [Freesound.org](https://freesound.org/)