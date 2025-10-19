from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import json
import asyncio
from typing import Dict, List
import uuid
import time

# Game state management
class GameState:
    def __init__(self):
        self.players: Dict[str, dict] = {}
        self.game_objects: List[dict] = []
        self.level_width = 1600
        self.level_height = 600
        self.gravity = 1.2
        self.initialize_level()
    
    def initialize_level(self):
        # Ground platforms
        self.game_objects = [
            # Ground
            {"type": "platform", "x": 0, "y": 550, "width": 1600, "height": 50, "color": "#8B4513"},
            # Platforms
            {"type": "platform", "x": 200, "y": 450, "width": 150, "height": 20, "color": "#8B4513"},
            {"type": "platform", "x": 500, "y": 400, "width": 150, "height": 20, "color": "#8B4513"},
            {"type": "platform", "x": 800, "y": 350, "width": 150, "height": 20, "color": "#8B4513"},
            {"type": "platform", "x": 1100, "y": 300, "width": 150, "height": 20, "color": "#8B4513"},
            # Additional platforms for more gravity testing
            {"type": "platform", "x": 1400, "y": 250, "width": 100, "height": 20, "color": "#8B4513"},
            {"type": "platform", "x": 300, "y": 300, "width": 100, "height": 20, "color": "#8B4513"},
            {"type": "platform", "x": 600, "y": 200, "width": 100, "height": 20, "color": "#8B4513"},
            # Enemies
            {"type": "enemy", "x": 300, "y": 520, "width": 30, "height": 30, "color": "#FF0000", "direction": 1},
            {"type": "enemy", "x": 600, "y": 370, "width": 30, "height": 30, "color": "#FF0000", "direction": -1},
            {"type": "enemy", "x": 900, "y": 320, "width": 30, "height": 30, "color": "#FF0000", "direction": 1},
            # Enemies on higher platforms to show gravity
            {"type": "enemy", "x": 320, "y": 270, "width": 30, "height": 30, "color": "#FF0000", "direction": 1},
            {"type": "enemy", "x": 620, "y": 170, "width": 30, "height": 30, "color": "#FF0000", "direction": -1},
            # Coins
            {"type": "coin", "x": 250, "y": 400, "width": 20, "height": 20, "color": "#FFD700"},
            {"type": "coin", "x": 550, "y": 350, "width": 20, "height": 20, "color": "#FFD700"},
            {"type": "coin", "x": 850, "y": 300, "width": 20, "height": 20, "color": "#FFD700"},
            {"type": "coin", "x": 1150, "y": 250, "width": 20, "height": 20, "color": "#FFD700"},
        ]
    
    def add_player(self, player_id: str, name: str = "Player"):
        self.players[player_id] = {
            "id": player_id,
            "name": name,
            "x": 50,
            "y": 500,
            "width": 23,
            "height": 48,
            "velocity_x": 0,
            "velocity_y": 0,
            "on_ground": False,
            "facing_right": True,
            "score": 0,
            "lives": 3
        }
    
    def remove_player(self, player_id: str):
        if player_id in self.players:
            del self.players[player_id]
    
    def update_player(self, player_id: str, action: str):
        if player_id not in self.players:
            return
        
        player = self.players[player_id]
        
        # Handle input
        if action == "left":
            player["velocity_x"] = -5
            player["facing_right"] = False
        elif action == "right":
            player["velocity_x"] = 5
            player["facing_right"] = True
        elif action == "jump" and player["on_ground"]:
            player["velocity_y"] = -18  # Increased jump strength for better feel
        elif action == "stop_left" or action == "stop_right":
            player["velocity_x"] = 0
    
    def update_all_players(self):
        """Update all players with physics (gravity, movement, collisions)"""
        for player_id, player in self.players.items():
            # Apply gravity
            player["velocity_y"] += self.gravity
            
            # Update position
            player["x"] += player["velocity_x"]
            player["y"] += player["velocity_y"]
            
            # Check collisions with platforms
            player["on_ground"] = False
            for obj in self.game_objects:
                if obj["type"] == "platform" and self.check_collision(player, obj):
                    if player["velocity_y"] > 0 and player["y"] < obj["y"]:
                        player["y"] = obj["y"] - player["height"]
                        player["velocity_y"] = 0
                        player["on_ground"] = True
                    elif player["velocity_y"] < 0 and player["y"] > obj["y"]:
                        player["y"] = obj["y"] + obj["height"]
                        player["velocity_y"] = 0
            
            # Check collisions with enemies
            for obj in self.game_objects[:]:
                if obj["type"] == "enemy" and self.check_collision(player, obj):
                    if player["velocity_y"] > 0 and player["y"] < obj["y"]:
                        # Player jumped on enemy
                        self.game_objects.remove(obj)
                        player["score"] += 100
                        player["velocity_y"] = -10  # Bounce
                    else:
                        # Player hit enemy from side
                        player["lives"] -= 1
                        player["x"] = 50
                        player["y"] = 500
                        player["velocity_x"] = 0
                        player["velocity_y"] = 0
            
            # Check collisions with coins
            for obj in self.game_objects[:]:
                if obj["type"] == "coin" and self.check_collision(player, obj):
                    self.game_objects.remove(obj)
                    player["score"] += 50
            
            # Keep player in bounds
            if player["x"] < 0:
                player["x"] = 0
            if player["x"] > self.level_width - player["width"]:
                player["x"] = self.level_width - player["width"]
            if player["y"] > self.level_height:
                player["lives"] -= 1
                player["x"] = 50
                player["y"] = 500
                player["velocity_x"] = 0
                player["velocity_y"] = 0
    
    def update_enemies(self):
        """Update all enemies with movement and gravity"""
        for obj in self.game_objects:
            if obj["type"] == "enemy":
                # Apply gravity to enemies
                if "velocity_y" not in obj:
                    obj["velocity_y"] = 0
                obj["velocity_y"] += self.gravity
                
                # Move horizontally
                obj["x"] += obj["direction"] * 2
                if obj["x"] <= 0 or obj["x"] >= self.level_width - obj["width"]:
                    obj["direction"] *= -1
                
                # Apply vertical movement
                obj["y"] += obj["velocity_y"]
                
                # Check if enemy is on ground or platform
                enemy_on_ground = False
                for platform in self.game_objects:
                    if platform["type"] == "platform" and self.check_collision(obj, platform):
                        if obj["velocity_y"] > 0 and obj["y"] < platform["y"]:
                            obj["y"] = platform["y"] - obj["height"]
                            obj["velocity_y"] = 0
                            enemy_on_ground = True
                        elif obj["velocity_y"] < 0 and obj["y"] > platform["y"]:
                            obj["y"] = platform["y"] + platform["height"]
                            obj["velocity_y"] = 0
                
                # If enemy falls off the world, reset its position
                if obj["y"] > self.level_height:
                    obj["y"] = 520  # Reset to ground level
                    obj["velocity_y"] = 0
    
    def check_collision(self, obj1, obj2):
        return (obj1["x"] < obj2["x"] + obj2["width"] and
                obj1["x"] + obj1["width"] > obj2["x"] and
                obj1["y"] < obj2["y"] + obj2["height"] and
                obj1["y"] + obj1["height"] > obj2["y"])
    
    def get_game_state(self):
        return {
            "players": list(self.players.values()),
            "objects": self.game_objects,
            "level_width": self.level_width,
            "level_height": self.level_height
        }

