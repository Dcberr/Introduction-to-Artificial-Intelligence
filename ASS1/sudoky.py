import time
import tracemalloc
import tkinter as tk
from tkinter import messagebox
import random
import heapq

def is_valid(board, row, col, num):
    for i in range(9):
        if board[row][i] == num or board[i][col] == num:
            return False
    
    start_row, start_col = 3 * (row // 3), 3 * (col // 3)
    for i in range(3):
        for j in range(3):
            if board[start_row + i][start_col + j] == num:
                return False
    
    return True

def dfs_solve(board):
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                for num in range(1, 10):
                    if is_valid(board, row, col, num):
                        board[row][col] = num
                        if dfs_solve(board):
                            return True
                        board[row][col] = 0
                return False
    return True

def find_candidates(board, row, col):
    candidates = set(range(1, 10))
    for i in range(9):
        candidates.discard(board[row][i])
        candidates.discard(board[i][col])
    r, c = (row // 3) * 3, (col // 3) * 3
    for i in range(3):
        for j in range(3):
            candidates.discard(board[r + i][c + j])
    return list(candidates)

def heuristic_solve(board):
    empty_cells = [(len(find_candidates(board, row, col)), row, col)
                   for row in range(9) for col in range(9) if board[row][col] == 0]
    heapq.heapify(empty_cells)

    def backtrack():
        if not empty_cells:
            return True
        
        _, row, col = heapq.heappop(empty_cells)
        candidates = find_candidates(board, row, col)

        for num in candidates:
            board[row][col] = num
            if backtrack():
                return True
            board[row][col] = 0

        heapq.heappush(empty_cells, (len(candidates), row, col))
        return False

    return backtrack()

def measure_performance(board, solve_function, method_name):
    tracemalloc.start()  # Bắt đầu theo dõi bộ nhớ
    start_time = time.time()  # Lấy thời gian bắt đầu

    solved_board = [row[:] for row in board]  # Sao chép mảng để không làm thay đổi mảng gốc
    success = solve_function(solved_board)

    end_time = time.time()  # Lấy thời gian kết thúc
    memory_used = tracemalloc.get_traced_memory()[1] / 1024  # Lấy bộ nhớ tối đa sử dụng (KB)
    tracemalloc.stop()  # Dừng theo dõi bộ nhớ

    print(f"📌 {method_name}:")
    print(f"   ✅ Đã giải: {'Thành công' if success else 'Thất bại'}")
    print(f"   ⏳ Thời gian chạy: {end_time - start_time:.6f} giây")
    print(f"   💾 Bộ nhớ tiêu thụ: {memory_used:.2f} KB\n")

def generate_board():
    board = [[0] * 9 for _ in range(9)]
    for _ in range(17):
        row, col = random.randint(0, 8), random.randint(0, 8)
        num = random.randint(1, 9)
        while not is_valid(board, row, col, num) or board[row][col] != 0:
            row, col = random.randint(0, 8), random.randint(0, 8)
            num = random.randint(1, 9)
        board[row][col] = num
    return board

# Tạo một bảng Sudoku và đo hiệu suất
board = generate_board()

print("⚡ Đánh giá hiệu suất các thuật toán giải Sudoku ⚡")
measure_performance(board, dfs_solve, "DFS (Backtracking)")
measure_performance(board, heuristic_solve, "Heuristic (A*)")
