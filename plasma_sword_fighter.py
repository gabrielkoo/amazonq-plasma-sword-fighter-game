import pygame
import math
import random

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)

class PlasmaSword:
    def __init__(self, x, y, color, length=80):
        self.x = x
        self.y = y
        self.color = color
        self.length = length
        self.angle = 0
        self.active = False
        self.swing_speed = 0
        self.base_angle = 0
        
    def update(self, player_x, player_y, mouse_x, mouse_y, swinging=False):
        self.x = player_x
        self.y = player_y
        
        # Calculate angle to mouse
        dx = mouse_x - player_x
        dy = mouse_y - player_y
        self.base_angle = math.atan2(dy, dx)
        
        if swinging:
            self.swing_speed = min(self.swing_speed + 0.3, 0.8)
            self.angle = self.base_angle + math.sin(pygame.time.get_ticks() * 0.02) * self.swing_speed
        else:
            self.swing_speed = max(self.swing_speed - 0.1, 0)
            self.angle = self.base_angle
    
    def draw(self, screen):
        if self.active:
            # Draw sword blade with glow effect
            end_x = self.x + math.cos(self.angle) * self.length
            end_y = self.y + math.sin(self.angle) * self.length
            
            # Glow effect
            for i in range(5, 0, -1):
                glow_color = tuple(min(255, c + 50) for c in self.color)
                pygame.draw.line(screen, glow_color, (self.x, self.y), (end_x, end_y), i * 2)
            
            # Main blade
            pygame.draw.line(screen, self.color, (self.x, self.y), (end_x, end_y), 4)
            
            # Hilt
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), 8)
            pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), 6)

