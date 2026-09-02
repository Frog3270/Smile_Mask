import pygame
import sys
import math
import random
import os

os.environ['SDL_VIDEO_CENTERED'] = '1'

pygame.init()
pygame.mixer.init()

# ---------- Геймпад ----------
pygame.joystick.init()
joystick = None
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Gamepad found: {joystick.get_name()}")
else:
    print("No gamepad detected.")

# Разрешение 16:9
WIDTH, HEIGHT = 1280, 720
TILE = 48
is_fullscreen = False

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
pygame.display.set_caption("Smile Mask")

# ---------- Установка иконки ----------
try:
    icon_img = pygame.image.load("textures/icon.png").convert_alpha()
    pygame.display.set_icon(icon_img)
except Exception as e:
    print(f"Failed to load icon: {e}")

# ---------- Цвета ----------
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 100)

# ---------- Шрифты ----------
try:
    font = pygame.font.Font("fonts/PressStart2P-Regular.ttf", 18)
    font_title = pygame.font.Font("fonts/PressStart2P-Regular.ttf", 48)
    font_small = pygame.font.Font("fonts/PressStart2P-Regular.ttf", 14)
    font_death = pygame.font.Font("fonts/PressStart2P-Regular.ttf", 72)
    font_disclaimer = pygame.font.Font("fonts/PressStart2P-Regular.ttf", 24)
except:
    font = pygame.font.SysFont("arial", 18, bold=True)
    font_title = pygame.font.SysFont("arial", 48, bold=True)
    font_small = pygame.font.SysFont("arial", 14, bold=True)
    font_death = pygame.font.SysFont("arial", 72, bold=True)
    font_disclaimer = pygame.font.SysFont("arial", 24, bold=True)

# ---------- Загрузка текстур ----------
def load_img(path, scale=None):
    try:
        img = pygame.image.load(path).convert_alpha()
        if scale:
            img = pygame.transform.scale(img, scale)
        return img
    except Exception as e:
        surf = pygame.Surface(scale if scale else (TILE, TILE))
        surf.fill((255, 0, 255))
        return surf

menu_bg = load_img("textures/menu_bg.png", (WIDTH, HEIGHT))
player_img = load_img("textures/vel.png", (TILE, TILE))
coin_img = load_img("textures/money.png", (TILE, TILE))
grass_img = load_img("textures/dirn.png", (TILE, TILE))
wall_img = load_img("textures/stone.png", (TILE, TILE))
start_img = load_img("textures/start.png", (TILE, TILE))
finish_img = load_img("textures/finish.png", (TILE, TILE))
devil_img = load_img("textures/devil.png", (TILE, TILE))
btn_img = load_img("textures/cnok.png")
exit_btn_small = load_img("textures/cnok4.png", (60, 30))

# ---------- Загрузка звуков ----------
sounds = {}
try:
    sounds['step'] = pygame.mixer.Sound("sounds/walking.mp3")
    sounds['coin'] = pygame.mixer.Sound("sounds/coin.mp3")
    sounds['death'] = pygame.mixer.Sound("sounds/death.wav")

    sounds['step'].set_volume(0.7)
    sounds['coin'].set_volume(0.3)
    sounds['death'].set_volume(0.7)
except:
    pass

def play_sound(name, loops=0):
    if name in sounds:
        sounds[name].play(loops)

def stop_sound(name):
    if name in sounds:
        sounds[name].stop()

# ---------- Состояния ----------
STATE_DISCLAIMER = 0
STATE_MENU = 1
STATE_PLAY = 2
STATE_DEATH = 3

game_state = STATE_DISCLAIMER
current_level = 0

step_timer = 0
STEP_DELAY = 300

HITBOX_W = 16
HITBOX_H = 26
OFFSET_X = 16
OFFSET_Y = 10
player_speed = 3

