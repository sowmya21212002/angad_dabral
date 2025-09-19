import pygame
import random
import csv
from datetime import datetime
import statistics
import os

# Initialize
pygame.init()
WIDTH, HEIGHT = 1200, 800
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("N-Back Challenge")

font_big = pygame.font.SysFont('Arial', 72, bold=True)
font_medium = pygame.font.SysFont('Arial', 36, bold=True)
font_small = pygame.font.SysFont('Arial', 28)
font_tiny = pygame.font.SysFont('Arial', 20)

# Modern Color Palette
BLACK = (15, 15, 23)
WHITE = (255, 255, 255)
GRAY = (100, 116, 139)
LIGHT_GRAY = (148, 163, 184)
DARK_GRAY = (30, 41, 59)
GREEN = (34, 197, 94)
RED = (239, 68, 68)
BLUE = (59, 130, 246)
YELLOW = (251, 191, 36)
PURPLE = (147, 51, 234)
ACCENT = (16, 185, 129)
SURFACE = (30, 41, 59)
BORDER = (71, 85, 105)

# Grid Configuration
GRID_SIZE = 3
CELL_SIZE = 140
GRID_START_X = WIDTH // 2 - (GRID_SIZE * CELL_SIZE) // 2 - 200
GRID_START_Y = HEIGHT // 2 - (GRID_SIZE * CELL_SIZE) // 2

# Game Configuration
LETTERS = [chr(i) for i in range(65, 75)]  # A-J
stimulus_duration = 2000  # 2 seconds
inter_stimulus_interval = 500  # 0.5 second break
reaction_window = 1500
trial_count = 30
n_back = 1

# Game State
class GameState:
    def __init__(self):
        self.stimuli = []
        self.score = 0
        self.hits = 0
        self.misses = 0
        self.false_alarms = 0
        self.correct_rejections = 0
        self.trial = 0
        self.current_stimulus = None
        self.feedback_text = ""
        self.feedback_color = WHITE
        self.feedback_time = 0
        self.game_phase = "instructions"  # instructions, practice, playing, break, finished
        self.phase_start_time = 0
        self.practice_trials = []
        self.practice_index = 0
        
        # CSV Logging - Single file that keeps appending
        self.filename = "nback_sessions.csv"
        
        # Create header only if file doesn't exist
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Session", "Trial", "Letter", "Position", "IsMatch", "UserPressed", 
                    "Correct", "RT", "Score", "Timestamp", "ResponseType", "Difficulty", 
                    "TrialType", "PrevTrialCorrect", "ConsecutiveErrors", "RTVariability",
                    "PrematureResponse", "LateResponse", "AttentionLapse", "ImpulsivityScore",
                    "WorkingMemoryLoad", "DistractorPresent", "StimulusDuration", "InterTrialInterval"
                ])
        
        # Generate session ID
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Additional ADHD research metrics
        self.reaction_times = []
        self.consecutive_errors = 0
        self.attention_lapses = 0
        self.premature_responses = 0
        self.late_responses = 0

class Stimulus:
    def __init__(self, letter, position, is_match, trial_num):
        self.letter = letter
        self.position = position
        self.is_match = is_match
        self.trial_num = trial_num
        self.shown_time = pygame.time.get_ticks()
        self.responded = False
        self.reaction_time = None
        self.correct = None
        self.user_pressed = False
        self.explanation = ""  # For practice mode

def draw_rounded_rect(surface, color, rect, radius=15):
    """Draw a rounded rectangle"""
    pygame.draw.rect(surface, color, rect, border_radius=radius)

