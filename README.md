# Super Mario Game with FastAPI

A web-based Super Mario game built with FastAPI, WebSockets, and HTML5 Canvas. Play the classic platformer in your browser with keyboard controls!

## Features

- 🎮 Real-time multiplayer gameplay using WebSockets
- 🏃‍♂️ Smooth character movement and jumping physics
- 🪙 Collectible coins for points
- 👾 Enemy AI with collision detection
- 🎯 Platform-based level design
- 💀 Lives system and game over screen
- 📊 Real-time score tracking

## Controls

- **Arrow Keys (← →)**: Move left and right
- **Spacebar**: Jump
- **Objective**: Collect coins, avoid enemies, and survive!

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Game

1. Start the FastAPI server:

```bash
python main.py
```

2. Open your web browser and navigate to:

```
http://localhost:8000
```

3. Start playing! The game supports multiple players simultaneously.

## Game Mechanics

- **Mario**: Red character with blue overalls and a red hat
- **Platforms**: Brown platforms you can jump on
- **Enemies**: Red creatures that move back and forth - avoid them or jump on them!
- **Coins**: Golden collectibles worth 50 points each
- **Lives**: Start with 3 lives, lose one when touching enemies or falling off the screen
- **Score**: Earn points by collecting coins (50 points) and defeating enemies (100 points)

## Technical Details

- **Backend**: FastAPI with WebSocket support for real-time communication
- **Frontend**: HTML5 Canvas with JavaScript for game rendering
- **Physics**: Custom gravity and collision detection system
- **Multiplayer**: WebSocket-based real-time synchronization

## Game Architecture

- `main.py`: FastAPI server with game logic and WebSocket handling
- `templates/index.html`: Complete game UI with HTML, CSS, and JavaScript
- `requirements.txt`: Python dependencies

## Development

The game uses a client-server architecture where:
- The server maintains the authoritative game state
- Clients send input via WebSocket messages
- The server broadcasts updated game state to all connected players
- The client renders the game using HTML5 Canvas

Enjoy playing Super Mario! 🍄
