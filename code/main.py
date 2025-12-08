# main.py
import pygame
import math
from settings import *
from player import Player
from ghost import Ghost

pygame.init()
pygame.font.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pac-Man: Advanced (Roguelike & Algorithms)")
clock = pygame.time.Clock()

game_logs = []
MAX_LOGS = 7

def log_message(message):
    ticks = pygame.time.get_ticks() // 1000
    formatted_msg = f"[{ticks}s] {message}"
    print(formatted_msg)
    game_logs.append(formatted_msg)
    if len(game_logs) > MAX_LOGS:
        game_logs.pop(0)

def draw_logs(surface):
    log_area_rect = pygame.Rect(0, MAP_HEIGHT, SCREEN_WIDTH, LOG_HEIGHT)
    pygame.draw.rect(surface, (20, 20, 20), log_area_rect)
    pygame.draw.line(surface, WHITE, (0, MAP_HEIGHT), (SCREEN_WIDTH, MAP_HEIGHT), 2)
    
    start_y = MAP_HEIGHT + 10
    info_text = f"LIVES: {player_lives} / {MAX_LIVES}   LEVEL: {current_level}   ALGO: {selected_algorithm}"
    info_surf = LOG_FONT.render(info_text, True, YELLOW)
    surface.blit(info_surf, (10, start_y))
    
    for i, msg in enumerate(game_logs):
        text_surf = LOG_FONT.render(msg, True, WHITE)
        surface.blit(text_surf, (10, start_y + 20 + i * 18))

