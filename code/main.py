# main.py
import pygame
import math
from settings import * 
from player import Player
from ghost import Ghost

# 遊戲初始化
pygame.init()
pygame.font.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pygame Pac-Man: Advanced")
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
    
    # 顯示生命值與關卡
    info_text = f"LIVES: {player_lives} / {MAX_LIVES}   LEVEL: {current_level}   ALGO: {selected_algorithm}"
    info_surf = LOG_FONT.render(info_text, True, YELLOW)
    surface.blit(info_surf, (10, start_y))
    
    # 顯示日誌
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

# --- 全局遊戲狀態變數 ---
player_lives = MAX_LIVES
current_level = 1
selected_algorithm = ALGO_ASTAR # 預設

# 初始化物件變數
player = None
ghosts = []
total_pellets = 0
running = True
game_state = GAME_STATE_MENU # ★★★ 初始狀態改為 MENU ★★★
frightened_mode = False
frightened_start_time = 0
global_ghost_mode = MODE_SCATTER
last_mode_switch_time = 0

path_blinky = [(26, 1)]
path_pinky = [(1, 1)]
path_inky = [(26, 29)]
path_clyde = [(1, 29)]

def init_level(new_level=False):
    """ 初始化關卡：重置地圖、豆子、玩家和鬼的位置 """
    global player, ghosts, total_pellets, GAME_MAP
    
    if new_level:
        # 如果是新關卡，重置地圖 (把豆子補回來)
        GAME_MAP[:] = [list(row) for row in MAP_STRINGS]
        log_message(f"--- Level {current_level} Started ---")
    else:
        # 如果是死亡重置 (Soft Reset)，地圖不變，只重置實體位置
        # 但豆子不能重置
        pass

    # 重置玩家 (分數保留)
    old_score = 0
    if player: old_score = player.score
    player = Player(13.5, 23)
    player.score = old_score

    # 重置鬼魂 (傳入 selected_algorithm)
    blinky = Ghost(13, 14, RED, ai_mode=AI_CHASE_BLINKY, chosen_algorithm=selected_algorithm,
                   scatter_point=path_blinky, in_house=True, delay=0, on_log=log_message)
    pinky = Ghost(14, 14, PINK, ai_mode=AI_CHASE_PINKY, chosen_algorithm=selected_algorithm,
                  scatter_point=path_pinky, in_house=True, delay=3000, on_log=log_message)
    inky = Ghost(12, 14, CYAN, ai_mode=AI_CHASE_INKY, chosen_algorithm=selected_algorithm, scatter_point=path_inky,
                 in_house=True, delay=6000, on_log=log_message)
    clyde = Ghost(15, 14, ORANGE, ai_mode=AI_CHASE_CLYDE, chosen_algorithm=selected_algorithm,
                  scatter_point=path_clyde, in_house=True, delay=9000, on_log=log_message)
    
    ghosts[:] = [blinky, pinky, inky, clyde]

    # 只有在新關卡時才重算豆子
    if new_level:
        total_pellets = sum(row.count(TILE_PELLET) for row in GAME_MAP)
        log_message(f"Total pellets: {total_pellets}")

def reset_game_totally():
    """ 完全重置遊戲 (Game Over 後) """
    global player_lives, current_level, game_state
    player_lives = MAX_LIVES
    current_level = 1
    game_state = GAME_STATE_MENU # 回到選單
    log_message("Game Reset to Menu")

