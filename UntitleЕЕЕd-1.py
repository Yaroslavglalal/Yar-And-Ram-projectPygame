import pygame
import random
import time
import math
from collections import deque

pygame.init()  # Инициализация библиотеки Pygame

# Размеры экрана
WIDTH, HEIGHT = 800, 600
win = pygame.display.set_mode((WIDTH, HEIGHT))  # Окно игры
pygame.display.set_caption("Лабиринтная игра")  # Заголовок окна

# Цвета, которые будут использоваться в игре
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GRAY = (128, 128, 128)
GREEN = (0, 255, 0)

# Размеры игрока и монстра
player_size = 5
player_hp = 100  # Здоровье игрока
player_speed = 5  # Скорость игрока

monster_size = 30  # Размер монстра
monster_speed = 0.5  # Скорость монстра

# Создаем класс для эхолокационных волн
class EchoWave:
    def __init__(self, x, y, radius=10, max_radius=200):
        self.x = x
        self.y = y
        self.radius = radius
        self.max_radius = max_radius
        self.color = (0, 255, 255)  # Цвет волны (голубой)

    def expand(self):
        if self.radius < self.max_radius:
            self.radius += 2  # Увеличиваем радиус волны
        else:
            return False  # Если волна достигла максимального радиуса, она исчезает
        return True

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (self.x, self.y), self.radius, 2)

    def affects_wall(self, wall):
        wall_center = wall.center
        distance = math.hypot(wall_center[0] - self.x, wall_center[1] - self.y)
        return distance < self.radius


# Список для хранения всех волн эхолокации
echo_waves = []

