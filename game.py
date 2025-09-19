import pygame
import random
import csv
from datetime import datetime

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 800, 600
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Alien Defense Simulator")

# Load Fonts & Sounds
font = pygame.font.SysFont('consolas', 24)
try:
    shoot_sound = pygame.mixer.Sound('laser.wav')  # Optional
    bg_music = 'background_music.mp3'              # Optional
    pygame.mixer.music.load(bg_music)
    pygame.mixer.music.play(-1)
except:
    shoot_sound = None

# Colors
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)

# Create Alien Sprites
def create_alien(color):
    surf = pygame.Surface((50, 50))
    surf.fill(color)
    pygame.draw.circle(surf, (0, 0, 0), (25, 25), 20, 2)
    return surf

RED_ALIEN = create_alien(RED)
GREEN_ALIEN = create_alien(GREEN)
EXPLOSION = create_alien(YELLOW)

# Crosshair
CROSSHAIR = pygame.Surface((25, 25), pygame.SRCALPHA)
pygame.draw.circle(CROSSHAIR, WHITE, (12, 12), 10, 2)

# Background stars
stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT)) for _ in range(80)]

# Game Variables
FPS = 60
clock = pygame.time.Clock()
score = 0
hits = 0
misses = 0
aliens = []
next_spawn_time = 0

# Speed control
alien_speed = 2
spawn_delay = 1000
min_spawn_delay = 200
max_alien_speed = 6
difficulty_timer = 0
difficulty_interval = 5000  # every 5 seconds

# Timing
game_duration = 60  # seconds
start_time = pygame.time.get_ticks()

import os

filename = "adhd_log.csv"
write_header = not os.path.exists(filename)

if write_header:
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Stimulus", "Action", "Correct", "Reaction_Time_ms"])


# Alien Class
class Alien:
    def __init__(self, kind):
        self.kind = kind
        self.image = RED_ALIEN if kind == "go" else GREEN_ALIEN
        self.x = random.randint(100, WIDTH - 100)
        self.y = -60
        self.spawn_time = pygame.time.get_ticks()
        self.responded = False
        self.exploding = False
        self.explode_time = 0
        self.rect = self.image.get_rect(topleft=(self.x, self.y))

    def update(self):
        if not self.exploding:
            self.y += alien_speed
            self.rect.y = self.y

    def draw(self, win):
        if self.exploding:
            win.blit(EXPLOSION, (self.x, self.y))
        else:
            win.blit(self.image, (self.x, self.y))

    def trigger_explosion(self):
        self.exploding = True
        self.explode_time = pygame.time.get_ticks()

# Helper Functions
def draw_background():
    win.fill((5, 5, 30))
    for x, y in stars:
        pygame.draw.circle(win, WHITE, (x, y), 1)

def draw_scoreboard():
    info = f"Score: {score} | Hits: {hits} | Misses: {misses}"
    text = font.render(info, True, WHITE)
    win.blit(text, (10, 10))

def draw_crosshair():
    mx, my = pygame.mouse.get_pos()
    win.blit(CROSSHAIR, (mx - 12, my - 12))

def log_response(alien, action, correct, rt):
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Go" if alien.kind == "go" else "No-Go",
            action,
            "Yes" if correct else "No",
            rt if rt is not None else ""
        ])

# Game Loop
run = True
pygame.mouse.set_visible(False)

while run:
    clock.tick(FPS)
    now = pygame.time.get_ticks()
    elapsed_sec = (now - start_time) / 1000

    # End after game_duration
    if elapsed_sec > game_duration:
        run = False
        continue

    # Increase difficulty every 5 seconds
    if now - difficulty_timer > difficulty_interval:
        difficulty_timer = now
        if spawn_delay > min_spawn_delay:
            spawn_delay = max(spawn_delay - 150, min_spawn_delay)
        if alien_speed < max_alien_speed:
            alien_speed = min(alien_speed + 0.7, max_alien_speed)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            for alien in aliens:
                if not alien.responded and alien.rect.collidepoint(mx, my):
                    rt = now - alien.spawn_time
                    alien.responded = True
                    alien.trigger_explosion()
                    if alien.kind == "go":
                        score += 10
                        hits += 1
                        log_response(alien, "Shoot", True, rt)
                    else:
                        score -= 5
                        misses += 1
                        log_response(alien, "Shoot", False, rt)
                    if shoot_sound:
                        shoot_sound.play()
                    break

    # Spawn new alien
    if now >= next_spawn_time:
        kind = "go" if random.random() < 0.7 else "nogo"
        aliens.append(Alien(kind))
        next_spawn_time = now + spawn_delay

    # Update aliens
    for alien in aliens:
        alien.update()

    # Remove expired or finished aliens
    for alien in aliens[:]:
        if not alien.responded and alien.y > HEIGHT:
            alien.responded = True
            if alien.kind == "go":
                log_response(alien, "No Shot", False, None)
                misses += 1
            else:
                log_response(alien, "No Shot", True, None)
            aliens.remove(alien)
        elif alien.exploding and now - alien.explode_time > 250:
            aliens.remove(alien)

    # Drawing
    draw_background()
    for alien in aliens:
        alien.draw(win)
    draw_scoreboard()
    draw_crosshair()
    pygame.display.update()

# Game Over Screen
win.fill((0, 0, 0))
end_text = font.render(f"Game Over! Final Score: {score}", True, YELLOW)
win.blit(end_text, (WIDTH // 2 - end_text.get_width() // 2, HEIGHT // 2))
pygame.display.update()
pygame.time.delay(4000)
pygame.quit()
