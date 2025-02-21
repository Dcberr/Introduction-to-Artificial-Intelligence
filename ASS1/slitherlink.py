import pygame
import random
from collections import deque

# Constants
WIDTH, HEIGHT = 600, 600
grid_size = 4 
tile_size = WIDTH // grid_size
FPS = 60

# Colors
BACKGROUND = (240, 230, 200)
BORDER = (60, 60, 60)
PIPE_COLOR_CONNECTED = (50, 100, 255)  # Blue when connected
PIPE_COLOR_DISCONNECTED = (255, 255, 255)  # White when disconnected
FIXED_COLOR = (200, 50, 50)
GRID_COLOR = (200, 200, 180)
WATER_SOURCE_COLOR = (255, 0, 0)  # Red circle for water source

# Pipe directions (Up, Right, Down, Left)
DIRECTIONS = [(0, -1), (1, 0), (0, 1), (-1, 0)]


class PipeTile:
    def __init__(self, x, y, connections):
        self.x, self.y = x, y
        self.connections = connections  # e.g., [True, False, True, False]
        self.fixed = False
        self.rotation = 0
        self.connected = False  # Flag to indicate if pipe is connected
        self.is_water_source = False  # Is this the water source?

    def rotate(self, clockwise=True):
        if not self.fixed:
            self.connections = self.connections[-1:] + self.connections[:-1] if clockwise else self.connections[1:] + self.connections[:1]
            self.rotation = (self.rotation + (90 if clockwise else -90)) % 360

    def draw(self, screen):
        pygame.draw.rect(screen, BACKGROUND, (self.x * tile_size, self.y * tile_size, tile_size, tile_size))
        pygame.draw.rect(screen, BORDER, (self.x * tile_size, self.y * tile_size, tile_size, tile_size), 2)

        center = (self.x * tile_size + tile_size // 2, self.y * tile_size + tile_size // 2)
        pipe_color = PIPE_COLOR_CONNECTED if self.connected else PIPE_COLOR_DISCONNECTED

        for i, connected in enumerate(self.connections):
            if connected:
                end = (center[0] + DIRECTIONS[i][0] * tile_size // 2, center[1] + DIRECTIONS[i][1] * tile_size // 2)
                pygame.draw.line(screen, pipe_color, center, end, 8)
                pygame.draw.circle(screen, pipe_color, end, 6)

        if self.fixed:
            pygame.draw.circle(screen, FIXED_COLOR, center, 8)

        if self.is_water_source:
            pygame.draw.circle(screen, WATER_SOURCE_COLOR, center, 10)  # Draw red circle for water source


class PipeGame:
    def __init__(self):
        self.grid = [[PipeTile(x, y, random.choices([True, False], k=4)) for y in range(grid_size)] for x in range(grid_size)]
        self.water_source = self.place_water_source()
        self.update_connections()

    def place_water_source(self):
        """Places a water source at a random tile with at least one open connection."""
        while True:
            x, y = random.randint(0, grid_size - 1), random.randint(0, grid_size - 1)
            if any(self.grid[x][y].connections):  # Ensure at least one connection
                self.grid[x][y].is_water_source = True
                return x, y

    def draw(self, screen):
        pygame.draw.rect(screen, GRID_COLOR, (tile_size - 5, tile_size - 5, WIDTH - 2 * tile_size + 10, HEIGHT - 2 * tile_size + 10))
        pygame.draw.rect(screen, BORDER, (tile_size - 5, tile_size - 5, WIDTH - 2 * tile_size + 10, HEIGHT - 2 * tile_size + 10), 4)
        for row in self.grid:
            for tile in row:
                tile.draw(screen)

    def rotate_tile(self, x, y, clockwise=True):
        self.grid[x][y].rotate(clockwise)
        self.update_connections()

    def update_connections(self):
        """BFS to determine connected pipes from the water source."""
        for row in self.grid:
            for tile in row:
                tile.connected = False  # Reset all pipes to disconnected

        x, y = self.water_source  # Start from the water source
        queue = deque([(x, y)])
        self.grid[x][y].connected = True

        while queue:
            x, y = queue.popleft()
            current_tile = self.grid[x][y]

            for i, (dx, dy) in enumerate(DIRECTIONS):
                nx, ny = x + dx, y + dy

                if 0 <= nx < grid_size and 0 <= ny < grid_size:  # Ensure inside grid
                    neighbor = self.grid[nx][ny]

                    # Check if pipes are connected
                    if current_tile.connections[i] and neighbor.connections[(i + 2) % 4] and not neighbor.connected:
                        neighbor.connected = True
                        queue.append((nx, ny))


# Pygame setup
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pipes Game")
clock = pygame.time.Clock()

game = PipeGame()

running = True
while running:
    screen.fill(BORDER)
    game.draw(screen)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            grid_x, grid_y = x // tile_size, y // tile_size
            if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
                if event.button == 1:
                    game.rotate_tile(grid_x, grid_y)
                elif event.button == 3:
                    game.grid[grid_x][grid_y].fixed = not game.grid[grid_x][grid_y].fixed

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