# Global game state
game_state = GameState()

# Game loop task
game_loop_task = None

async def game_loop():
    """Continuous game loop that runs independently of player input"""
    frame_count = 0
    print("Game loop started!")
    while True:
        try:
            # Update all players with physics
            game_state.update_all_players()
            
            # Update enemies
            game_state.update_enemies()
            
            # Broadcast updated game state to all connected players
            if manager.active_connections:
                game_data = game_state.get_game_state()
                await manager.broadcast(json.dumps(game_data))
            
            # Debug: Print every 60 frames (once per second)
            frame_count += 1
            if frame_count % 60 == 0:
                print(f"Game loop running - Frame {frame_count}, Players: {len(game_state.players)}, Enemies: {len([obj for obj in game_state.game_objects if obj['type'] == 'enemy'])}")
            
            # Run at 60 FPS
            await asyncio.sleep(1/60)
        except Exception as e:
            print(f"Game loop error: {e}")
            await asyncio.sleep(1/60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the application lifespan"""
    global game_loop_task
    # Startup
    game_loop_task = asyncio.create_task(game_loop())
    print("Game loop started!")
    yield
    # Shutdown
    if game_loop_task:
        game_loop_task.cancel()
        print("Game loop stopped!")

# WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, player_id: str):
        await websocket.accept()
        self.active_connections[player_id] = websocket
        game_state.add_player(player_id)
    
    def disconnect(self, player_id: str):
        if player_id in self.active_connections:
            del self.active_connections[player_id]
        game_state.remove_player(player_id)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Create FastAPI app with lifespan
app = FastAPI(title="Super Mario Game API", lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_game(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: str):
    await manager.connect(websocket, player_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            action = json.loads(data).get("action")
            game_state.update_player(player_id, action)
            # Note: Game state is now updated continuously by the game loop
            
    except WebSocketDisconnect:
        manager.disconnect(player_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
