# ghost.py
import pygame
import random
import math
from settings import *
from queue import PriorityQueue, Queue

class Ghost:
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
        self.delay = delay
        self.chosen_algorithm = chosen_algorithm  # 保存演算法選擇

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
             pygame.draw.circle(surface, WHITE, (int(self.pixel_x - eye_offset), int(self.pixel_y)), eye_radius)
             pygame.draw.circle(surface, WHITE, (int(self.pixel_x + eye_offset), int(self.pixel_y)), eye_radius)
        else:
            draw_color = self.color
            if self.is_frightened:
                draw_color = FRIGHTENED_BLUE
            pygame.draw.circle(surface, draw_color, (int(self.pixel_x), int(self.pixel_y)), self.radius)

    def eat(self):
        self.is_frightened = False
        self.is_eaten = True
        self.current_ai_mode = MODE_GO_HOME
        self.speed = 2*SPEED
        self.target = self.home_pos
        # 校正位置
        center_offset = TILE_SIZE // 2
        remainder_x = (self.pixel_x - center_offset) % self.speed
        if remainder_x != 0: self.pixel_x -= remainder_x
        remainder_y = (self.pixel_y - center_offset) % self.speed
        if remainder_y != 0: self.pixel_y -= remainder_y

    def respawn(self):
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

    # --- Pathfinding Algorithms ---

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

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

    def DFS(self, start, goal, game_map):
        stack = [start]
        came_from = {}
        visited = {start}

        while stack:
            current = stack.pop()
            if current == goal:
                return self.reconstruct_path(came_from, current)
            
            neighbors = self.get_neighbors(current, game_map)
            random.shuffle(neighbors) # 增加隨機性
            
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

    def update(self, game_map, player, all_ghosts, dt, global_ghost_mode, blinky_tile=None):
        valid_to_switch = (self.current_ai_mode not in [MODE_GO_HOME, MODE_EXIT_HOUSE, MODE_WAITING]
                           and not self.is_frightened and not self.is_eaten)

        if valid_to_switch:
            if global_ghost_mode == MODE_SCATTER and self.current_ai_mode != MODE_SCATTER:
                self.current_ai_mode = MODE_SCATTER
                self.direction = (self.direction[0] * -1, self.direction[1] * -1)

        if self.current_ai_mode == MODE_WAITING:
            if self.is_frightened:
                 # Bounce logic
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

            # --- 尋路邏輯 ---
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
                    target_pos = self.scatter_path[self.scatter_index]
                elif self.current_ai_mode == AI_CHASE_BLINKY:
                    target_pos = (player.grid_x, player.grid_y)
                elif self.current_ai_mode == AI_CHASE_PINKY:
                    pdx, pdy = player.direction
                    if pdx==0 and pdy==0: target_pos = (player.grid_x, player.grid_y)
                    else: target_pos = (player.grid_x + pdx*4, player.grid_y + pdy*4)
                elif self.current_ai_mode == AI_CHASE_CLYDE:
                    d = self.get_distance((self.grid_x, self.grid_y), (player.grid_x, player.grid_y))
                    if d > 8: target_pos = (player.grid_x, player.grid_y)
                    else: target_pos = self.scatter_path[0]
                elif self.current_ai_mode == AI_CHASE_INKY:
                    pdx, pdy = player.direction
                    if blinky_tile is None or (pdx==0 and pdy==0): target_pos = (player.grid_x, player.grid_y)
                    else:
                        tx, ty = player.grid_x + pdx*2, player.grid_y + pdy*2
                        bx, by = blinky_tile
                        target_pos = (tx + (tx-bx), ty + (ty-by))

                self.target = target_pos
                found_path = False
                
                # 根據選單選擇的演算法尋路
                if self.current_ai_mode != MODE_FRIGHTENED and target_pos:
                    path = None
                    if self.chosen_algorithm == ALGO_ASTAR:
                        path = self.A_star((self.grid_x, self.grid_y), target_pos, game_map)
                    elif self.chosen_algorithm == ALGO_BFS:
                        path = self.BFS((self.grid_x, self.grid_y), target_pos, game_map)
                    elif self.chosen_algorithm == ALGO_DFS:
                        path = self.DFS((self.grid_x, self.grid_y), target_pos, game_map)
                    
                    if path and len(path) > 1:
                        dx, dy = path[1][0]-self.grid_x, path[1][1]-self.grid_y
                        self.direction = (dx, dy)
                        found_path = True
                
                # 失敗或驚嚇模式時的 Fallback
                if not found_path:
                    valid = self.get_valid_directions(game_map, all_ghosts)
                    if valid:
                        best_dir = (0,0)
                        best_dist = float('-inf') if self.current_ai_mode == MODE_FRIGHTENED else float('inf')
                        
                        for d in valid:
                            nx, ny = self.grid_x + d[0], self.grid_y + d[1]
                            calc_t = target_pos if target_pos else (player.grid_x, player.grid_y)
                            dist = self.get_distance((nx, ny), calc_t)
                            
                            if self.current_ai_mode == MODE_FRIGHTENED:
                                if dist > best_dist:
                                    best_dist = dist
                                    best_dir = d
                            else:
                                if dist < best_dist:
                                    best_dist = dist
                                    best_dir = d
                        self.direction = best_dir

        # 移動
        self.pixel_x += self.direction[0] * self.speed
        self.pixel_y += self.direction[1] * self.speed
        
        # 隧道
        if self.pixel_x < -TILE_SIZE//2: self.pixel_x = SCREEN_WIDTH + TILE_SIZE//2
        elif self.pixel_x > SCREEN_WIDTH + TILE_SIZE//2: self.pixel_x = -TILE_SIZE//2