def draw_grid(stimulus=None, highlight_correct=False):
    """Draw the 3x3 grid with modern design"""
    # Draw grid background
    grid_bg = pygame.Rect(GRID_START_X - 20, GRID_START_Y - 20, 
                         GRID_SIZE * CELL_SIZE + 40, GRID_SIZE * CELL_SIZE + 40)
    draw_rounded_rect(win, SURFACE, grid_bg, 20)
    pygame.draw.rect(win, BORDER, grid_bg, 3, border_radius=20)
    
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            x = GRID_START_X + col * CELL_SIZE + 10
            y = GRID_START_Y + row * CELL_SIZE + 10
            rect = pygame.Rect(x, y, CELL_SIZE - 20, CELL_SIZE - 20)
            
            # Cell styling
            if stimulus and stimulus.position == (col, row):
                if highlight_correct:
                    cell_color = GREEN if stimulus.correct else RED
                    draw_rounded_rect(win, cell_color, rect, 12)
                    # Add glow effect
                    glow_rect = pygame.Rect(x - 3, y - 3, CELL_SIZE - 14, CELL_SIZE - 14)
                    pygame.draw.rect(win, cell_color, glow_rect, 4, border_radius=15)
                else:
                    draw_rounded_rect(win, ACCENT, rect, 12)
                    # Subtle shadow
                    shadow_rect = pygame.Rect(x + 2, y + 2, CELL_SIZE - 20, CELL_SIZE - 20)
                    draw_rounded_rect(win, (0, 0, 0, 30), shadow_rect, 12)
            else:
                draw_rounded_rect(win, DARK_GRAY, rect, 12)
                pygame.draw.rect(win, BORDER, rect, 2, border_radius=12)
    
    # Draw the letter with shadow effect
    if stimulus:
        x, y = stimulus.position
        cx = GRID_START_X + x * CELL_SIZE + CELL_SIZE // 2
        cy = GRID_START_Y + y * CELL_SIZE + CELL_SIZE // 2
        
        # Shadow
        shadow_text = font_big.render(stimulus.letter, True, BLACK)
        shadow_rect = shadow_text.get_rect(center=(cx + 3, cy + 3))
        win.blit(shadow_text, shadow_rect)
        
        # Main text
        text = font_big.render(stimulus.letter, True, WHITE)
        text_rect = text.get_rect(center=(cx, cy))
        win.blit(text, text_rect)

