import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from collections import deque

def bfs(maze, start, goal):
    queue = deque([(start, [])])  # Hàng đợi BFS, mỗi phần tử là (vị trí hiện tại, đường đi đã đi qua)
    visited = set()  # Tập hợp các ô đã được duyệt qua
    
    while queue:  # Lặp đến khi hàng đợi trống
        current, path = queue.popleft()  # Lấy phần tử đầu tiên trong hàng đợi
        x, y = current
        
        if current == goal:  # Nếu đến đích, trả về đường đi
            return path + [current]
        
        if current in visited:  # Nếu ô đã được duyệt, bỏ qua
            continue
        
        visited.add(current)  # Đánh dấu ô đã được duyệt
        
        # Duyệt các ô lân cận (trái, phải, trên, dưới)
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            # Kiểm tra điều kiện hợp lệ
            if 0 <= nx < len(maze) and 0 <= ny < len(maze[0]) and maze[nx][ny] != 1:
                queue.append(((nx, ny), path + [current]))  # Thêm vào hàng đợi
    
    return None  # Nếu không tìm được đường đi, trả về None


def visualize_maze(maze, start, goal, path=None):
    cmap = ListedColormap(['white', 'black', 'red', 'blue', 'green'])  # Định nghĩa màu sắc
    bounds = [0, 0.5, 1.5, 2.5, 3.5, 4.5]
    norm = plt.Normalize(bounds[0], bounds[-1])
    
    fig, ax = plt.subplots()
    ax.imshow(maze, cmap=cmap, norm=norm)  # Vẽ mê cung
    
    ax.scatter(start[1], start[0], color='yellow', marker='o', label='Start')  # Vẽ điểm bắt đầu
    ax.scatter(goal[1], goal[0], color='purple', marker='o', label='Goal')  # Vẽ điểm đích
    
    if path:  # Nếu có đường đi hợp lệ
        for node in path[1:-1]:
            ax.scatter(node[1], node[0], color='green', marker='o')  # Vẽ đường đi bằng màu xanh
    
    ax.legend()
    plt.show()

maze = np.array([
    [0, 0, 0, 0, 0, 0],
    [1, 1, 0, 1, 1, 0],
    [0, 0, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0]
])

start = (0, 0)  # Điểm bắt đầu
goal = (4, 2)  # Điểm kết thúc

path = bfs(maze, start, goal)  # Chạy thuật toán BFS
visualize_maze(maze, start, goal, path)  # Hiển thị mê cung và đường đi
