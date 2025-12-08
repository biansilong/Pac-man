# ghost.py
import pygame
import random
import math
from settings import *
from queue import PriorityQueue, Queue # <--- 新增 Queue

class Ghost:
    # 1. 修改 __init__ 接收 chosen_algorithm
    def __init__(self, grid_x, grid_y, color, ai_mode, chosen_algorithm, scatter_point=None, in_house=False, delay=0, on_log=None):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.home_pos = (grid_x, grid_y)

        self.pixel_x = (self.grid_x * TILE_SIZE) + (TILE_SIZE // 2)
        self.pixel_y = (self.grid_y * TILE_SIZE) + (TILE_SIZE // 2)
        self.radius = TILE_SIZE // 2 - 2

        self.color = color
        self.default_speed = SPEED
        self.speed = self.default_speed
        self.direction = (1, 0)
        self.all_directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

        self.ai_mode = ai_mode
        self.chosen_algorithm = chosen_algorithm # <--- 儲存演算法

        self.delay = delay

        if in_house:
            if self.delay > 0:
                self.current_ai_mode = MODE_WAITING
                self.direction = (0, -0.5)
            else:
                self.current_ai_mode = MODE_EXIT_HOUSE
                self.direction = (0, -1)
        else:
            self.current_ai_mode = ai_mode

        if scatter_point is None:
            self.scatter_path = [(grid_x, grid_y)]
        else:
            self.scatter_path = scatter_point

        self.scatter_index = 0
        self.target = (0, 0)

        self.is_frightened = False
        self.is_eaten = False

        self.on_log = on_log

    def draw(self, surface):
        if self.is_eaten:
            eye_radius = self.radius // 2
            eye_offset = self.radius // 3
            pygame.draw.circle(surface, WHITE, (self.pixel_x - eye_offset, self.pixel_y), eye_radius)
            pygame.draw.circle(surface, WHITE, (self.pixel_x + eye_offset, self.pixel_y), eye_radius)
        else:
            draw_color = self.color
            if self.is_frightened:
                draw_color = FRIGHTENED_BLUE
            pygame.draw.circle(surface, draw_color, (self.pixel_x, self.pixel_y), self.radius)

    def eat(self):
        if self.on_log:
            self.on_log(f"[{self.ai_mode}] Ghost eaten!")
        self.is_frightened = False
        self.is_eaten = True
        self.current_ai_mode = MODE_GO_HOME
        self.speed = 2*SPEED
        self.target = self.home_pos
        center_offset = TILE_SIZE // 2
        remainder_x = (self.pixel_x - center_offset) % self.speed
        if remainder_x != 0: self.pixel_x -= remainder_x
        remainder_y = (self.pixel_y - center_offset) % self.speed
        if remainder_y != 0: self.pixel_y -= remainder_y

    def respawn(self):
        if self.on_log:
            self.on_log(f"[{self.ai_mode}] Respawned!")
        self.is_eaten = False
        self.current_ai_mode = MODE_EXIT_HOUSE
        self.speed = self.default_speed
        self.pixel_x = (self.home_pos[0] * TILE_SIZE) + (TILE_SIZE // 2)
        self.pixel_y = (self.home_pos[1] * TILE_SIZE) + (TILE_SIZE // 2)
        self.direction = (0, -1)

    def start_frightened(self):
        if self.is_eaten: return
        self.is_frightened = True
        if self.current_ai_mode not in [MODE_GO_HOME, MODE_EXIT_HOUSE, MODE_WAITING]:
            self.current_ai_mode = MODE_FRIGHTENED
            self.speed = 1
            self.direction = (self.direction[0] * -1, self.direction[1] * -1)

    def end_frightened(self):
        if self.is_frightened:
            self.is_frightened = False
            if self.current_ai_mode not in [MODE_GO_HOME, MODE_EXIT_HOUSE, MODE_WAITING]:
                self.current_ai_mode = self.ai_mode

    # --- 演算法區域 ---

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    # 1. A* (保持不變)
    def A_star(self, start, goal, game_map):
        open_set = PriorityQueue()
        open_set.put((0, start))
        came_from = {}
        g_score = {start: 0}

        while not open_set.empty():
            _, current = open_set.get()
            if current == goal:
                return self.reconstruct_path(came_from, current)

            for nx, ny in self.get_neighbors(current, game_map):
                tentative = g_score[current] + 1
                if (nx, ny) not in g_score or tentative < g_score[(nx, ny)]:
                    g_score[(nx, ny)] = tentative
                    priority = tentative + self.heuristic((nx, ny), goal)
                    open_set.put((priority, (nx, ny)))
                    came_from[(nx, ny)] = current
        return None

    # 2. BFS (廣度優先 - 新增) 


    def BFS(self, start, goal, game_map):
        queue = Queue()
        queue.put(start)
        came_from = {}
        visited = {start} 

        while not queue.empty():
            current = queue.get()
            if current == goal:
                return self.reconstruct_path(came_from, current)
            
            for nx, ny in self.get_neighbors(current, game_map):
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    came_from[(nx, ny)] = current
                    queue.put((nx, ny))
        return None

    # 3. DFS (深度優先 - 新增) 
    def DFS(self, start, goal, game_map):
        stack = [start]
        came_from = {}
        visited = {start}

        while stack:
            current = stack.pop()
            if current == goal:
                return self.reconstruct_path(came_from, current)
            
            # 隨機打亂鄰居順序，讓 DFS 比較不僵硬
            neighbors = self.get_neighbors(current, game_map)
            random.shuffle(neighbors)
            
            for nx, ny in neighbors:
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    came_from[(nx, ny)] = current
                    stack.append((nx, ny))
        return None

    def get_neighbors(self, node, game_map):
        x, y = node
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        neighbors = []
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= ny < len(game_map) and 0 <= nx < len(game_map[0]):
                if not is_wall(game_map, nx, ny):
                    neighbors.append((nx, ny))
        return neighbors

    def reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

    def get_distance(self, pos1, pos2):
        return math.hypot(pos1[0] - pos2[0], pos1[1] - pos2[1])

    def get_valid_directions(self, game_map, others):
        valid_moves = []
        reverse_dir = (self.direction[0] * -1, self.direction[1] * -1)
        for move_dir in self.all_directions:
            no_rev = (self.current_ai_mode != MODE_WAITING)
            if no_rev and move_dir == reverse_dir: continue
            next_g_x = int(self.grid_x + move_dir[0])
            next_g_y = int(self.grid_y + move_dir[1])
            if 0 <= next_g_y < len(game_map):
                if is_wall(game_map, next_g_x, next_g_y): continue
                check_x = next_g_x % len(game_map[0])
                tile = game_map[next_g_y][check_x]
                if tile == TILE_DOOR:
                    if self.current_ai_mode not in [MODE_EXIT_HOUSE, MODE_GO_HOME]: continue
                is_blocked_by_ghost = False
                if self.current_ai_mode not in [MODE_EXIT_HOUSE, MODE_GO_HOME, MODE_WAITING]:
                    for ghost in others:
                        if ghost is not self and ghost.current_ai_mode not in [MODE_EXIT_HOUSE, MODE_GO_HOME, MODE_WAITING]:
                            if ghost.grid_x == next_g_x and ghost.grid_y == next_g_y:
                                is_blocked_by_ghost = True
                                break
                if is_blocked_by_ghost: continue
                valid_moves.append(move_dir)
        if not valid_moves: valid_moves.append(reverse_dir)
        return valid_moves

    # --- Update 修改：根據 self.chosen_algorithm 決定跑哪個函式 ---
    def update(self, game_map, player, all_ghosts, dt, global_ghost_mode, blinky_tile=None):
        valid_to_switch = (self.current_ai_mode not in [MODE_GO_HOME, MODE_EXIT_HOUSE, MODE_WAITING]
                           and not self.is_frightened and not self.is_eaten)

        if valid_to_switch:
            if global_ghost_mode == MODE_SCATTER and self.current_ai_mode != MODE_SCATTER:
                self.current_ai_mode = MODE_SCATTER
                self.direction = (self.direction[0] * -1, self.direction[1] * -1)

        if self.current_ai_mode == MODE_WAITING:
            if self.is_frightened:
                 home_pixel_y = (self.home_pos[1] * TILE_SIZE) + (TILE_SIZE // 2)
                 limit = 5
                 self.pixel_y += self.direction[1]
                 if self.pixel_y > home_pixel_y + limit: self.direction = (0, -0.5)
                 elif self.pixel_y < home_pixel_y - limit: self.direction = (0, 0.5)
                 return
            self.delay -= dt
            if self.delay <= 0:
                self.current_ai_mode = MODE_EXIT_HOUSE
                self.direction = (0, -1)
                self.pixel_x = (self.home_pos[0] * TILE_SIZE) + (TILE_SIZE // 2)
                self.pixel_y = (self.home_pos[1] * TILE_SIZE) + (TILE_SIZE // 2)
                self.speed = self.default_speed
            else:
                 home_pixel_y = (self.home_pos[1] * TILE_SIZE) + (TILE_SIZE // 2)
                 limit = 5
                 self.pixel_y += self.direction[1]
                 if self.pixel_y > home_pixel_y + limit: self.direction = (0, -0.5)
                 elif self.pixel_y < home_pixel_y - limit: self.direction = (0, 0.5)
            return

        if abs(self.pixel_x - round(self.pixel_x)) < 0.1: self.pixel_x = round(self.pixel_x)
        if abs(self.pixel_y - round(self.pixel_y)) < 0.1: self.pixel_y = round(self.pixel_y)
        is_centered_x = (self.pixel_x - (TILE_SIZE // 2)) % TILE_SIZE == 0
        is_centered_y = (self.pixel_y - (TILE_SIZE // 2)) % TILE_SIZE == 0

        if is_centered_x and is_centered_y:
            self.grid_x = int((self.pixel_x - (TILE_SIZE // 2)) // TILE_SIZE)
            self.grid_y = int((self.pixel_y - (TILE_SIZE // 2)) // TILE_SIZE)

            if self.current_ai_mode == MODE_GO_HOME and (self.grid_x, self.grid_y) == self.home_pos:
                self.respawn()

            if self.current_ai_mode == MODE_EXIT_HOUSE:
                if self.grid_y <= 11:
                    self.current_ai_mode = self.ai_mode
                    self.direction = random.choice([(-1, 0), (1, 0)])

            if not self.is_frightened and self.current_ai_mode not in [MODE_GO_HOME, MODE_EXIT_HOUSE, MODE_WAITING]:
                self.speed = self.default_speed

            # AI Pathfinding Decision
            if self.current_ai_mode not in [MODE_GO_HOME, MODE_EXIT_HOUSE, MODE_WAITING]:
                target_pos = None
                
                # 計算目標點
                if self.current_ai_mode == MODE_FRIGHTENED:
                    target_pos = (player.grid_x, player.grid_y)
                elif self.current_ai_mode == MODE_SCATTER:
                    current_target_point = self.scatter_path[self.scatter_index]
                    if (self.grid_x, self.grid_y) == current_target_point:
                        self.scatter_index += 1
                        if self.scatter_index >= len(self.scatter_path):
                            self.scatter_index = 0
                            if global_ghost_mode == MODE_CHASE:
                                self.current_ai_mode = self.ai_mode
                                if self.on_log: self.on_log(f"{self.color} 繞行結束，開始追逐！")
                    target_pos = self.scatter_path[self.scatter_index]
                elif self.current_ai_mode == AI_CHASE_BLINKY:
                    target_pos = (player.grid_x, player.grid_y)
                elif self.current_ai_mode == AI_CHASE_PINKY:
                    player_dir_x, player_dir_y = player.direction
                    if player_dir_x == 0 and player_dir_y == 0: target_pos = (player.grid_x, player.grid_y)
                    else: target_pos = (player.grid_x + (player_dir_x * 4), player.grid_y + (player_dir_y * 4))
                elif self.current_ai_mode == AI_CHASE_CLYDE:
                    distance = self.get_distance((self.grid_x, self.grid_y), (player.grid_x, player.grid_y))
                    if distance > 8: target_pos = (player.grid_x, player.grid_y)
                    else: target_pos = self.scatter_path[0]
                elif self.current_ai_mode == AI_CHASE_INKY:
                    player_dir_x, player_dir_y = player.direction
                    if blinky_tile is None or (player_dir_x == 0 and player_dir_y == 0): target_pos = (player.grid_x, player.grid_y)
                    else:
                        trigger_x = player.grid_x + (player_dir_x * 2)
                        trigger_y = player.grid_y + (player_dir_y * 2)
                        blinky_x, blinky_y = blinky_tile
                        vec_x = trigger_x - blinky_x
                        vec_y = trigger_y - blinky_y
                        target_pos = (trigger_x + vec_x, trigger_y + vec_y)

                self.target = target_pos
                found_path = False
                
                # ★★★ 這裡修改：根據選的演算法來找路 ★★★
                if self.current_ai_mode != MODE_FRIGHTENED and target_pos:
                    path = None
                    if self.chosen_algorithm == ALGO_ASTAR:
                        path = self.A_star((self.grid_x, self.grid_y), target_pos, game_map)
                    elif self.chosen_algorithm == ALGO_BFS:
                        path = self.BFS((self.grid_x, self.grid_y), target_pos, game_map)
                    elif self.chosen_algorithm == ALGO_DFS:
                        path = self.DFS((self.grid_x, self.grid_y), target_pos, game_map)
                    
                    if path and len(path) > 1:
                        next_step = path[1]
                        dx = next_step[0] - self.grid_x
                        dy = next_step[1] - self.grid_y
                        self.direction = (dx, dy)
                        found_path = True
                
                # Fallback (貪婪/隨機)
                if not found_path:
                    valid_directions = self.get_valid_directions(game_map, all_ghosts)
                    if valid_directions:
                        best_direction = (0, 0)
                        if self.current_ai_mode == MODE_FRIGHTENED: best_distance = float('-inf')
                        else: best_distance = float('inf')
                        for direction in valid_directions:
                            next_g_x = self.grid_x + direction[0]
                            next_g_y = self.grid_y + direction[1]
                            calc_target = target_pos if target_pos else (player.grid_x, player.grid_y)
                            dist = self.get_distance((next_g_x, next_g_y), calc_target)
                            if self.current_ai_mode == MODE_FRIGHTENED:
                                if dist > best_distance:
                                    best_distance = dist
                                    best_direction = direction
                            else:
                                if dist < best_distance:
                                    best_distance = dist
                                    best_direction = direction
                        self.direction = best_direction

        self.pixel_x += self.direction[0] * self.speed
        self.pixel_y += self.direction[1] * self.speed

        if self.pixel_x < -TILE_SIZE//2: self.pixel_x = SCREEN_WIDTH + TILE_SIZE//2
        elif self.pixel_x > SCREEN_WIDTH + TILE_SIZE//2: self.pixel_x = -TILE_SIZE//2