def draw_timer_bar(current_time, phase_start_time, duration):
    """Draw a modern timer bar"""
    elapsed = current_time - phase_start_time
    remaining = max(0, duration - elapsed)
    progress = remaining / duration
    
    # Timer bar position
    bar_x = GRID_START_X
    bar_y = GRID_START_Y + GRID_SIZE * CELL_SIZE + 50
    bar_width = GRID_SIZE * CELL_SIZE
    bar_height = 25
    
    # Background with rounded corners
    bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
    draw_rounded_rect(win, DARK_GRAY, bg_rect, 12)
    
    # Progress bar with gradient effect
    if progress > 0:
        if progress > 0.6:
            color = GREEN
        elif progress > 0.3:
            color = YELLOW
        else:
            color = RED
        
        progress_width = int(bar_width * progress)
        progress_rect = pygame.Rect(bar_x, bar_y, progress_width, bar_height)
        draw_rounded_rect(win, color, progress_rect, 12)
        
        # Add shine effect
        shine_rect = pygame.Rect(bar_x, bar_y, progress_width, bar_height // 2)
        shine_color = tuple(min(255, c + 40) for c in color)
        draw_rounded_rect(win, shine_color, shine_rect, 12)
    
    # Border
    pygame.draw.rect(win, BORDER, bg_rect, 2, border_radius=12)
    
    # Time text with background
    time_left = remaining / 1000.0
    time_text = font_small.render(f"{time_left:.1f}s", True, WHITE)
    text_bg = pygame.Rect(bar_x + bar_width - 80, bar_y + 30, 75, 35)
    draw_rounded_rect(win, SURFACE, text_bg, 8)
    win.blit(time_text, (bar_x + bar_width - 75, bar_y + 35))

def draw_previous_trial_reference(game_state):
    """Show previous trial in a modern card design"""
    if game_state.trial > 0 and len(game_state.stimuli) > 0:
        prev_index = max(0, len(game_state.stimuli) - 2)
        if prev_index >= 0 and prev_index < len(game_state.stimuli):
            prev_stimulus = game_state.stimuli[prev_index]
            
            # Card position and size
            card_x = 50
            card_y = 50
            card_width = 200
            card_height = 160
            
            # Card background
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            draw_rounded_rect(win, SURFACE, card_rect, 15)
            pygame.draw.rect(win, BORDER, card_rect, 2, border_radius=15)
            
            # Header
            header_rect = pygame.Rect(card_x, card_y, card_width, 35)
            draw_rounded_rect(win, BLUE, header_rect, 15)
            header_text = font_small.render("Previous Trial", True, WHITE)
            header_text_rect = header_text.get_rect(center=(card_x + card_width//2, card_y + 17))
            win.blit(header_text, header_text_rect)
            
            # Letter display
            letter_y = card_y + 50
            letter_text = font_big.render(f"'{prev_stimulus.letter}'", True, WHITE)
            letter_rect = letter_text.get_rect(center=(card_x + card_width//2, letter_y + 25))
            win.blit(letter_text, letter_rect)
            
            # Position info
            pos_text = font_small.render(f"Position: ({prev_stimulus.position[0]}, {prev_stimulus.position[1]})", True, LIGHT_GRAY)
            pos_rect = pos_text.get_rect(center=(card_x + card_width//2, letter_y + 60))
            win.blit(pos_text, pos_rect)
            
            # Mini grid
            mini_size = 12
            mini_x = card_x + card_width//2 - (GRID_SIZE * mini_size)//2
            mini_y = letter_y + 85
            
            for row in range(GRID_SIZE):
                for col in range(GRID_SIZE):
                    mini_rect = pygame.Rect(mini_x + col * mini_size + col * 2, 
                                          mini_y + row * mini_size + row * 2, mini_size, mini_size)
                    if (col, row) == prev_stimulus.position:
                        draw_rounded_rect(win, ACCENT, mini_rect, 3)
                    else:
                        draw_rounded_rect(win, DARK_GRAY, mini_rect, 3)
                    pygame.draw.rect(win, BORDER, mini_rect, 1, border_radius=3)

def draw_info_panel(game_state):
    """Draw the modern information panel"""
    panel_x = GRID_START_X + GRID_SIZE * CELL_SIZE + 80
    panel_y = 80
    panel_width = 300
    
    # Main panel background
    panel_bg = pygame.Rect(panel_x - 20, panel_y - 20, panel_width + 40, 500)
    draw_rounded_rect(win, SURFACE, panel_bg, 15)
    pygame.draw.rect(win, BORDER, panel_bg, 2, border_radius=15)
    
    # Title with gradient background
    title_bg = pygame.Rect(panel_x - 10, panel_y - 10, panel_width + 20, 50)
    draw_rounded_rect(win, PURPLE, title_bg, 12)
    title = font_medium.render("N-Back Challenge", True, WHITE)
    title_rect = title.get_rect(center=(panel_x + panel_width//2, panel_y + 15))
    win.blit(title, title_rect)
    
    # Progress section
    progress_y = panel_y + 70
    progress_text = font_small.render(f"Trial {game_state.trial + 1} of {trial_count}", True, WHITE)
    win.blit(progress_text, (panel_x, progress_y))
    
    # Progress bar
    prog_bar_rect = pygame.Rect(panel_x, progress_y + 30, panel_width - 20, 8)
    draw_rounded_rect(win, DARK_GRAY, prog_bar_rect, 4)
    progress_fill = int((panel_width - 20) * (game_state.trial + 1) / trial_count)
    if progress_fill > 0:
        fill_rect = pygame.Rect(panel_x, progress_y + 30, progress_fill, 8)
        draw_rounded_rect(win, ACCENT, fill_rect, 4)
    
    # Score section
    score_y = progress_y + 70
    score_bg = pygame.Rect(panel_x, score_y, panel_width - 20, 50)
    draw_rounded_rect(win, YELLOW if game_state.score >= 0 else RED, score_bg, 10)
    score_text = font_medium.render(f"Score: {game_state.score}", True, BLACK)
    score_rect = score_text.get_rect(center=(panel_x + (panel_width - 20)//2, score_y + 25))
    win.blit(score_text, score_rect)
    
    # Statistics section
    stats_y = score_y + 80
    stats_title = font_small.render("Performance", True, ACCENT)
    win.blit(stats_title, (panel_x, stats_y))
    
    stats = [
        ("Hits", game_state.hits, GREEN),
        ("Misses", game_state.misses, RED),
        ("False Alarms", game_state.false_alarms, RED),
        ("Correct Rejections", game_state.correct_rejections, GREEN)
    ]
    
    for i, (label, value, color) in enumerate(stats):
        y_pos = stats_y + 30 + i * 30
        label_text = font_tiny.render(f"{label}:", True, LIGHT_GRAY)
        value_text = font_tiny.render(str(value), True, color)
        win.blit(label_text, (panel_x, y_pos))
        win.blit(value_text, (panel_x + 150, y_pos))
    
    # Instructions section
    inst_y = stats_y + 180
    inst_bg = pygame.Rect(panel_x, inst_y, panel_width - 20, 120)
    draw_rounded_rect(win, DARK_GRAY, inst_bg, 10)
    
    inst_title = font_small.render("Quick Guide", True, BLUE)
    win.blit(inst_title, (panel_x + 10, inst_y + 10))
    
    instructions = [
        "• Press SPACE for match",
        "• Both letter & position",
        "  must match previous",
        "• +10 hit, -5 miss/alarm"
    ]
    
    for i, line in enumerate(instructions):
        text = font_tiny.render(line, True, LIGHT_GRAY)
        win.blit(text, (panel_x + 10, inst_y + 40 + i * 20))

def draw_feedback(game_state):
    """Draw modern feedback with animations"""
    if game_state.feedback_text and pygame.time.get_ticks() - game_state.feedback_time < 1200:
        # Feedback bubble
        bubble_x = WIDTH // 2 - 150
        bubble_y = HEIGHT - 120
        bubble_width = 300
        bubble_height = 60
        
        # Bubble background with glow
        glow_rect = pygame.Rect(bubble_x - 5, bubble_y - 5, bubble_width + 10, bubble_height + 10)
        draw_rounded_rect(win, game_state.feedback_color, glow_rect, 20)
        
        bubble_rect = pygame.Rect(bubble_x, bubble_y, bubble_width, bubble_height)
        draw_rounded_rect(win, SURFACE, bubble_rect, 15)
        pygame.draw.rect(win, game_state.feedback_color, bubble_rect, 3, border_radius=15)
        
        # Feedback text
        feedback_surface = font_tiny.render(game_state.feedback_text, True, game_state.feedback_color)
        feedback_rect = feedback_surface.get_rect(center=(bubble_x + bubble_width//2, bubble_y + bubble_height//2))
        win.blit(feedback_surface, feedback_rect)

def draw_instructions():
    """Draw the initial instructions screen"""
    win.fill(BLACK)
    
    title = font_big.render("N-Back Memory Challenge", True, BLUE)
    title_rect = title.get_rect(center=(WIDTH//2, 80))
    win.blit(title, title_rect)
    
    # Main rule in big text
    rule = font_medium.render("RULE: Press SPACE only when BOTH letter AND position", True, YELLOW)
    rule2 = font_medium.render("match the trial shown 1 step back", True, YELLOW)
    rule_rect = rule.get_rect(center=(WIDTH//2, 130))
    rule2_rect = rule2.get_rect(center=(WIDTH//2, 160))
    win.blit(rule, rule_rect)
    win.blit(rule2, rule2_rect)
    
    instructions = [
        "",
        "",
        "Trial 1: 'A' in top-left      → (First trial, do nothing)",
        "Trial 2: 'B' in center        → Do nothing (doesn't match trial 1)",
        "Trial 3: 'B' in center        → PRESS SPACE! (matches trial 2 exactly)",
        "Trial 4: 'B' in top-right     → Do nothing (same letter, wrong position)",
        "Trial 5: 'C' in center        → Do nothing (wrong letter, even if same position)",
        "",
        "WHAT COUNTS AS A MATCH:",
        "- Same letter + Same position as 1 trial ago",
        "- Same letter but different position",
        "- Different letter but same position",
        "- Completely different",
        "",
        "Press P for Practice Mode or ENTER to start the real game!"
    ]
    
    y = 200
    for line in instructions:
        if line.startswith("EXAMPLE") or line.startswith("WHAT COUNTS"):
            color = YELLOW
        elif "PRESS SPACE!" in line:
            color = GREEN
        elif "Do nothing" in line:
            color = RED
        elif line.startswith("✓"):
            color = GREEN
        elif line.startswith("✗"):
            color = RED
        elif line.startswith("Trial"):
            color = LIGHT_GRAY
        else:
            color = WHITE
            
        text = font_small.render(line, True, color)
        text_rect = text.get_rect(center=(WIDTH//2, y))
        win.blit(text, text_rect)
        y += 25

def setup_practice_mode(game_state):
    """Setup predefined practice trials to demonstrate the concept clearly"""
    practice_data = [
        ('A', (0, 0), False, "First trial - nothing to compare"),
        ('B', (1, 1), False, "Different from trial 1 - do nothing"),
        ('B', (1, 1), True, "MATCH! Same as trial 2 - PRESS SPACE!"),
        ('B', (2, 0), False, "Same letter but different position - do nothing"),
        ('C', (1, 1), False, "Different letter, even though same position - do nothing"),
        ('C', (1, 1), True, "MATCH! Same as trial 5 - PRESS SPACE!")
    ]
    
    game_state.practice_trials = []
    for i, (letter, pos, is_match, explanation) in enumerate(practice_data):
        stimulus = Stimulus(letter, pos, is_match, i)
        stimulus.explanation = explanation
        game_state.practice_trials.append(stimulus)

def draw_practice_screen(game_state):
    """Draw the practice mode screen with explanations"""
    win.fill(BLACK)
    
    if game_state.practice_index < len(game_state.practice_trials):
        current = game_state.practice_trials[game_state.practice_index]
        
        # Draw grid with current stimulus
        draw_grid(current)
        
        # Draw trial information
        trial_text = font_medium.render(f"Practice Trial {game_state.practice_index + 1} of {len(game_state.practice_trials)}", True, BLUE)
        win.blit(trial_text, (50, 50))
        
        # Draw explanation
        explanation_lines = [
            f"Current: '{current.letter}' at position ({current.position[0]}, {current.position[1]})",
            "",
            current.explanation
        ]
        
        if game_state.practice_index > 0:
            prev = game_state.practice_trials[game_state.practice_index - 1]
            explanation_lines.insert(1, f"Previous: '{prev.letter}' at position ({prev.position[0]}, {prev.position[1]})")
        
        y = HEIGHT - 200
        for line in explanation_lines:
            if "MATCH!" in line or "PRESS SPACE!" in line:
                color = GREEN
            elif "do nothing" in line:
                color = RED
            elif "Current:" in line or "Previous:" in line:
                color = LIGHT_GRAY
            else:
                color = WHITE
            
            text = font_small.render(line, True, color)
            win.blit(text, (50, y))
            y += 30
        
        # Instructions
        instruction_text = "Press SPACE if you think this is a match, or any other key to continue"
        instruction = font_tiny.render(instruction_text, True, YELLOW)
        win.blit(instruction, (50, HEIGHT - 50))
    
    else:
        # Practice complete
        win.fill(BLACK)
        complete_text = font_big.render("Practice Complete!", True, GREEN)
        complete_rect = complete_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
        win.blit(complete_text, complete_rect)
        
        ready_text = font_medium.render("Ready for the real game? Press ENTER to start!", True, WHITE)
        ready_rect = ready_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))
        win.blit(ready_text, ready_rect)

def generate_trial(game_state):
    """Generate the next trial stimulus"""
    trial_index = game_state.trial
    
    # For the first trial, or if we want a non-match
    if trial_index < n_back or random.random() > 0.4:  # 40% match rate
        # Generate a non-match
        letter = random.choice(LETTERS)
        position = (random.randint(0, 2), random.randint(0, 2))
        
        # Make sure it's actually different from the n-back stimulus
        if trial_index >= n_back:
            past_stimulus = game_state.stimuli[trial_index - n_back]
            while letter == past_stimulus.letter and position == past_stimulus.position:
                letter = random.choice(LETTERS)
                position = (random.randint(0, 2), random.randint(0, 2))
        
        return Stimulus(letter, position, False, trial_index)
    else:
        # Generate a match
        past_stimulus = game_state.stimuli[trial_index - n_back]
        return Stimulus(past_stimulus.letter, past_stimulus.position, True, trial_index)

def calculate_adhd_metrics(game_state, stimulus):
    """Calculate ADHD-specific behavioral metrics"""
    
    # Response classification
    if stimulus.user_pressed and stimulus.is_match:
        response_type = "Hit"
    elif stimulus.user_pressed and not stimulus.is_match:
        response_type = "FalseAlarm"
    elif not stimulus.user_pressed and stimulus.is_match:
        response_type = "Miss"
    else:
        response_type = "CorrectRejection"
    
    # RT-based classifications
    premature = False
    late_response = False
    attention_lapse = False
    
    if stimulus.reaction_time:
        if stimulus.reaction_time < 200:  # Too fast - impulsive
            premature = True
            game_state.premature_responses += 1
        elif stimulus.reaction_time > 1800:  # Very slow
            late_response = True
            game_state.late_responses += 1
        
        game_state.reaction_times.append(stimulus.reaction_time)
    
    # Attention lapse detection (no response to target)
    if stimulus.is_match and not stimulus.user_pressed:
        attention_lapse = True
        game_state.attention_lapses += 1
    
    # Consecutive errors tracking
    if not stimulus.correct:
        game_state.consecutive_errors += 1
    else:
        game_state.consecutive_errors = 0
    
    # RT Variability (using last 5 trials)
    rt_variability = 0
    if len(game_state.reaction_times) >= 3:
        recent_rts = [rt for rt in game_state.reaction_times[-5:] if rt is not None]
        if len(recent_rts) >= 3:
            rt_variability = statistics.stdev(recent_rts)
    
    # Working memory load (distance from target)
    wm_load = min(game_state.trial + 1, n_back)
    
    # Trial difficulty (based on similarity to n-back stimulus)
    difficulty = "Easy"
    if game_state.trial >= n_back:
        past_stimulus = game_state.stimuli[game_state.trial - n_back]
        if stimulus.letter == past_stimulus.letter and stimulus.position != past_stimulus.position:
            difficulty = "Hard"  # Same letter, different position
        elif stimulus.letter != past_stimulus.letter and stimulus.position == past_stimulus.position:
            difficulty = "Medium"  # Different letter, same position
    
    # Impulsivity score (based on premature responses and false alarms)
    impulsivity_score = 0
    if premature:
        impulsivity_score += 2
    if response_type == "FalseAlarm":
        impulsivity_score += 1
    
    # Previous trial correctness
    prev_correct = True
    if len(game_state.stimuli) > 1:
        prev_correct = game_state.stimuli[-2].correct
    
    return {
        'response_type': response_type,
        'difficulty': difficulty,
        'trial_type': "Target" if stimulus.is_match else "NonTarget",
        'prev_correct': prev_correct,
        'consecutive_errors': game_state.consecutive_errors,
        'rt_variability': round(rt_variability, 2),
        'premature': premature,
        'late_response': late_response,
        'attention_lapse': attention_lapse,
        'impulsivity_score': impulsivity_score,
        'wm_load': wm_load,
        'distractor_present': False,  # Can be expanded later
        'stimulus_duration': stimulus_duration,
        'inter_trial_interval': inter_stimulus_interval
    }

def handle_response(game_state, pressed_space):
    """Handle user response and update score"""
    stimulus = game_state.current_stimulus
    stimulus.user_pressed = pressed_space
    stimulus.responded = True
    
    if pressed_space:
        stimulus.reaction_time = pygame.time.get_ticks() - stimulus.shown_time
    
    # Determine correctness
    if stimulus.is_match and pressed_space:
        # Hit
        stimulus.correct = True
        game_state.hits += 1
        game_state.score += 10
        game_state.feedback_text = "HIT! +10"
        game_state.feedback_color = GREEN
    elif stimulus.is_match and not pressed_space:
        # Miss
        stimulus.correct = False
        game_state.misses += 1
        game_state.score -= 5
        game_state.feedback_text = "MISS! -5"
        game_state.feedback_color = RED
    elif not stimulus.is_match and pressed_space:
        # False Alarm
        stimulus.correct = False
        game_state.false_alarms += 1
        game_state.score -= 5
        game_state.feedback_text = "FALSE ALARM! -5"
        game_state.feedback_color = RED
    else:
        # Correct Rejection
        stimulus.correct = True
        game_state.correct_rejections += 1
        game_state.feedback_text = "CORRECT!"
        game_state.feedback_color = GREEN
    
    game_state.feedback_time = pygame.time.get_ticks()
    
    # Calculate ADHD metrics
    metrics = calculate_adhd_metrics(game_state, stimulus)
    
    # Log to CSV - append to single file
    with open(game_state.filename, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            game_state.session_id,
            game_state.trial + 1,
            stimulus.letter,
            f"({stimulus.position[0]},{stimulus.position[1]})",
            "Yes" if stimulus.is_match else "No",
            "Yes" if stimulus.user_pressed else "No",
            "Yes" if stimulus.correct else "No",
            stimulus.reaction_time if stimulus.reaction_time else "",
            game_state.score,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            metrics['response_type'],
            metrics['difficulty'],
            metrics['trial_type'],
            "Yes" if metrics['prev_correct'] else "No",
            metrics['consecutive_errors'],
            metrics['rt_variability'],
            "Yes" if metrics['premature'] else "No",
            "Yes" if metrics['late_response'] else "No",
            "Yes" if metrics['attention_lapse'] else "No",
            metrics['impulsivity_score'],
            metrics['wm_load'],
            "Yes" if metrics['distractor_present'] else "No",
            metrics['stimulus_duration'],
            metrics['inter_trial_interval']
        ])

def draw_final_summary(game_state):
    """Draw the final results screen"""
    win.fill(BLACK)
    
    # Calculate accuracy
    total_responses = game_state.hits + game_state.misses + game_state.false_alarms + game_state.correct_rejections
    accuracy = (game_state.hits + game_state.correct_rejections) / total_responses * 100 if total_responses > 0 else 0
    
    title = font_big.render("Game Complete!", True, BLUE)
    title_rect = title.get_rect(center=(WIDTH//2, 100))
    win.blit(title, title_rect)
    
    results = [
        f"Final Score: {game_state.score}",
        f"Accuracy: {accuracy:.1f}%",
        "",
        f"Hits: {game_state.hits}",
        f"Misses: {game_state.misses}",
        f"False Alarms: {game_state.false_alarms}",
        f"Correct Rejections: {game_state.correct_rejections}",
        "",
        #f"Data saved to: {game_state.filename} (Session: {game_state.session_id})",
        "",
        "Press ESC to exit"
    ]
    
    y = 200
    for line in results:
        if "Final Score" in line:
            color = YELLOW
        elif "Accuracy" in line:
            color = GREEN if accuracy >= 70 else RED
        elif line.startswith("Data saved"):
            color = LIGHT_GRAY
        else:
            color = WHITE
            
        text = font_medium.render(line, True, color)
        text_rect = text.get_rect(center=(WIDTH//2, y))
        win.blit(text, text_rect)
        y += 40

def main():
    game_state = GameState()
    clock = pygame.time.Clock()
    running = True
    
    while running:
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if game_state.game_phase == "instructions":
                    if event.key == pygame.K_RETURN:
                        game_state.game_phase = "playing"
                        game_state.phase_start_time = current_time
                    elif event.key == pygame.K_p:
                        game_state.game_phase = "practice"
                        setup_practice_mode(game_state)
                        game_state.phase_start_time = current_time
                
                elif game_state.game_phase == "practice":
                    if game_state.practice_index < len(game_state.practice_trials):
                        current = game_state.practice_trials[game_state.practice_index]
                        user_thinks_match = (event.key == pygame.K_SPACE)
                        
                        # Show feedback
                        if user_thinks_match == current.is_match:
                            game_state.feedback_text = "Correct! " + ("This WAS a match" if current.is_match else "This was NOT a match")
                            game_state.feedback_color = GREEN
                        else:
                            if current.is_match:
                                game_state.feedback_text = "Incorrect. This WAS a match - should press SPACE"
                            else:
                                game_state.feedback_text = "Incorrect. This was NOT a match"
                            game_state.feedback_color = RED
                        
                        game_state.feedback_time = current_time
                        game_state.practice_index += 1
                    else:
                        if event.key == pygame.K_RETURN:
                            game_state.game_phase = "playing"
                            game_state.phase_start_time = current_time
                
                elif game_state.game_phase == "playing" and event.key == pygame.K_SPACE:
                    if game_state.current_stimulus and not game_state.current_stimulus.responded:
                        handle_response(game_state, True)
                
                elif game_state.game_phase == "finished" and event.key == pygame.K_ESCAPE:
                    running = False
        
        # Game logic
        if game_state.game_phase == "instructions":
            draw_instructions()
        
        elif game_state.game_phase == "practice":
            draw_practice_screen(game_state)
            draw_feedback(game_state)
        
        elif game_state.game_phase == "playing":
            if game_state.trial >= trial_count:
                game_state.game_phase = "finished"
            
            elif game_state.current_stimulus is None:
                # Start new trial
                game_state.current_stimulus = generate_trial(game_state)
                game_state.stimuli.append(game_state.current_stimulus)
                game_state.phase_start_time = current_time
            
            elif current_time - game_state.phase_start_time >= stimulus_duration:
                # Time up for current stimulus
                if not game_state.current_stimulus.responded:
                    handle_response(game_state, False)
                
                # Move to break phase
                game_state.game_phase = "break"
                game_state.phase_start_time = current_time
            
            else:
                # Draw current trial
                win.fill(BLACK)
                draw_grid(game_state.current_stimulus)
                draw_timer_bar(current_time, game_state.phase_start_time, stimulus_duration)
                draw_previous_trial_reference(game_state)
                draw_info_panel(game_state)
                draw_feedback(game_state)
        
        elif game_state.game_phase == "break":
            if current_time - game_state.phase_start_time >= inter_stimulus_interval:
                # Break over, prepare next trial
                game_state.trial += 1
                game_state.current_stimulus = None
                game_state.game_phase = "playing"
            else:
                # Show break screen with feedback
                win.fill(BLACK)
                
                # Show "Processing..." or break message
                break_text = font_medium.render("", True, YELLOW)
                break_rect = break_text.get_rect(center=(WIDTH//2 - 75, HEIGHT//2))
                win.blit(break_text, break_rect)
                
                # Show what just happened
                if len(game_state.stimuli) > 0:
                    draw_grid(game_state.stimuli[-1], highlight_correct=True)
                
                draw_info_panel(game_state)
                draw_feedback(game_state)
        
        elif game_state.game_phase == "finished":
            draw_final_summary(game_state)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()

if __name__ == "__main__":
    main()