class Fighter:
    def __init__(self, x, y, color, controls, is_player1=False, is_ai=False):
        self.x = x
        self.y = y
        self.color = color
        self.health = 100
        self.max_health = 100
        self.speed = 5
        self.sword = PlasmaSword(x, y, color)
        self.controls = controls
        self.is_player1 = is_player1
        self.is_ai = is_ai
        self.last_hit_time = 0
        self.invulnerable_time = 500  # milliseconds
        self.force_push_cooldown = 0
        self.force_push_max_cooldown = 2000
        self.auto_target = not is_player1 or is_ai  # Player 1 starts with mouse control, AI always auto-targets
        self.toggle_pressed = False  # Track toggle key state
        
        # AI specific attributes
        self.ai_decision_timer = 0
        self.ai_action = 'idle'
        self.ai_target_distance = 100
        self.ai_reaction_time = 0
        
    def update(self, keys, mouse_pos, other_fighter, ai_difficulty='medium'):
        current_time = pygame.time.get_ticks()
        
        if self.is_ai:
            # AI behavior
            self.update_ai(other_fighter, ai_difficulty, current_time)
        else:
            # Human player controls
            # Movement
            if keys[self.controls['up']]:
                self.y -= self.speed
            if keys[self.controls['down']]:
                self.y += self.speed
            if keys[self.controls['left']]:
                self.x -= self.speed
            if keys[self.controls['right']]:
                self.x += self.speed
                
            # Keep player on screen
            self.x = max(20, min(SCREEN_WIDTH - 20, self.x))
            self.y = max(20, min(SCREEN_HEIGHT - 20, self.y))
            
            # Sword activation and swinging
            swinging = keys[self.controls['attack']]
            self.sword.active = keys[self.controls['activate']] or swinging
            
            # Force push ability
            if keys[self.controls['force']] and self.force_push_cooldown <= 0:
                self.use_force_push(other_fighter)
                self.force_push_cooldown = self.force_push_max_cooldown
            
            # Toggle targeting mode
            if 'toggle_target' in self.controls:
                if keys[self.controls['toggle_target']] and not self.toggle_pressed:
                    self.auto_target = not self.auto_target
                    self.toggle_pressed = True
                elif not keys[self.controls['toggle_target']]:
                    self.toggle_pressed = False
            
            # Update sword
            if self.auto_target:
                # Auto-target the other fighter
                target_x = other_fighter.x
                target_y = other_fighter.y
                self.sword.update(self.x, self.y, target_x, target_y, swinging)
            else:
                # Use mouse for sword targeting (Player 1 only)
                self.sword.update(self.x, self.y, mouse_pos[0], mouse_pos[1], swinging)
            
            # Combat detection
            if swinging and self.sword.active:
                self.check_combat(other_fighter, current_time)
        
        if self.force_push_cooldown > 0:
            self.force_push_cooldown -= 16  # Assuming 60 FPS
    
    def update_ai(self, other_fighter, difficulty, current_time):
        # Calculate distance to player
        dx = other_fighter.x - self.x
        dy = other_fighter.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # AI difficulty settings
        if difficulty == 'easy':
            reaction_delay = 800
            move_speed = 2
            attack_range = 60
            force_push_chance = 0.01
            dodge_chance = 0.3
        elif difficulty == 'medium':
            reaction_delay = 400
            move_speed = 4
            attack_range = 80
            force_push_chance = 0.02
            dodge_chance = 0.5
        else:  # hard
            reaction_delay = 200
            move_speed = 6
            attack_range = 100
            force_push_chance = 0.03
            dodge_chance = 0.7
        
        self.speed = move_speed
        
        # AI decision making with reaction delay
        if current_time - self.ai_decision_timer > reaction_delay:
            self.ai_decision_timer = current_time
            
            # Determine AI action based on situation
            if distance > attack_range:
                self.ai_action = 'approach'
            elif distance < 40 and other_fighter.sword.active and random.random() < dodge_chance:
                self.ai_action = 'dodge'
            elif distance <= attack_range:
                if random.random() < force_push_chance and self.force_push_cooldown <= 0:
                    self.ai_action = 'force_push'
                else:
                    self.ai_action = 'attack'
            else:
                self.ai_action = 'circle'
        
        # Execute AI action
        if self.ai_action == 'approach':
            # Move towards player
            if abs(dx) > 5:
                self.x += self.speed if dx > 0 else -self.speed
            if abs(dy) > 5:
                self.y += self.speed if dy > 0 else -self.speed
            self.sword.active = True
            
        elif self.ai_action == 'dodge':
            # Move away from player
            if distance > 0:
                self.x -= (dx / distance) * self.speed * 1.5
                self.y -= (dy / distance) * self.speed * 1.5
            self.sword.active = True
            
        elif self.ai_action == 'attack':
            # Attack the player
            self.sword.active = True
            swinging = True
            # Update sword targeting
            self.sword.update(self.x, self.y, other_fighter.x, other_fighter.y, swinging)
            # Check combat
            self.check_combat(other_fighter, current_time)
            
        elif self.ai_action == 'force_push':
            # Use force push
            self.use_force_push(other_fighter)
            self.force_push_cooldown = self.force_push_max_cooldown
            self.ai_action = 'attack'  # Switch to attack after force push
            
        elif self.ai_action == 'circle':
            # Circle around the player
            angle = math.atan2(dy, dx) + math.pi/2
            self.x += math.cos(angle) * self.speed
            self.y += math.sin(angle) * self.speed
            self.sword.active = True
        
        # Keep AI on screen
        self.x = max(20, min(SCREEN_WIDTH - 20, self.x))
        self.y = max(20, min(SCREEN_HEIGHT - 20, self.y))
        
        # Always update sword for AI (auto-targeting)
        if not hasattr(self, 'swinging') or self.ai_action != 'attack':
            swinging = self.ai_action == 'attack'
        self.sword.update(self.x, self.y, other_fighter.x, other_fighter.y, swinging)

    def use_force_push(self, other_fighter):
        # Calculate distance and direction
        dx = other_fighter.x - self.x
        dy = other_fighter.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 150:  # Force push range
            # Push other fighter away
            push_strength = 30
            if distance > 0:
                other_fighter.x += (dx / distance) * push_strength
                other_fighter.y += (dy / distance) * push_strength
                other_fighter.take_damage(5)
    
    def check_combat(self, other_fighter, current_time):
        # Check if swords are close enough for combat
        sword_end_x = self.x + math.cos(self.sword.angle) * self.sword.length
        sword_end_y = self.y + math.sin(self.sword.angle) * self.sword.length
        
        distance_to_fighter = math.sqrt((sword_end_x - other_fighter.x)**2 + 
                                      (sword_end_y - other_fighter.y)**2)
        
        # Deal damage if close enough and enough time has passed since last hit
        if distance_to_fighter < 30 and current_time - self.last_hit_time > 200:
            other_fighter.take_damage(10)
            self.last_hit_time = current_time
    
    def take_damage(self, damage):
        current_time = pygame.time.get_ticks()
        if not self.is_invulnerable(current_time):
            self.health -= damage
            self.last_hit_time = current_time
            self.health = max(0, self.health)
    
    def is_invulnerable(self, current_time):
        return current_time - self.last_hit_time < self.invulnerable_time
    
    def draw(self, screen):
        current_time = pygame.time.get_ticks()
        
        # Flash effect when hit
        if self.is_invulnerable(current_time) and (current_time // 100) % 2:
            fighter_color = WHITE
        else:
            fighter_color = self.color
        
        # Draw fighter body
        pygame.draw.circle(screen, fighter_color, (int(self.x), int(self.y)), 15)
        pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), 13)
        
        # Draw sword
        self.sword.draw(screen)
        
        # Health bar
        health_width = 200
        health_height = 20
        if self.is_player1:
            health_x = 50
            health_y = 50
        else:
            health_x = SCREEN_WIDTH - health_width - 50
            health_y = 50
            
        # Health bar background
        pygame.draw.rect(screen, RED, (health_x, health_y, health_width, health_height))
        
        # Health bar fill
        health_fill = (self.health / self.max_health) * health_width
        pygame.draw.rect(screen, GREEN, (health_x, health_y, health_fill, health_height))
        
        # Health bar border
        pygame.draw.rect(screen, WHITE, (health_x, health_y, health_width, health_height), 2)
        
        # Force push cooldown indicator
        if self.force_push_cooldown > 0:
            cooldown_ratio = self.force_push_cooldown / self.force_push_max_cooldown
            cooldown_width = health_width * cooldown_ratio
            pygame.draw.rect(screen, PURPLE, (health_x, health_y + 25, cooldown_width, 10))
        
        # Targeting mode indicator (only for human players)
        if not self.is_ai:
            target_text = "AUTO" if self.auto_target else "MOUSE"
            font = pygame.font.Font(None, 24)
            text_surface = font.render(target_text, True, YELLOW)
            screen.blit(text_surface, (health_x, health_y + 40))
        else:
            # AI difficulty indicator
            font = pygame.font.Font(None, 24)
            text_surface = font.render("AI", True, RED)
            screen.blit(text_surface, (health_x, health_y + 40))

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Plasma Sword Fighter")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Player controls
        player1_controls = {
            'up': pygame.K_w,
            'down': pygame.K_s,
            'left': pygame.K_a,
            'right': pygame.K_d,
            'activate': pygame.K_SPACE,
            'attack': pygame.K_LSHIFT,
            'force': pygame.K_q,
            'toggle_target': pygame.K_t
        }
        
        player2_controls = {
            'up': pygame.K_UP,
            'down': pygame.K_DOWN,
            'left': pygame.K_LEFT,
            'right': pygame.K_RIGHT,
            'activate': pygame.K_RCTRL,
            'attack': pygame.K_RSHIFT,
            'force': pygame.K_RETURN,
            'toggle_target': pygame.K_p
        }
        
        # Create fighters
        self.player1 = Fighter(200, SCREEN_HEIGHT // 2, BLUE, player1_controls, True, False)
        self.player2 = Fighter(SCREEN_WIDTH - 200, SCREEN_HEIGHT // 2, RED, player2_controls, False, True)  # AI player
        
        # Game state
        self.game_over = False
        self.winner = None
        self.ai_difficulty = 'medium'  # easy, medium, hard
        self.difficulty_change_timer = 0
        
        # Font for text
        self.font = pygame.font.Font(None, 74)
        self.small_font = pygame.font.Font(None, 36)
    
    def handle_events(self):
        current_time = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_over:
                    self.restart_game()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_1 and current_time - self.difficulty_change_timer > 500:
                    self.ai_difficulty = 'easy'
                    self.difficulty_change_timer = current_time
                elif event.key == pygame.K_2 and current_time - self.difficulty_change_timer > 500:
                    self.ai_difficulty = 'medium'
                    self.difficulty_change_timer = current_time
                elif event.key == pygame.K_3 and current_time - self.difficulty_change_timer > 500:
                    self.ai_difficulty = 'hard'
                    self.difficulty_change_timer = current_time
    
    def restart_game(self):
        self.player1.health = self.player1.max_health
        self.player2.health = self.player2.max_health
        self.player1.x = 200
        self.player1.y = SCREEN_HEIGHT // 2
        self.player2.x = SCREEN_WIDTH - 200
        self.player2.y = SCREEN_HEIGHT // 2
        self.game_over = False
        self.winner = None
    
    def update(self):
        if not self.game_over:
            keys = pygame.key.get_pressed()
            mouse_pos = pygame.mouse.get_pos()
            
            # Update fighters
            self.player1.update(keys, mouse_pos, self.player2)
            self.player2.update(keys, mouse_pos, self.player1, self.ai_difficulty)
            
            # Check for game over
            if self.player1.health <= 0:
                self.game_over = True
                self.winner = f"AI ({self.ai_difficulty.upper()})"
            elif self.player2.health <= 0:
                self.game_over = True
                self.winner = "Player"
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw background stars
        for _ in range(50):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            pygame.draw.circle(self.screen, WHITE, (x, y), 1)
        
        if not self.game_over:
            # Draw fighters
            self.player1.draw(self.screen)
            self.player2.draw(self.screen)
            
            # Draw instructions
            instructions = [
                "Player: WASD to move, SPACE to activate sword, SHIFT to attack, Q for force push, T to toggle targeting",
                f"AI Difficulty: {self.ai_difficulty.upper()} - Press 1/2/3 to change (Easy/Medium/Hard)"
            ]
            for i, instruction in enumerate(instructions):
                text = self.small_font.render(instruction, True, WHITE)
                self.screen.blit(text, (10, SCREEN_HEIGHT - 60 + i * 25))
        
        else:
            # Draw game over screen
            game_over_text = self.font.render("GAME OVER", True, WHITE)
            winner_text = self.font.render(f"{self.winner} Wins!", True, YELLOW)
            restart_text = self.small_font.render("Press R to restart or ESC to quit", True, WHITE)
            
            # Center the text
            game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            winner_rect = winner_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            
            self.screen.blit(game_over_text, game_over_rect)
            self.screen.blit(winner_text, winner_rect)
            self.screen.blit(restart_text, restart_rect)
        
        pygame.display.flip()
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