# * 主迴圈
while running:
    dt = clock.tick(60)
    
    # --- 事件處理 ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        # 1. 選單模式：選擇演算法
        if game_state == GAME_STATE_MENU:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    selected_algorithm = ALGO_BFS
                    game_state = GAME_STATE_START
                    init_level(new_level=True) # 初始化第一關
                elif event.key == pygame.K_2:
                    selected_algorithm = ALGO_DFS
                    game_state = GAME_STATE_START
                    init_level(new_level=True)
                elif event.key == pygame.K_3:
                    selected_algorithm = ALGO_ASTAR
                    game_state = GAME_STATE_START
                    init_level(new_level=True)
                    
        # 2. 準備開始模式
        elif game_state == GAME_STATE_START:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                    game_state = GAME_STATE_PLAYING
                    last_mode_switch_time = pygame.time.get_ticks()
                    log_message(f"Level {current_level} Start! Algo: {selected_algorithm}")
                    player.handle_input(event)

        # 3. 遊戲進行中
        elif game_state == GAME_STATE_PLAYING:
            player.handle_input(event)

        # 4. 結束畫面
        elif game_state in [GAME_STATE_GAME_OVER, GAME_STATE_WIN]:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game_totally()

    # --- 邏輯更新 ---
    if game_state == GAME_STATE_PLAYING:
        current_time = pygame.time.get_ticks()

        # Ghost Mode Switch logic
        if not frightened_mode:
            time_passed = current_time - last_mode_switch_time
            if global_ghost_mode == MODE_SCATTER and time_passed > SCATTER_DURATION:
                global_ghost_mode = MODE_CHASE
                last_mode_switch_time = current_time
                log_message(">> Mode Switch: CHASE")
            elif global_ghost_mode == MODE_CHASE and time_passed > CHASE_DURATION:
                global_ghost_mode = MODE_SCATTER
                last_mode_switch_time = current_time
                log_message(">> Mode Switch: SCATTER")

        # Ghost Updates
        blinky_pos_for_inky = (ghosts[0].grid_x, ghosts[0].grid_y) # Assume index 0 is blinky
        for ghost in ghosts:
             if (not ghost.is_frightened and not ghost.is_eaten and ghost.current_ai_mode not in [MODE_GO_HOME, MODE_EXIT_HOUSE, MODE_WAITING]):
                if global_ghost_mode == MODE_SCATTER: ghost.current_ai_mode = MODE_SCATTER
                elif global_ghost_mode == MODE_CHASE: ghost.current_ai_mode = ghost.ai_mode
             ghost.update(GAME_MAP, player, ghosts, dt, global_ghost_mode, blinky_pos_for_inky)

        # Frightened Timer
        if frightened_mode:
            if current_time - frightened_start_time > FRIGHTENED_DURATION:
                frightened_mode = False
                log_message("Frightened mode ended.")
                for ghost in ghosts: ghost.end_frightened()
                last_mode_switch_time = current_time

        # Player Update
        player_status = player.update(GAME_MAP)
        if player_status == EVENT_ATE_PELLET:
            total_pellets -= 1
            player.score += PELLELETS_POINT
        elif player_status == EVENT_ATE_POWER_PELLET:
            player.score += POWER_PELLET_POINT
            frightened_mode = True
            frightened_start_time = pygame.time.get_ticks()
            log_message("Ghosts Frightened!")
            for ghost in ghosts: ghost.start_frightened()

        # --- ★★★ 進階下一關邏輯 ★★★ ---
        if total_pellets <= 0:
            log_message("Level Cleared!")
            current_level += 1
            # 加命 (最多3)
            if player_lives < MAX_LIVES:
                player_lives += 1
                log_message("Extra Life Gained!")
            
            # 重新開始下一關 (保留分數，重置地圖)
            game_state = GAME_STATE_START
            frightened_mode = False
            global_ghost_mode = MODE_SCATTER
            init_level(new_level=True)

        # 碰撞偵測 (處理扣命)
        for ghost in ghosts:
            dx = player.pixel_x - ghost.pixel_x
            dy = player.pixel_y - ghost.pixel_y
            distance = math.hypot(dx, dy)
            collision_distance = player.radius + ghost.radius

            if distance < collision_distance:
                if ghost.is_frightened:
                    ghost.eat()
                    player.score += GHOST_POINT
                elif not ghost.is_eaten:
                    # ★★★ 被鬼抓到 -> 扣命 ★★★
                    player_lives -= 1
                    log_message(f"Hit! Lives left: {player_lives}")
                    
                    if player_lives > 0:
                        # 還有命：軟重置 (保留地圖與豆子)
                        game_state = GAME_STATE_START
                        frightened_mode = False
                        global_ghost_mode = MODE_SCATTER
                        init_level(new_level=False) 
                    else:
                        # 沒命了：Game Over
                        game_state = GAME_STATE_GAME_OVER
                        log_message("No lives left. Game Over.")

    # --- 畫面繪製 ---
    screen.fill(BLACK)
    
    if game_state == GAME_STATE_MENU:
        # 繪製選單
        title = WIN_FONT.render("PAC-MAN AI SELECT", True, YELLOW)
        t_rect = title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//3))
        screen.blit(title, t_rect)
        
        opt1 = SCORE_FONT.render("Press 1 for BFS (Wide Search)", True, WHITE)
        opt2 = SCORE_FONT.render("Press 2 for DFS (Deep/Random)", True, WHITE)
        opt3 = SCORE_FONT.render("Press 3 for A* (Smartest)", True, WHITE)
        
        screen.blit(opt1, (50, SCREEN_HEIGHT//2))
        screen.blit(opt2, (50, SCREEN_HEIGHT//2 + 40))
        screen.blit(opt3, (50, SCREEN_HEIGHT//2 + 80))
        
    else:
        # 繪製遊戲畫面
        draw_map()
        if player: player.draw(screen)
        for ghost in ghosts: ghost.draw(screen)
        draw_logs(screen)
        
        # UI
        if player:
            score_text = SCORE_FONT.render(f"SCORE: {int(player.score)}", True, WHITE)
            screen.blit(score_text, (10, MAP_HEIGHT - 25))

        center_pos = (SCREEN_WIDTH // 2, MAP_HEIGHT // 2)
        if game_state == GAME_STATE_START:
            ready_text = WIN_FONT.render(f"LEVEL {current_level}", True, YELLOW)
            hint_text = SCORE_FONT.render("Press ARROWS", True, WHITE)
            r1 = ready_text.get_rect(center=center_pos)
            r2 = hint_text.get_rect(center=(center_pos[0], center_pos[1] + 40))
            screen.blit(ready_text, r1)
            screen.blit(hint_text, r2)
            
        elif game_state == GAME_STATE_GAME_OVER:
            text = GAME_OVER_FONT.render("GAME OVER", True, RED)
            rect = text.get_rect(center=center_pos)
            screen.blit(text, rect)
            rst = SCORE_FONT.render("Press R to Menu", True, WHITE)
            r_rect = rst.get_rect(center=(center_pos[0], center_pos[1] + 50))
            screen.blit(rst, r_rect)

    pygame.display.flip()

pygame.quit()