import tkinter as tk
from tkinter import messagebox
import random
import heapq
import time
import tracemalloc

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

def measure_performance(algorithm, board):
    board_copy = [row[:] for row in board]
    tracemalloc.start()
    start_time = time.time()
    success = algorithm(board_copy)
    end_time = time.time()
    memory_used = tracemalloc.get_traced_memory()[1] / 1024
    tracemalloc.stop()
    execution_time = end_time - start_time
    return execution_time, memory_used, success

def solve_with_ai():
    global board, entries
    dfs_time, dfs_memory, dfs_success = measure_performance(dfs_solve, board)
    heuristic_time, heuristic_memory, heuristic_success = measure_performance(heuristic_solve, board)
    
    solved_board = [row[:] for row in board]
    if heuristic_success:
        heuristic_solve(solved_board)
    elif dfs_success:
        dfs_solve(solved_board)
    else:
        messagebox.showerror("Error", "AI could not solve the Sudoku.")
        return
    
    for i in range(9):
        for j in range(9):
            entries[i][j].delete(0, tk.END)
            entries[i][j].insert(0, str(solved_board[i][j]))
            entries[i][j].config(state='disabled')
    
    messagebox.showinfo("Performance", f"DFS: {dfs_time:.4f}s, {dfs_memory:.2f}KB\nHeuristic: {heuristic_time:.4f}s, {heuristic_memory:.2f}KB")

def check_solution():
    for row in range(9):
        for col in range(9):
            num = entries[row][col].get()
            if not num.isdigit() or not (1 <= int(num) <= 9):
                messagebox.showerror("Error", "Invalid input! Only numbers 1-9 are allowed.")
                return
            board[row][col] = int(num)
    
    if heuristic_solve([row[:] for row in board]) or dfs_solve([row[:] for row in board]):
        messagebox.showinfo("Success", "Congratulations! You solved the Sudoku!")
    else:
        messagebox.showerror("Error", "Incorrect solution. Try again!")

def new_game():
    global board, entries
    board = generate_board()
    for i in range(9):
        for j in range(9):
            entries[i][j].config(state='normal')
            entries[i][j].delete(0, tk.END)
            if board[i][j] != 0:
                entries[i][j].insert(0, str(board[i][j]))
                entries[i][j].config(state='disabled')

def create_ui():
    global root, entries, board
    root = tk.Tk()
    root.title("Sudoku Game")
    
    board = generate_board()
    entries = []
    
    for i in range(9):
        row_entries = []
        for j in range(9):
            entry = tk.Entry(root, width=3, font=('Arial', 18), justify='center')
            entry.grid(row=i, column=j, padx=2, pady=2)
            if board[i][j] != 0:
                entry.insert(0, str(board[i][j]))
                entry.config(state='disabled')
            row_entries.append(entry)
        entries.append(row_entries)
    
    check_button = tk.Button(root, text="Check Solution", command=check_solution)
    check_button.grid(row=9, column=0, columnspan=3, pady=10)
    
    ai_button = tk.Button(root, text="Solve with AI", command=solve_with_ai)
    ai_button.grid(row=9, column=3, columnspan=3, pady=10)
    
    new_game_button = tk.Button(root, text="New Game", command=new_game)
    new_game_button.grid(row=9, column=6, columnspan=3, pady=10)
    
    root.mainloop()

create_ui()