# ---------- Генератор уровней (без изменений) ----------
def generate_static_level(seed_val, num_enemies, num_coins, level_index):
    random.seed(seed_val)
    COLS, ROWS = 26, 15
    grid = [[1 for _ in range(COLS)] for _ in range(ROWS)]

    start_c, start_r = 1, 1
    grid[start_r][start_c] = 0
    stack = [(start_c, start_r)]

    while stack:
        c, r = stack[-1]
        neighbors = []
        for dc, dr in [(0, -2), (0, 2), (-2, 0), (2, 0)]:
            nc, nr = c + dc, r + dr
            if 0 < nc < COLS - 2 and 0 < nr < ROWS - 1:
                if grid[nr][nc] == 1:
                    neighbors.append((nc, nr, dc, dr))

        if neighbors:
            nc, nr, dc, dr = random.choice(neighbors)
            grid[r + dr // 2][c + dc // 2] = 0
            grid[nr][nc] = 0
            stack.append((nc, nr))
        else:
            stack.pop()

    for r in range(1, ROWS - 1):
        if grid[r][23] == 0:
            if random.random() < 0.5:
                grid[r][24] = 0

    def creates_2x2_empty(test_r, test_c):
        if grid[test_r-1][test_c-1] == 0 and grid[test_r-1][test_c] == 0 and grid[test_r][test_c-1] == 0: return True
        if grid[test_r-1][test_c+1] == 0 and grid[test_r-1][test_c] == 0 and grid[test_r][test_c+1] == 0: return True
        if grid[test_r+1][test_c-1] == 0 and grid[test_r+1][test_c] == 0 and grid[test_r][test_c-1] == 0: return True
        if grid[test_r+1][test_c+1] == 0 and grid[test_r+1][test_c] == 0 and grid[test_r][test_c+1] == 0: return True
        return False

    loop_chance = 0.25 + (level_index * 0.01)
    for r in range(1, ROWS - 1):
        for c in range(1, COLS - 1):
            if grid[r][c] == 1:
                horiz = grid[r][c-1] == 0 and grid[r][c+1] == 0
                vert = grid[r-1][c] == 0 and grid[r+1][c] == 0
                if (horiz and not vert) or (vert and not horiz):
                    if random.random() < loop_chance:
                        if not creates_2x2_empty(r, c):
                            grid[r][c] = 0

    grid[1][1] = 3

    empty_cells = [(c, r) for r in range(1, ROWS-1) for c in range(1, COLS-1) if grid[r][c] == 0]

    empty_cells.sort(key=lambda p: math.hypot(p[0]-1, p[1]-1), reverse=True)
    finish_c, finish_r = empty_cells[0]
    grid[finish_r][finish_c] = 4
    empty_cells.pop(0)

    valid_enemies = [p for p in empty_cells if math.hypot(p[0]-1, p[1]-1) >= 6]
    random.shuffle(valid_enemies)
    for _ in range(num_enemies):
        if valid_enemies:
            ec, er = valid_enemies.pop(0)
            if (ec, er) in empty_cells:
                empty_cells.remove((ec, er))
            grid[er][ec] = 5

    random.shuffle(empty_cells)
    for _ in range(num_coins):
        if empty_cells:
            cc, cr = empty_cells.pop(0)
            grid[cr][cc] = 2

    return grid

level_configs = [
    (1, 5), (1, 10), (1, 15),
    (2, 10), (2, 15), (2, 20),
    (3, 10), (3, 15), (3, 20),
    (4, 10), (4, 15), (4, 20),
    (5, 15), (5, 20), (5, 25)
]

levels = []
for i, (enemies_count, coins_count) in enumerate(level_configs):
    generated_map = generate_static_level(42 + i, enemies_count, coins_count, i)
    levels.append(generated_map)

total_levels = len(levels)

# ---------- Класс Devil (без изменений) ----------
class Devil:
    def __init__(self, col, row, level_index):
        self.col = col
        self.row = row
        self.target_col = col
        self.target_row = row

        self.x = float(col * TILE)
        self.y = float(row * TILE)

        self.level = level_index
        self.speed = 2.5 + (level_index * 0.2)
        self.detect_radius = min(8, 3 + (level_index // 3))

        self.rect = pygame.Rect(self.x, self.y, TILE, TILE)
        self.image = devil_img

        self.state = "patrol"
        self.direction = random.randint(0, 3)
        self.direction_timer = pygame.time.get_ticks()
        self.direction_interval = random.randint(2000, 4000)

    def has_line_of_sight(self, target_col, target_row):
        x0, y0 = int(self.col), int(self.row)
        x1, y1 = int(target_col), int(target_row)
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy

        while True:
            if 0 <= y0 < ROWS and 0 <= x0 < COLS:
                if map_data[y0][x0] == 1:
                    return False
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
        return True

    def decide_next_move(self, p_col, p_row):
        dist_to_player = math.hypot(p_col - self.col, p_row - self.row)

        if dist_to_player <= self.detect_radius and self.has_line_of_sight(p_col, p_row):
            self.state = "chase"
        else:
            self.state = "patrol"

        neighbors = []
        dirs = [(0, -1, 0), (1, 0, 1), (0, 1, 2), (-1, 0, 3)]

        for dc, dr, d_idx in dirs:
            nc, nr = self.col + dc, self.row + dr
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                if map_data[nr][nc] != 1:
                    neighbors.append((nc, nr, d_idx))

        if not neighbors:
            return

        if self.state == "chase":
            def heuristic(n):
                dist = math.hypot(p_col - n[0], p_row - n[1])
                for other in devils:
                    if other != self and other.target_col == n[0] and other.target_row == n[1]:
                        dist += 2.0
                if self.level >= 20:
                    dist -= 0.5
                return dist

            neighbors.sort(key=heuristic)
            best_choice = neighbors[0]
            opposite_dir = (self.direction + 2) % 4

            if best_choice[2] == opposite_dir and len(neighbors) > 1:
                best_choice = neighbors[1]

            self.target_col, self.target_row, self.direction = best_choice
            self.direction_timer = pygame.time.get_ticks()

        else:
            current_time = pygame.time.get_ticks()
            forward_possible = any(n[2] == self.direction for n in neighbors)

            if not forward_possible or current_time - self.direction_timer > self.direction_interval:
                opposite_dir = (self.direction + 2) % 4
                valid_choices = [n for n in neighbors if n[2] != opposite_dir]
                if not valid_choices:
                    valid_choices = neighbors

                choice = random.choice(valid_choices)
                self.target_col, self.target_row, self.direction = choice
                self.direction_timer = current_time
                self.direction_interval = random.randint(2000, 4000)
            else:
                for n in neighbors:
                    if n[2] == self.direction:
                        self.target_col, self.target_row = n[0], n[1]
                        break

    def update(self, player_x, player_y):
        p_col = int((player_x + OFFSET_X + HITBOX_W / 2) // TILE)
        p_row = int((player_y + OFFSET_Y + HITBOX_H / 2) // TILE)

        target_x = self.target_col * TILE
        target_y = self.target_row * TILE

        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.hypot(dx, dy)

        if dist <= self.speed:
            self.x = float(target_x)
            self.y = float(target_y)
            self.col = self.target_col
            self.row = self.target_row
            self.decide_next_move(p_col, p_row)
        else:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def draw(self, surface):
        surface.blit(self.image, (int(self.x), int(self.y)))

# ---------- Механика игры ----------
def load_level(index):
    global map_data, COLS, ROWS, wall_rects, coin_cells, devils
    global start_pos, finish_pos, total_coins, static_bg, player_x, player_y, score

    if index >= len(levels):
        return False

    map_data = [row[:] for row in levels[index]]
    COLS, ROWS = len(map_data[0]), len(map_data)

    start_pos, finish_pos = None, None
    wall_rects = {}
    coin_cells = set()
    devils = []

    static_bg = pygame.Surface((COLS * TILE, ROWS * TILE))

    for row in range(ROWS):
        for col in range(COLS):
            x, y = col * TILE, row * TILE
            cell = map_data[row][col]
            static_bg.blit(grass_img, (x, y))

            if cell == 1:
                wall_rects[(col, row)] = pygame.Rect(x, y, TILE, TILE)
                static_bg.blit(wall_img, (x, y))
            elif cell == 2:
                coin_cells.add((col, row))
            elif cell == 3:
                start_pos = (col, row)
            elif cell == 4:
                finish_pos = (col, row)
            elif cell == 5:
                devils.append(Devil(col, row, index))
                map_data[row][col] = 0

    total_coins = len(coin_cells)
    player_x = float(start_pos[0] * TILE)
    player_y = float(start_pos[1] * TILE)
    score = 0
    return True

def get_hitbox(px, py):
    return pygame.Rect(int(px) + OFFSET_X, int(py) + OFFSET_Y, HITBOX_W, HITBOX_H)

def get_nearby_walls(px, py):
    center_col = int(px + OFFSET_X + HITBOX_W / 2) // TILE
    center_row = int(py + OFFSET_Y + HITBOX_H / 2) // TILE
    nearby = []
    for dc in range(-2, 3):
        for dr in range(-2, 3):
            wall = wall_rects.get((center_col + dc, center_row + dr))
            if wall:
                nearby.append(wall)
    return nearby

def resolve_x(px, py, dx):
    new_px = px + dx
    hb = get_hitbox(new_px, py)
    for wall in get_nearby_walls(new_px, py):
        if hb.colliderect(wall):
            if dx > 0:
                return wall.left - OFFSET_X - HITBOX_W
            else:
                return wall.right - OFFSET_X
    return new_px

def resolve_y(px, py, dy):
    new_py = py + dy
    hb = get_hitbox(px, new_py)
    for wall in get_nearby_walls(px, new_py):
        if hb.colliderect(wall):
            if dy > 0:
                return wall.top - OFFSET_Y - HITBOX_H
            else:
                return wall.bottom - OFFSET_Y
    return new_py

def draw_button(surface, text, x, y, w, h, img, fnt, selected=False):
    mouse_x, mouse_y = pygame.mouse.get_pos()
    rect = pygame.Rect(x, y, w, h)

    if rect.collidepoint(mouse_x, mouse_y):
        new_w, new_h = int(w * 0.92), int(h * 0.92)
        btn_rect = pygame.Rect(x + (w - new_w) // 2, y + (h - new_h) // 2, new_w, new_h)
    else:
        btn_rect = rect

    surface.blit(pygame.transform.scale(img, (btn_rect.width, btn_rect.height)), btn_rect)
    text_surf = fnt.render(text, True, WHITE)
    surface.blit(text_surf, text_surf.get_rect(center=btn_rect.center))

    # Если кнопка выбрана (геймпад / клавиатура) — рисуем рамку
    if selected and joystick is not None:
        pygame.draw.rect(surface, YELLOW, rect, 4)

    return rect

# ---------- Игровой цикл ----------
clock = pygame.time.Clock()
running = True
title_time = 0

# Для меню
buttons = []          # список (rect, действие, текст) — будет заполняться в меню
selected_button = 0   # индекс выбранной кнопки

# Для дисклеймера
disclaimer_ack_btn = None

while running:
    # ---------- Обработка событий ----------
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ---------- События геймпада ----------
        if event.type == pygame.JOYBUTTONDOWN:
            if game_state == STATE_DISCLAIMER:
                if event.button == 0:  # A — подтвердить
                    game_state = STATE_MENU
                    selected_button = 0

            elif game_state == STATE_MENU:
                if event.button == 0:  # A — подтвердить
                    if buttons and 0 <= selected_button < len(buttons):
                        action = buttons[selected_button][1]
                        action()  # вызов функции (start или exit)
                elif event.button == 1:  # B — выход
                    running = False

            elif game_state == STATE_PLAY:
                if event.button == 1:  # B — выйти в меню
                    game_state = STATE_MENU
                    stop_sound('death')  # на всякий случай

        if event.type == pygame.JOYHATMOTION:
            if game_state == STATE_MENU:
                # D-pad вверх/вниз
                if event.value == (0, 1):   # вверх
                    selected_button = (selected_button - 1) % len(buttons) if buttons else 0
                elif event.value == (0, -1): # вниз
                    selected_button = (selected_button + 1) % len(buttons) if buttons else 0

        # ---------- События мыши ----------
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_state == STATE_DISCLAIMER:
                if disclaimer_ack_btn and disclaimer_ack_btn.collidepoint(event.pos):
                    game_state = STATE_MENU
                    selected_button = 0

            elif game_state == STATE_MENU:
                for i, (rect, action, text) in enumerate(buttons):
                    if rect.collidepoint(event.pos):
                        action()
                        break

            elif game_state == STATE_PLAY:
                if back_btn.collidepoint(event.pos):
                    game_state = STATE_MENU
                    stop_sound('death')

        # ---------- События клавиатуры ----------
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F9 or event.key == pygame.K_F11:
                is_fullscreen = not is_fullscreen
                flags = pygame.SCALED | (pygame.FULLSCREEN if is_fullscreen else 0)
                screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)

            if game_state == STATE_DEATH:
                stop_sound('death')
                game_state = STATE_MENU

            # Навигация в меню по стрелкам клавиатуры
            if game_state == STATE_MENU:
                if event.key == pygame.K_UP:
                    selected_button = (selected_button - 1) % len(buttons) if buttons else 0
                elif event.key == pygame.K_DOWN:
                    selected_button = (selected_button + 1) % len(buttons) if buttons else 0
                elif event.key == pygame.K_RETURN:
                    if buttons and 0 <= selected_button < len(buttons):
                        action = buttons[selected_button][1]
                        action()

    # ---------- Логика геймпада (движение в игре) ----------
    # Обрабатываем оси отдельно, чтобы движение было плавным
    dx_gamepad, dy_gamepad = 0, 0
    if joystick and game_state == STATE_PLAY:
        # Левый стик: оси 0 и 1
        axis_x = joystick.get_axis(0)
        axis_y = joystick.get_axis(1)
        # Мертвая зона (чтобы не дёргалось)
        dead_zone = 0.2
        if abs(axis_x) > dead_zone:
            dx_gamepad = axis_x * player_speed
        if abs(axis_y) > dead_zone:
            dy_gamepad = axis_y * player_speed

    # ---------- Отрисовка ----------
    # ---------- ДИСКЛЕЙМЕР ----------
    if game_state == STATE_DISCLAIMER:
        screen.fill(BLACK)

        # Заголовок
        warn = font_title.render("WARNING", True, RED)
        screen.blit(warn, warn.get_rect(center=(WIDTH // 2, 80)))

        # Текст
        lines = [
            "This game contains:",
            "• Bright flashes",
            "  (may cause discomfort for people with epilepsy)",
            "",
            "• Loud sounds",
            "",
            "By pressing 'I UNDERSTAND' you confirm",
            "that you have read and understood this warning.",
        ]
        y = 180
        for line in lines:
            if line == "":
                y += 20
                continue
            text = font_disclaimer.render(line, True, WHITE)
            screen.blit(text, text.get_rect(center=(WIDTH // 2, y)))
            y += 40

        # Кнопка "ПОНЯТНО"
        btn_w, btn_h = 300, 70
        btn_x = (WIDTH - btn_w) // 2
        btn_y = 580
        disclaimer_ack_btn = draw_button(
            screen, "I UNDERSTAND", btn_x, btn_y, btn_w, btn_h, btn_img, font
        )

    # ---------- ГЛАВНОЕ МЕНЮ ----------
    elif game_state == STATE_MENU:
        screen.blit(menu_bg, (0, 0))

        hint = font_small.render("F9 / F11 - Fullscreen", True, WHITE)
        screen.blit(hint, (20, 20))

        title_time += 0.045
        title_y = 120 + math.sin(title_time) * 8
        title_text = font_title.render("SMILE MASK", True, (168, 23, 23))
        screen.blit(title_text, title_text.get_rect(center=(WIDTH // 2, title_y)))

        btn_w, btn_h = 240, 70
        btn_x = (WIDTH - btn_w) // 2

        # Определяем кнопки и их действия
                # Определяем кнопки и их действия
        def action_start():
            global current_level, game_state
            current_level = 0
            load_level(current_level)
            game_state = STATE_PLAY

        def action_exit():
            global running
            running = False

        buttons = [
            (pygame.Rect(btn_x, 300, btn_w, btn_h), action_start, "START"),
            (pygame.Rect(btn_x, 400, btn_w, btn_h), action_exit, "EXIT"),
        ]

        # Рисуем кнопки с подсветкой выбранной
        for i, (rect, action, text) in enumerate(buttons):
            selected = (i == selected_button)
            # Обновляем rect в списке, т.к. draw_button возвращает rect (может измениться из-за hover)
            rect = draw_button(screen, text, rect.x, rect.y, rect.w, rect.h, btn_img, font, selected)
            buttons[i] = (rect, action, text)

        # (Кнопки остаются доступными и для мыши — в обработчике событий)

    # ---------- ИГРА ----------
    elif game_state == STATE_PLAY:
        # Движение: клавиатура + геймпад (суммируем)
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= player_speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += player_speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= player_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += player_speed

        # Добавляем геймпад (если есть)
        if joystick:
            # Нормализуем, чтобы скорость не превышала player_speed
            if abs(dx_gamepad) > 0.1 or abs(dy_gamepad) > 0.1:
                # Если клавиатура тоже нажата, суммируем, но ограничим по модулю
                dx += dx_gamepad
                dy += dy_gamepad
                # Ограничим максимальную скорость (по диагонали не быстрее)
                if math.hypot(dx, dy) > player_speed:
                    scale = player_speed / math.hypot(dx, dy)
                    dx *= scale
                    dy *= scale

        if (dx != 0 or dy != 0):
            if pygame.time.get_ticks() - step_timer > STEP_DELAY:
                play_sound('step')
                step_timer = pygame.time.get_ticks()

        player_x = resolve_x(player_x, player_y, dx)
        player_y = resolve_y(player_x, player_y, dy)
        player_hb = get_hitbox(player_x, player_y)

        # Сбор монет
        center_col = int(player_x + OFFSET_X + HITBOX_W / 2) // TILE
        center_row = int(player_y + OFFSET_Y + HITBOX_H / 2) // TILE
        for c_dc in range(-1, 2):
            for c_dr in range(-1, 2):
                key = (center_col + c_dc, center_row + c_dr)
                if key in coin_cells:
                    if player_hb.colliderect(pygame.Rect(key[0] * TILE, key[1] * TILE, TILE, TILE)):
                        coin_cells.remove(key)
                        score += 1
                        play_sound('coin')

        # Обновление врагов
        for devil in devils:
            devil.update(player_x, player_y)

        # Отрисовка уровня на виртуальную поверхность
        game_surf = pygame.Surface((COLS * TILE, ROWS * TILE))
        game_surf.blit(static_bg, (0, 0))
        if start_pos:
            game_surf.blit(start_img, (start_pos[0] * TILE, start_pos[1] * TILE))
        if finish_pos:
            game_surf.blit(finish_img, (finish_pos[0] * TILE, finish_pos[1] * TILE))

        for col, row in coin_cells:
            game_surf.blit(coin_img, (col * TILE, row * TILE))

        for devil in devils:
            devil.draw(game_surf)

        game_surf.blit(player_img, (int(player_x), int(player_y)))

        # Атмосфера (затенение)
        darkness = pygame.Surface((COLS * TILE, ROWS * TILE))
        darkness.set_alpha(80)
        darkness.fill(BLACK)
        game_surf.blit(darkness, (0, 0))

        # Вывод игры по центру
        screen.fill(BLACK)
        screen_offset_x = (WIDTH - COLS * TILE) // 2
        screen_offset_y = (HEIGHT - ROWS * TILE) // 2
        screen.blit(game_surf, (screen_offset_x, screen_offset_y))

        # UI поверх всего
        score_text = font_small.render(f"Coins: {score}/{total_coins}", True, WHITE)
        screen.blit(score_text, score_text.get_rect(topright=(WIDTH - 20, 20)))

        lvl_text = font_small.render(f"Level: {current_level + 1}/{total_levels}", True, WHITE)
        screen.blit(lvl_text, lvl_text.get_rect(topright=(WIDTH - 20, 50)))

        back_btn = pygame.Rect(20, 20, 60, 30)
        screen.blit(exit_btn_small, back_btn)
        arrow = font_small.render("<", True, WHITE)
        screen.blit(arrow, arrow.get_rect(center=back_btn.center))

        # Проверка смерти
        for devil in devils:
            if player_hb.colliderect(devil.rect):
                play_sound('death', -1)
                game_state = STATE_DEATH
                break

        # Проверка выхода
        if score == total_coins and finish_pos:
            if player_hb.colliderect(pygame.Rect(finish_pos[0] * TILE, finish_pos[1] * TILE, TILE, TILE)):
                current_level += 1
                if current_level < total_levels:
                    load_level(current_level)
                else:
                    game_state = STATE_MENU

    # ---------- ЭКРАН СМЕРТИ ----------
    elif game_state == STATE_DEATH:
        game_surf = pygame.Surface((COLS * TILE, ROWS * TILE))
        game_surf.blit(static_bg, (0, 0))
        for col, row in coin_cells:
            game_surf.blit(coin_img, (col * TILE, row * TILE))
        for devil in devils:
            devil.draw(game_surf)
        game_surf.blit(player_img, (int(player_x), int(player_y)))

        overlay = pygame.Surface((COLS * TILE, ROWS * TILE))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        game_surf.blit(overlay, (0, 0))

        screen.fill(BLACK)
        screen_offset_x = (WIDTH - COLS * TILE) // 2
        screen_offset_y = (HEIGHT - ROWS * TILE) // 2
        screen.blit(game_surf, (screen_offset_x, screen_offset_y))

        death_text = font_death.render("YOU DIED", True, RED)
        screen.blit(death_text, death_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))

        hint = font_small.render("Press any key", True, WHITE)
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80)))

        pulse = abs(math.sin(pygame.time.get_ticks() / 300)) * 50
        red_pulse = pygame.Surface((WIDTH, HEIGHT))
        red_pulse.set_alpha(int(pulse))
        red_pulse.fill(RED)
        screen.blit(red_pulse, (0, 0))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()