def draw_map():
    for y, row in enumerate(GAME_MAP):
        for x, char in enumerate(row):
            rect_x = x * TILE_SIZE
            rect_y = y * TILE_SIZE
            if char == TILE_WALL:
                pygame.draw.rect(screen, BLUE, (rect_x, rect_y, TILE_SIZE, TILE_SIZE))
            elif char == TILE_DOOR:
                pygame.draw.line(screen, GREY, (rect_x, rect_y + TILE_SIZE//2), (rect_x + TILE_SIZE, rect_y + TILE_SIZE//2), 2)
            elif char == TILE_PELLET:
                pygame.draw.circle(screen, WHITE, (rect_x + TILE_SIZE // 2, rect_y + TILE_SIZE // 2), 2)
            elif char == TILE_POWER_PELLET:
                pygame.draw.circle(screen, WHITE, (rect_x + TILE_SIZE // 2, rect_y + TILE_SIZE // 2), 6)

# --- 全局變數 ---
player_lives = MAX_LIVES
current_level = 1
selected_algorithm = ALGO_ASTAR

player = None
ghosts = []
total_pellets = 0
running = True
game_state = GAME_STATE_MENU
frightened_mode = False
frightened_start_time = 0
global_ghost_mode = MODE_SCATTER
last_mode_switch_time = 0

# 鬼魂散開點 (因為是隨機地圖，設為角落較安全)
path_blinky = [(26, 1)]
path_pinky = [(1, 1)]
path_inky = [(26, 28)]
path_clyde = [(1, 28)]

def init_level(new_level=False):
    global player, ghosts, total_pellets, GAME_MAP
    
    if new_level:
        GAME_MAP[:] = generate_random_map()
        log_message(f"--- Level {current_level} Generated ---")
    
    # 尋找安全的玩家出生點 (非牆壁)
    spawn_x, spawn_y = 13.5, 23
    # 簡單搜尋附近空格
    if GAME_MAP[23][13] == TILE_WALL:
        found = False
        for y in range(20, 28):
            for x in range(1, 27):
                if GAME_MAP[y][x] != TILE_WALL:
                    spawn_x, spawn_y = x + 0.5, y
                    found = True
                    break
            if found: break

    old_score = 0
    if player: old_score = player.score
    player = Player(spawn_x, spawn_y)
    player.score = old_score

    # 重置鬼魂
    blinky = Ghost(13, 14, RED, ai_mode=AI_CHASE_BLINKY, chosen_algorithm=selected_algorithm,
                   scatter_point=path_blinky, in_house=True, delay=0, on_log=log_message)
    pinky = Ghost(14, 14, PINK, ai_mode=AI_CHASE_PINKY, chosen_algorithm=selected_algorithm,
                  scatter_point=path_pinky, in_house=True, delay=3000, on_log=log_message)
    inky = Ghost(12, 14, CYAN, ai_mode=AI_CHASE_INKY, chosen_algorithm=selected_algorithm, scatter_point=path_inky,
                 in_house=True, delay=6000, on_log=log_message)
    clyde = Ghost(15, 14, ORANGE, ai_mode=AI_CHASE_CLYDE, chosen_algorithm=selected_algorithm,
                  scatter_point=path_clyde, in_house=True, delay=9000, on_log=log_message)
    
    ghosts[:] = [blinky, pinky, inky, clyde]

    if new_level:
        total_pellets = sum(row.count(TILE_PELLET) for row in GAME_MAP)
        log_message(f"Total pellets: {total_pellets}")

def reset_game_totally():
    global player_lives, current_level, game_state
    player_lives = MAX_LIVES
    current_level = 1
    game_state = GAME_STATE_MENU
    log_message("Game Reset to Menu")

while running:
    dt = clock.tick(60)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if game_state == GAME_STATE_MENU:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    selected_algorithm = ALGO_BFS
                    game_state = GAME_STATE_START
                    init_level(new_level=True)
                elif event.key == pygame.K_2:
                    selected_algorithm = ALGO_DFS
                    game_state = GAME_STATE_START
                    init_level(new_level=True)
                elif event.key == pygame.K_3:
                    selected_algorithm = ALGO_ASTAR
                    game_state = GAME_STATE_START
                    init_level(new_level=True)
                    
        elif game_state == GAME_STATE_START:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                    game_state = GAME_STATE_PLAYING
                    last_mode_switch_time = pygame.time.get_ticks()
                    log_message("GO!")
                    player.handle_input(event)

        elif game_state == GAME_STATE_PLAYING:
            player.handle_input(event)

        elif game_state in [GAME_STATE_GAME_OVER, GAME_STATE_WIN]:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game_totally()

    if game_state == GAME_STATE_PLAYING:
        current_time = pygame.time.get_ticks()

        if not frightened_mode:
            time_passed = current_time - last_mode_switch_time
            if global_ghost_mode == MODE_SCATTER and time_passed > SCATTER_DURATION:
                global_ghost_mode = MODE_CHASE
                last_mode_switch_time = current_time
                log_message(">> CHASE MODE")
            elif global_ghost_mode == MODE_CHASE and time_passed > CHASE_DURATION:
                global_ghost_mode = MODE_SCATTER
                last_mode_switch_time = current_time
                log_message(">> SCATTER MODE")

        # Ghost Update
        blinky_pos = (ghosts[0].grid_x, ghosts[0].grid_y)
        for ghost in ghosts:
             if (not ghost.is_frightened and not ghost.is_eaten and ghost.current_ai_mode not in [MODE_GO_HOME, MODE_EXIT_HOUSE, MODE_WAITING]):
                if global_ghost_mode == MODE_SCATTER: ghost.current_ai_mode = MODE_SCATTER
                elif global_ghost_mode == MODE_CHASE: ghost.current_ai_mode = ghost.ai_mode
             ghost.update(GAME_MAP, player, ghosts, dt, global_ghost_mode, blinky_pos)

        # Frightened Timer
        if frightened_mode:
            if current_time - frightened_start_time > FRIGHTENED_DURATION:
                frightened_mode = False
                log_message("Frightened mode ended.")
                for ghost in ghosts: ghost.end_frightened()
                last_mode_switch_time = current_time

        # Player Update
        status = player.update(GAME_MAP)
        if status == EVENT_ATE_PELLET:
            total_pellets -= 1
            player.score += PELLELETS_POINT
        elif status == EVENT_ATE_POWER_PELLET:
            player.score += POWER_PELLET_POINT
            frightened_mode = True
            frightened_start_time = pygame.time.get_ticks()
            log_message("Power Pellet!")
            for ghost in ghosts: ghost.start_frightened()

        # Win Condition
        if total_pellets <= 0:
            log_message("Level Cleared!")
            current_level += 1
            if player_lives < MAX_LIVES:
                player_lives += 1
                log_message("+1 Life!")
            
            if current_level > MAX_LEVELS:
                game_state = GAME_STATE_WIN
            else:
                game_state = GAME_STATE_START
                frightened_mode = False
                global_ghost_mode = MODE_SCATTER
                init_level(new_level=True)

        # Collision
        for ghost in ghosts:
            d = math.hypot(player.pixel_x - ghost.pixel_x, player.pixel_y - ghost.pixel_y)
            if d < player.radius + ghost.radius:
                if ghost.is_frightened:
                    ghost.eat()
                    player.score += GHOST_POINT
                elif not ghost.is_eaten:
                    player_lives -= 1
                    log_message(f"Hit! Lives: {player_lives}")
                    if player_lives > 0:
                        game_state = GAME_STATE_START
                        frightened_mode = False
                        global_ghost_mode = MODE_SCATTER
                        init_level(new_level=False)
                    else:
                        game_state = GAME_STATE_GAME_OVER
                        log_message("Game Over")

    # Drawing
    screen.fill(BLACK)
    if game_state == GAME_STATE_MENU:
        t = WIN_FONT.render("PAC-MAN AI SELECT", True, YELLOW)
        screen.blit(t, t.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3)))
        screen.blit(SCORE_FONT.render("1: BFS (Breadth-First)", True, WHITE), (50, SCREEN_HEIGHT//2))
        screen.blit(SCORE_FONT.render("2: DFS (Depth-First)", True, WHITE), (50, SCREEN_HEIGHT//2 + 40))
        screen.blit(SCORE_FONT.render("3: A* (Best Path)", True, WHITE), (50, SCREEN_HEIGHT//2 + 80))
    else:
        draw_map()
        if player: player.draw(screen)
        for g in ghosts: g.draw(screen)
        draw_logs(screen)
        if player:
            screen.blit(SCORE_FONT.render(f"SCORE: {int(player.score)}", True, WHITE), (10, MAP_HEIGHT - 25))
        
        c = (SCREEN_WIDTH // 2, MAP_HEIGHT // 2)
        if game_state == GAME_STATE_START:
            t = WIN_FONT.render(f"LEVEL {current_level}", True, YELLOW)
            screen.blit(t, t.get_rect(center=c))
            t2 = SCORE_FONT.render("Press ARROWS", True, WHITE)
            screen.blit(t2, t2.get_rect(center=(c[0], c[1]+40)))
        elif game_state == GAME_STATE_GAME_OVER:
            t = GAME_OVER_FONT.render("GAME OVER", True, RED)
            screen.blit(t, t.get_rect(center=c))
            t2 = SCORE_FONT.render("Press R to Menu", True, WHITE)
            screen.blit(t2, t2.get_rect(center=(c[0], c[1]+50)))
        elif game_state == GAME_STATE_WIN:
            t = WIN_FONT.render("YOU WIN!", True, YELLOW)
            screen.blit(t, t.get_rect(center=c))

    pygame.display.flip()

pygame.quit()