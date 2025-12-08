# settings.py
import pygame
import random

# --- 視窗與顯示設定 ---
TILE_SIZE = 20
MAP_HEIGHT = 30 * TILE_SIZE  # 稍微縮小一點以適應隨機生成的比例
LOG_HEIGHT = 140
SCREEN_WIDTH = 28 * TILE_SIZE
SCREEN_HEIGHT = MAP_HEIGHT + LOG_HEIGHT

# --- 顏色定義 ---
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
PINK = (255, 184, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 184, 82)
GREY = (150, 150, 150)
FRIGHTENED_BLUE = (0, 0, 139)

# --- 字型 ---
pygame.font.init()
SCORE_FONT = pygame.font.Font(None, 24)
GAME_OVER_FONT = pygame.font.Font(None, 64)
WIN_FONT = pygame.font.Font(None, 64)
LOG_FONT = pygame.font.Font(None, 20)

# --- 遊戲機制常數 ---
SPEED = 2
FRIGHTENED_DURATION = 7000
SCATTER_DURATION = 7000
CHASE_DURATION = 20000

MAX_LIVES = 3         # 最大生命值
MAX_LEVELS = 255      # 最大關卡數

# 分數
PELLELETS_POINT = 10
POWER_PELLET_POINT = 50
GHOST_POINT = 200

# --- 狀態常數 ---
GAME_STATE_MENU = "MENU"
GAME_STATE_START = "START"
GAME_STATE_PLAYING = "PLAYING"
GAME_STATE_GAME_OVER = "GAME_OVER"
GAME_STATE_WIN = "WIN"

# --- 演算法選擇 ---
ALGO_BFS = "BFS"
ALGO_DFS = "DFS"
ALGO_ASTAR = "A_STAR"

# --- AI 模式 ---
MODE_SCATTER = "SCATTER"
MODE_CHASE = "CHASE"
MODE_FRIGHTENED = "FRIGHTENED"
MODE_GO_HOME = "GO_HOME"
MODE_EXIT_HOUSE = "EXIT_HOUSE"
MODE_WAITING = "WAITING"

AI_CHASE_BLINKY = "CHASE_BLINKY"
AI_CHASE_PINKY = "CHASE_PINKY"
AI_CHASE_INKY = "CHASE_INKY"
AI_CHASE_CLYDE = "CHASE_CLYDE"

# --- 地圖物件 ---
TILE_WALL = "W"
TILE_DOOR = "="
TILE_PELLET = "."
TILE_POWER_PELLET = "O"
TILE_EMPTY = " "
EVENT_ATE_PELLET = "ATE_PELLET"
EVENT_ATE_POWER_PELLET = "ATE_POWER_PELLET"

# 預設地圖容器 (全域變數)
GAME_MAP = []

def generate_random_map():
    """
    生成隨機地圖：
    1. 使用遞迴回溯法生成迷宮 (保證連通)。
    2. 消除所有死路 (確保每格至少有2個出口)。
    3. 覆蓋鬼屋結構。
    4. 鏡像處理 (選擇性，這裡為了隨機性我們做非對稱或部分對稱，以下示範非對稱全隨機)。
    """
    rows = 30
    cols = 28
    
    # 1. 初始化全牆壁
    new_map = [[TILE_WALL for _ in range(cols)] for _ in range(rows)]
    
    # 2. 挖路 (Maze Generation)
    # 從 (1,1) 開始
    stack = [(1, 1)]
    new_map[1][1] = TILE_PELLET
    
    while stack:
        cx, cy = stack[-1]
        neighbors = []
        # 檢查四周跨兩格的鄰居
        for dx, dy in [(0, -2), (0, 2), (-2, 0), (2, 0)]:
            nx, ny = cx + dx, cy + dy
            if 1 <= nx < cols-1 and 1 <= ny < rows-1:
                if new_map[ny][nx] == TILE_WALL:
                    neighbors.append((nx, ny, dx//2, dy//2))
        
        if neighbors:
            nx, ny, wx, wy = random.choice(neighbors)
            new_map[cy + wy][cx + wx] = TILE_PELLET # 打通牆
            new_map[ny][nx] = TILE_PELLET           # 設為路
            stack.append((nx, ny))
        else:
            stack.pop()

    # 3. ★★★ 消除死路 (Dead End Removal) ★★★
    # 這一步確保不會有被鬼堵住必死的情況
    has_dead_end = True
    while has_dead_end:
        has_dead_end = False
        for y in range(1, rows - 1):
            for x in range(1, cols - 1):
                if new_map[y][x] != TILE_WALL:
                    # 計算周圍的「路」有幾條
                    road_neighbors = 0
                    wall_neighbors = []
                    for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        if new_map[y+dy][x+dx] != TILE_WALL:
                            road_neighbors += 1
                        elif 1 <= x+dx < cols-1 and 1 <= y+dy < rows-1:
                            wall_neighbors.append((x+dx, y+dy))
                    
                    # 如果只有 1 條路相連，代表這是死路
                    if road_neighbors <= 1 and wall_neighbors:
                        # 隨機打通一道牆，把它變成環狀道路的一部分
                        wx, wy = random.choice(wall_neighbors)
                        new_map[wy][wx] = TILE_PELLET
                        has_dead_end = True # 地圖變動了，需重新檢查

    # 4. 強制覆蓋鬼屋 (固定在中間)
    # 鬼屋範圍約 y:12~16, x:10~17
    ghost_house = [
        "WWWWWWWW",
        "W      W",
        "W WWWW W",
        "W W  W W",
        "W WWWW W",
        "WWWWWWWW"
    ]
    start_gx, start_gy = 10, 12
    for r, row_str in enumerate(ghost_house):
        for c, char in enumerate(row_str):
            if char == 'W': new_map[start_gy+r][start_gx+c] = TILE_WALL
            else: new_map[start_gy+r][start_gx+c] = TILE_EMPTY
    
    # 設置門
    new_map[14][13] = TILE_DOOR
    new_map[14][14] = TILE_DOOR

    # 5. 隨機放置大力丸 (4顆)
    pellets = []
    for y in range(rows):
        for x in range(cols):
            if new_map[y][x] == TILE_PELLET:
                pellets.append((x, y))
    
    if len(pellets) >= 4:
        # 簡單隨機選4個變成大力丸
        for _ in range(4):
            px, py = random.choice(pellets)
            new_map[py][px] = TILE_POWER_PELLET

    return new_map

def is_wall(game_map, x, y):
    if 0 <= y < len(game_map) and 0 <= x < len(game_map[0]):
        return game_map[y][x] == TILE_WALL
    return False