# Функция для генерации лабиринта с использованием алгоритма DFS (поиск в глубину)
def generate_dfs_maze(rows, cols):
    maze = [[1 for _ in range(cols)] for _ in range(rows)]  # Заполняем лабиринт стенами (1)
    start_cell = (0, 0)  # Стартовая клетка
    stack = [start_cell]
    maze[start_cell[0]][start_cell[1]] = 0  # Стартовая клетка – это проходимая область

    # Основной цикл генерации лабиринта
    while stack:
        current = stack[-1]
        neighbors = get_dfs_neighbors(current, rows, cols, maze)

        if neighbors:
            next_cell = random.choice(neighbors)  # Выбираем случайного соседа
            stack.append(next_cell)
            maze[next_cell[0]][next_cell[1]] = 0  # Делаем его проходимым
            maze[(current[0] + next_cell[0]) // 2][
                (current[1] + next_cell[1]) // 2] = 0  # Прорубаем путь между клетками
        else:
            stack.pop()  # Если нет соседей для дальнейшего движения, отступаем назад

    return maze


# Функция для получения соседей текущей клетки для алгоритма DFS
def get_dfs_neighbors(cell, rows, cols, maze):
    x, y = cell
    neighbors = []
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < rows and 0 <= ny < cols and maze[nx][ny] == 1:  # Проверяем, является ли клетка стеной
            neighbors.append((nx, ny))
    return neighbors


# Функция для отрисовки лабиринта
def render_maze(maze, wall_size):
    walls = []
    for i, row in enumerate(maze):
        for j, cell in enumerate(row):
            if cell == 1:  # Если клетка стена
                walls.append(
                    pygame.Rect(j * wall_size, i * wall_size, wall_size, wall_size))  # Рисуем прямоугольник для стены
    return walls


# Инициализация начальных параметров
current_level = 0
walls = []
exit_rect = pygame.Rect(WIDTH - 60, HEIGHT - 60, 40, 40)  # Прямоугольник выхода из лабиринта

font = pygame.font.SysFont("Arial", 24)  # Шрифт для текста

history = []  # Список для истории игр


# Функция для отрисовки текста на экране
def draw_text(text, x, y, color):
    render = font.render(text, True, color)
    win.blit(render, (x, y))


# Функция сброса уровня
def reset_level():
    global player_pos, monster_pos, player_hp, start_time
    while True:
        player_pos = [random.randint(100, WIDTH - 100 - player_size), random.randint(100, HEIGHT - 100 - player_size)]
        # Проверка, не накладывается ли игрок на стену
        if not any(pygame.Rect(player_pos[0], player_pos[1], player_size, player_size).colliderect(wall) for wall in
                   walls):
            break

    # Начальная позиция монстра, чтобы он был далеко от игрока
    monster_pos = [max(0, player_pos[0] - 250), max(0, player_pos[1] - 250)]
    player_hp = 100  # Восстанавливаем здоровье игрока
    start_time = time.time()  # Засекаем время начала игры


# Начальная позиция игрока и монстра
player_pos = [150, 150]
monster_pos = [max(0, player_pos[0] - 250), max(0, player_pos[1] - 250)]

# Часы для управления частотой обновления экрана
clock = pygame.time.Clock()
running = True  # Основной цикл игры
menu = True  # Главное меню
game_over = False  # Состояние игры
difficulty = "Легкий"  # Начальная сложность
current_stage = 0  # Текущий уровень
stages_per_difficulty = 3  # Количество уровней для каждой сложности

# Сложность игры и соответствующие размеры лабиринта
maze_difficulty = {
    "Легкий": (15, 15),
    "Средний": (25, 25),
    "Сложный": (35, 35)
}


# Главная функция меню
def main_menu():
    global menu, difficulty, current_stage
    while menu:
        win.fill(BLACK)  # Заполнение экрана черным
        draw_text("Лабиринтная игра", WIDTH // 2 - 120, HEIGHT // 2 - 200, WHITE)  # Отображение заголовка
        easy_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 50)  # Кнопка для легкого уровня
        medium_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 20, 200, 50)  # Кнопка для среднего уровня
        hard_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 90, 200, 50)  # Кнопка для сложного уровня
        history_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 160, 200, 50)  # Кнопка для истории игр

        # Отрисовка кнопок
        pygame.draw.rect(win, GREEN, easy_button)
        pygame.draw.rect(win, GRAY, medium_button)
        pygame.draw.rect(win, RED, hard_button)
        pygame.draw.rect(win, WHITE, history_button)

        # Тексты на кнопках
        draw_text("Легкий", WIDTH // 2 - 30, HEIGHT // 2 - 40, BLACK)
        draw_text("Средний", WIDTH // 2 - 40, HEIGHT // 2 + 30, BLACK)
        draw_text("Сложный", WIDTH // 2 - 40, HEIGHT // 2 + 100, BLACK)
        draw_text("История игр", WIDTH // 2 - 70, HEIGHT // 2 + 170, BLACK)

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if easy_button.collidepoint(event.pos):
                    difficulty = "Легкий"
                    start_game()
                if medium_button.collidepoint(event.pos):
                    difficulty = "Средний"
                    start_game()
                if hard_button.collidepoint(event.pos):
                    difficulty = "Сложный"
                    start_game()
                if history_button.collidepoint(event.pos):
                    show_history()

        pygame.display.update()  # Обновление экрана

# Функция для отображения истории игр
def show_history():
    showing = True
    while showing:
        win.fill(BLACK)
        draw_text("История игр", WIDTH // 2 - 120, 50, WHITE)
        y_offset = 100
        for record in history:
            draw_text(record, 50, y_offset, WHITE)
            y_offset += 30
        back_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 100, 200, 50)
        pygame.draw.rect(win, GRAY, back_button)
        draw_text("Вернуться в меню", WIDTH // 2 - 95, HEIGHT - 85, BLACK)

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(event.pos):
                    return_to_menu()

        pygame.display.update()

# Функция для возврата в меню
def return_to_menu():
    global menu
    menu = True
    main_menu()


# Функция для начала игры
def start_game():
    global menu, current_stage, walls, player_pos, monster_pos, player_hp, start_time, game_over
    menu = False
    current_stage = 0
    rows, cols = maze_difficulty[difficulty]
    maze = generate_dfs_maze(rows, cols)
    walls = render_maze(maze, WIDTH // cols)
    reset_level()  # Сброс начальных параметров
    game_over = False  # Сбрасываем состояние игры


# Функция окончания игры (при проигрыше)
def game_over_screen():
    win.fill(BLACK)
    draw_text("Ты проиграл!", WIDTH // 2 - 70, HEIGHT // 2 - 50, RED)

    # Кнопка для возврата в главное меню
    backk_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 100, 200, 50)
    back_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 100, 200, 50)
    pygame.draw.rect(win, GRAY, back_button)
    draw_text("Вернуться в меню", WIDTH // 2 - 95, HEIGHT - 85, BLACK)

    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if back_button.collidepoint(event.pos):
                return_to_menu()


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if return_button.collidepoint(event.pos):
                main_menu()

    pygame.display.update()


# Основной игровой цикл
main_menu()

while running:
    win.fill(BLACK)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if menu:
        main_menu()
        continue

    if game_over:
        game_over_screen()
        continue

    # Управление движением игрока
    keys = pygame.key.get_pressed()
    dx, dy = 0, 0
    if keys[pygame.K_UP]:
        dy = -player_speed
    if keys[pygame.K_DOWN]:
        dy = player_speed
    if keys[pygame.K_LEFT]:
        dx = -player_speed
    if keys[pygame.K_RIGHT]:
        dx = player_speed

    # Проверка столкновений с стенами
    next_pos = pygame.Rect(player_pos[0] + dx, player_pos[1] + dy, player_size, player_size)
    collision = False
    for wall in walls:
        if next_pos.colliderect(wall):
            collision = True
            player_hp -= 1
            break

    if not collision:
        player_pos[0] += dx
        player_pos[1] += dy

    # Ограничение перемещения игрока по экрану
    player_pos[0] = max(0, min(WIDTH - player_size, player_pos[0]))
    player_pos[1] = max(0, min(HEIGHT - player_size, player_pos[1]))

    # Управление монстром
    direction = [player_pos[0] - monster_pos[0], player_pos[1] - monster_pos[1]]
    length = math.hypot(direction[0], direction[1])
    direction = [direction[0] / length, direction[1] / length]
    monster_pos[0] += direction[0] * monster_speed
    monster_pos[1] += direction[1] * monster_speed

    # Если монстр столкнулся с игроком, игра окончена
    if pygame.Rect(player_pos[0], player_pos[1], player_size, player_size).colliderect(pygame.Rect(monster_pos[0], monster_pos[1], monster_size, monster_size)):
        game_over = True
    if player_hp <= 0:
        game_over = True

    # Проверка достижения выхода
    if exit_rect.colliderect(pygame.Rect(player_pos[0], player_pos[1], player_size, player_size)):
        current_stage += 1
        reset_level()

    # Отрисовка лабиринта, игрока и монстра
    for wall in walls:
        # Стены отображаются только если волна эхолокации их затронула
        if any(wave.affects_wall(wall) for wave in echo_waves):
            pygame.draw.rect(win, GRAY, wall)

    pygame.draw.rect(win, GREEN, pygame.Rect(player_pos[0], player_pos[1], player_size, player_size))  # Игрок
    pygame.draw.rect(win, RED, pygame.Rect(monster_pos[0], monster_pos[1], monster_size, monster_size))  # Монстр
    pygame.draw.rect(win, WHITE, exit_rect)  # Выход

    # Отображаем информацию о жизни
    draw_text(f"HP: {player_hp}", 10, 10, WHITE)

    # Обработка эхолокационных волн
    if keys[pygame.K_SPACE]:
        new_wave = EchoWave(player_pos[0] + player_size // 2, player_pos[1] + player_size // 2)
        echo_waves.append(new_wave)

    # Обработка расширения волн и их отрисовка
    for wave in echo_waves[:]:
        if not wave.expand():
            echo_waves.remove(wave)

    for wave in echo_waves:
        wave.draw(win)
    elapsed_time = time.time() - start_time
    draw_text(f"Время: {round(elapsed_time, 2)} сек.", WIDTH - 200, 10, WHITE)
    print(elapsed_time)

    pygame.display.update()  # Обновление экрана
    clock.tick(60)  # Частота обновления экрана

pygame.quit()
