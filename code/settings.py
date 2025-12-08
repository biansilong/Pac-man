# settings.py
import pygame

# * 遊戲架構有關常數
# 遊戲視窗
TILE_SIZE = 20
MAP_HEIGHT = 36 * TILE_SIZE
LOG_HEIGHT = 140
SCREEN_WIDTH = 28 * TILE_SIZE
SCREEN_HEIGHT = MAP_HEIGHT + LOG_HEIGHT

# 顏色定義
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

# 字型設定
pygame.font.init()
SCORE_FONT = pygame.font.Font(None, 24)
GAME_OVER_FONT = pygame.font.Font(None, 64)
WIN_FONT = pygame.font.Font(None, 64)
LOG_FONT = pygame.font.Font(None, 20)

# * 運作常數

# 時間與速度常數
SPEED = 2
FRIGHTENED_DURATION = 7000
SCATTER_DURATION = 7000
CHASE_DURATION = 20000

# --- 新增：生命值常數 ---
MAX_LIVES = 3

# 分數資料
PELLELETS_POINT = 10
POWER_PELLET_POINT = 50
GHOST_POINT = 200

# --- 修改：新增 MENU 狀態 ---
GAME_STATE_MENU = "MENU"      # 選單
GAME_STATE_START = "START"    # 關卡開始前的 Ready
GAME_STATE_PLAYING = "PLAYING"
GAME_STATE_GAME_OVER = "GAME_OVER"
GAME_STATE_WIN = "WIN"        # 全破 (這裡我們當作過關)

# --- 新增：演算法選擇 ---
ALGO_BFS = "BFS"
ALGO_DFS = "DFS"
ALGO_ASTAR = "A_STAR"

# 鬼魂全域/行為模式
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

# 地圖物件符號
TILE_WALL = "W"
TILE_DOOR = "="
TILE_PELLET = "."
TILE_POWER_PELLET = "O"
TILE_EMPTY = " "

EVENT_ATE_PELLET = "ATE_PELLET"
EVENT_ATE_POWER_PELLET = "ATE_POWER_PELLET"

# 地圖資料
MAP_STRINGS = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "W............WW............W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "WOWWWW.WWWWW.WW.WWWWW.WWWWOW",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "W..........................W",
    "W.WWWW.WW.WWWWWWWW.WWWW.WW.W",
    "W.WWWW.WW.WWWWWWWW.WWWW.WW.W",
    "W......WW....WW....WW......W",
    "WWWWWW.WWWWW WW WWWWW.WWWWWW",
    "     W.WWWWW WW WWWWW.W     ",
    "     W.WW          WW.W     ",
    "     W.WW WWW==WWW WW.W     ",
    "WWWWWW.WW W      W WW.WWWWWW",
    "      .   W      W   .      ",
    "WWWWWW.WW W      W WW.WWWWWW",
    "     W.WW WWWWWWWW WW.W     ",
    "     W.WW          WW.W     ",
    "     W.WW WWWWWWWW WW.W     ",
    "WWWWWW.WW WWWWWWWW WW.WWWWWW",
    "W............WW............W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "WO..WW.......  .......WW..OW",
    "WWW.WW.WW.WWWWWWWW.WW.WW.WWW",
    "WWW.WW.WW.WWWWWWWW.WW.WW.WWW",
    "W......WW....WW....WW......W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "W..........................W",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    " ", " ", " ", " ", " "
]

GAME_MAP = [list(row) for row in MAP_STRINGS]

def is_wall(game_map, x, y):
    if 0 <= y < len(game_map) and 0 <= x < len(game_map[0]):
        return game_map[y][x] == TILE_WALL
    return False