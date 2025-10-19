class MarioGame {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.ws = null;
        this.playerId = this.generatePlayerId();
        this.keys = {};
        this.gameState = {
            players: [],
            objects: [],
            level_width: 1600,
            level_height: 600
        };
        this.camera = { x: 0, y: 0 };
        this.hollowKnightSprite = null;
        
        this.init();
    }
    
    generatePlayerId() {
        return 'player_' + Math.random().toString(36).substr(2, 9);
    }
    
    init() {
        this.loadSprites();
        this.setupWebSocket();
        this.setupEventListeners();
        this.gameLoop();
    }
    
    loadSprites() {
        // Load Hollow Knight sprite
        this.hollowKnightSprite = new Image();
        this.hollowKnightSprite.onload = () => {
            console.log('Hollow Knight sprite loaded successfully');
        };
        this.hollowKnightSprite.onerror = () => {
            console.log('Failed to load Hollow Knight sprite, using fallback');
        };
        this.hollowKnightSprite.src = '/static/HollowKnight48.png';
    }
    
    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/${this.playerId}`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('Connected to game server');
        };
        
        this.ws.onmessage = (event) => {
            this.gameState = JSON.parse(event.data);
            this.updateUI();
        };
        
        this.ws.onclose = () => {
            console.log('Disconnected from game server');
            setTimeout(() => this.setupWebSocket(), 1000);
        };
    }
    
    setupEventListeners() {
        document.addEventListener('keydown', (e) => {
            this.keys[e.code] = true;
            this.handleKeyPress(e.code, true, e);
        });
        
        document.addEventListener('keyup', (e) => {
            this.keys[e.code] = false;
            this.handleKeyPress(e.code, false, e);
        });
    }
    
    handleKeyPress(keyCode, pressed, e) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        
        let action = null;
        
        if (pressed) {
            switch(keyCode) {
                case 'ArrowLeft':
                    action = 'left';
                    break;
                case 'ArrowRight':
                    action = 'right';
                    break;
                case 'Space':
                    action = 'jump';
                    if (e) e.preventDefault();
                    console.log('Jump key pressed!'); // Debug log
                    break;
            }
        } else {
            switch(keyCode) {
                case 'ArrowLeft':
                    action = 'stop_left';
                    break;
                case 'ArrowRight':
                    action = 'stop_right';
                    break;
            }
        }
        
        if (action) {
            this.ws.send(JSON.stringify({ action }));
            if (action === 'jump') {
                console.log('Jump action sent to server!'); // Debug log
            }
        }
    }
    
    updateUI() {
        const player = this.gameState.players.find(p => p.id === this.playerId);
        if (player) {
            document.getElementById('score').textContent = player.score;
            document.getElementById('lives').textContent = player.lives;
            
            if (player.lives <= 0) {
                this.showGameOver(player.score);
            }
            
            // Update camera to follow player
            this.camera.x = player.x - this.canvas.width / 2;
            this.camera.x = Math.max(0, Math.min(this.camera.x, this.gameState.level_width - this.canvas.width));
        }
    }
    
    showGameOver(score) {
        document.getElementById('finalScore').textContent = score;
        document.getElementById('gameOver').style.display = 'block';
    }
    
    restartGame() {
        document.getElementById('gameOver').style.display = 'none';
        // The server will reset the player when they reconnect
        this.setupWebSocket();
    }
    
    draw() {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw Hollow Knight style background
        this.ctx.fillStyle = '#0f0f23';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw ground (darker, more cave-like)
        this.ctx.fillStyle = '#2d2d44';
        this.ctx.fillRect(0, this.canvas.height - 50, this.canvas.width, 50);
        
        // Draw game objects
        this.gameState.objects.forEach(obj => {
            const x = obj.x - this.camera.x;
            const y = obj.y - this.camera.y;
            
            if (x + obj.width > 0 && x < this.canvas.width) {
                this.ctx.fillStyle = obj.color;
                this.ctx.fillRect(x, y, obj.width, obj.height);
                
                // Add some styling
                if (obj.type === 'platform') {
                    // Hollow Knight style platform (stone/cave)
                    this.ctx.strokeStyle = '#4a4a6a';
                    this.ctx.lineWidth = 2;
                    this.ctx.strokeRect(x, y, obj.width, obj.height);
                    
                    // Add some texture
                    this.ctx.fillStyle = '#3a3a5a';
                    this.ctx.fillRect(x + 2, y + 2, obj.width - 4, obj.height - 4);
                } else if (obj.type === 'enemy') {
                    // Draw Hollow Knight enemy (Gruz Mother style)
                    // Main body (orange/red)
                    this.ctx.fillStyle = '#ff6b35';
                    this.ctx.fillRect(x + 5, y + 5, obj.width - 10, obj.height - 10);
                    
                    // Eyes (white with black pupils)
                    this.ctx.fillStyle = '#ffffff';
                    this.ctx.fillRect(x + 8, y + 8, 6, 6);
                    this.ctx.fillRect(x + 16, y + 8, 6, 6);
                    
                    this.ctx.fillStyle = '#000';
                    this.ctx.fillRect(x + 10, y + 10, 2, 2);
                    this.ctx.fillRect(x + 18, y + 10, 2, 2);
                    
                    // Wings
                    this.ctx.fillStyle = '#ff8c42';
                    this.ctx.fillRect(x - 2, y + 12, 4, 8);
                    this.ctx.fillRect(x + obj.width - 2, y + 12, 4, 8);
                    
                    // Legs
                    this.ctx.fillStyle = '#d63031';
                    this.ctx.fillRect(x + 8, y + obj.height - 5, 3, 5);
                    this.ctx.fillRect(x + 19, y + obj.height - 5, 3, 5);
                } else if (obj.type === 'coin') {
                    // Draw Hollow Knight Geo (currency)
                    // Outer ring
                    this.ctx.fillStyle = '#ffd700';
                    this.ctx.beginPath();
                    this.ctx.arc(x + obj.width/2, y + obj.height/2, obj.width/2, 0, 2 * Math.PI);
                    this.ctx.fill();
                    
                    // Inner circle
                    this.ctx.fillStyle = '#ffed4e';
                    this.ctx.beginPath();
                    this.ctx.arc(x + obj.width/2, y + obj.height/2, obj.width/2 - 3, 0, 2 * Math.PI);
                    this.ctx.fill();
                    
                    // Hollow Knight symbol (simplified)
                    this.ctx.fillStyle = '#1a1a2e';
                    this.ctx.fillRect(x + obj.width/2 - 2, y + obj.height/2 - 4, 4, 8);
                    this.ctx.fillRect(x + obj.width/2 - 4, y + obj.height/2 - 2, 8, 4);
                }
            }
        });
        
                // Draw players (Hollow Knight)
        this.gameState.players.forEach(player => {
            const x = player.x - this.camera.x;
            const y = player.y - this.camera.y;
            
            if (x + player.width > 0 && x < this.canvas.width) {
                // Draw Hollow Knight sprite if loaded, otherwise fallback to pixel art
                if (this.hollowKnightSprite && this.hollowKnightSprite.complete) {
                    // Draw the sprite image at original 48x48 size
                    this.ctx.drawImage(
                        this.hollowKnightSprite,
                        x, y, 48, 48
                    );
                } else {
                    // Fallback pixel art (scaled to 48x48)
                    // Main body (dark blue/black)
                    this.ctx.fillStyle = '#1a1a2e';
                    this.ctx.fillRect(x + 3, y + 12, 17, 33);
                    
                    // Head (white mask)
                    this.ctx.fillStyle = '#f5f5f5';
                    this.ctx.fillRect(x + 5, y + 6, 13, 24);
                    
                    // Eyes (black dots)
                    this.ctx.fillStyle = '#000';
                    if (!player.on_ground) {
                        // Eyes closed when jumping (horizontal lines)
                        this.ctx.fillRect(x + 8, y + 14, 4, 2);
                        this.ctx.fillRect(x + 11, y + 14, 4, 2);
                    } else {
                        // Normal eyes when on ground
                        this.ctx.fillRect(x + 8, y + 14, 3, 3);
                        this.ctx.fillRect(x + 12, y + 14, 3, 3);
                    }
                    
                    // Horns
                    this.ctx.fillStyle = '#1a1a2e';
                    this.ctx.fillRect(x + 6, y + 2, 2, 10);
                    this.ctx.fillRect(x + 15, y + 2, 2, 10);
                    
                    // Cloak/cape
                    this.ctx.fillStyle = '#16213e';
                    this.ctx.fillRect(x + 1, y + 18, 21, 27);
                    
                    // Nail (sword)
                    this.ctx.fillStyle = '#c9c9c9';
                    this.ctx.fillRect(x + 21, y + 24, 2, 18);
                }
                
                // Add jump indicator
                if (!player.on_ground && player.velocity_y < 0) {
                    this.ctx.fillStyle = '#ffd700';
                    this.ctx.font = '12px Arial';
                    this.ctx.fillText('DASH!', x - 5, y - 10);
                }
            }
        });
    }
    
    gameLoop() {
        this.draw();
        requestAnimationFrame(() => this.gameLoop());
    }
}

// Start the game when page loads
window.addEventListener('load', () => {
    new MarioGame();
});

function restartGame() {
    location.reload();
}
