import tkinter as tk
from tkinter import messagebox, ttk
import random
import heapq
import time
import tracemalloc
import gc

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
                        gc.collect()
                        entries[row][col].delete(0, tk.END)
                        entries[row][col].insert(0, str(num))
                        entries[row][col].config(fg="blue")
                        root.update_idletasks()
                        # time.sleep(0.001) # Chờ 0.1 giây để thấy rõ thay đổi
                        # root.after(1, dfs_solve)
                        if dfs_solve(board):
                            return True
                        board[row][col] = 0
                return False
    return True

def stop_solving():
    global solving
    solving = False

def reset_game():
    global board, original_board
    for i in range(9):
        for j in range(9):
            entries[i][j].config(state='normal')
            entries[i][j].delete(0, tk.END)
            if original_board[i][j] != 0:
                entries[i][j].insert(0, str(original_board[i][j]))
                entries[i][j].config(state='disabled')
            else:
                entries[i][j].config(fg="black")
    board = [row[:] for row in original_board]

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
            gc.collect()
            entries[row][col].delete(0, tk.END)
            entries[row][col].insert(0, str(num))
            entries[row][col].config(fg="blue")
            root.update_idletasks()
            # time.sleep(0.001) # Chờ 0.1 giây để thấy rõ thay đổi
            # root.after(1, backtrack)
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
    start_snapshot = tracemalloc.take_snapshot()
    start_time = time.time()
    
    success = algorithm(board_copy)

    end_time = time.time()
    end_snapshot = tracemalloc.take_snapshot()
    memory_stats = end_snapshot.compare_to(start_snapshot, 'lineno')
    memory_used = sum(stat.size_diff for stat in memory_stats) / 1024  # KB

    tracemalloc.stop()
    execution_time = end_time - start_time
    return execution_time, memory_used, success


def solve_with_dfs():
    global board, entries
    dfs_time, dfs_memory, dfs_success = measure_performance(dfs_solve, board)
    
    solved_board = [row[:] for row in board]
    if dfs_success:
        dfs_solve(solved_board)
    else:
        messagebox.showerror("Error", "AI DFS could not solve the Sudoku.")
        return
    
    messagebox.showinfo("Performance", f"DFS: {dfs_time:.4f}s, {dfs_memory:.2f}KB")

def solve_with_heuristic():
    global board, entries
    heuristic_time, heuristic_memory, heuristic_success = measure_performance(heuristic_solve, board)
    
    solved_board = [row[:] for row in board]
    if heuristic_success:
        heuristic_solve(solved_board)
    else:
        messagebox.showerror("Error", "AI Heuristic could not solve the Sudoku.")
        return
    
    messagebox.showinfo("Performance", f"Heuristic: {heuristic_time:.4f}s, {heuristic_memory:.2f}KB")

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
    global board, original_board
    board = generate_board()
    original_board = [row[:] for row in board]
    for i in range(9):
        for j in range(9):
            entries[i][j].config(state='normal')
            entries[i][j].delete(0, tk.END)
            if board[i][j] != 0:
                entries[i][j].insert(0, str(board[i][j]))
                entries[i][j].config(state='disabled')

def create_ui():
    global root, entries, board, difficulty_var, speed_var
    root = tk.Tk()
    root.title("Sudoku Game")

    # Sudoku grid
    board_frame = tk.Frame(root)
    board_frame.grid(row=0, column=0, padx=10, pady=10)
    entries = []
    for i in range(9):
        row_entries = []
        for j in range(9):
            entry = tk.Entry(board_frame, width=3, font=('Arial', 18), justify='center')
            entry.grid(row=i, column=j, padx=2, pady=2)
            row_entries.append(entry)
        entries.append(row_entries)

    # Sidebar
    control_frame = tk.Frame(root)
    control_frame.grid(row=0, column=1, padx=10, pady=10, sticky='n')

    # Difficulty selection
    difficulty_label = tk.Label(control_frame, text="Difficulty")
    difficulty_label.pack(anchor='w')
    difficulty_var = tk.StringVar(value="Medium")
    for level in ["Easy", "Medium", "Hard", "Expert"]:
        tk.Radiobutton(control_frame, text=level, variable=difficulty_var, value=level).pack(anchor='w')
    
    # Animation speed
    speed_label = tk.Label(control_frame, text="Animation Speed")
    speed_label.pack(anchor='w')
    speed_var = tk.DoubleVar(value=0.5)
    speed_slider = ttk.Scale(control_frame, from_=0.1, to=1.0, variable=speed_var, orient='horizontal')
    speed_slider.pack(fill='x')

    # Control buttons
    tk.Button(control_frame, text="New Game",command= new_game, width=20).pack(pady=5)
    tk.Button(control_frame, text="Reset Game",command=reset_game, width=20).pack(pady=5)
    tk.Button(control_frame, text="Check Solution",command=check_solution, width=20).pack(pady=5)
    tk.Button(control_frame, text="Solve with Heuristic",command=solve_with_heuristic, width=20).pack(pady=5)
    tk.Button(control_frame, text="Solve with DFS",command=solve_with_dfs, width=20).pack(pady=5)
    tk.Button(control_frame, text="Stop Solving", command=stop_solving, width=20).pack(pady=5)
    
    # Status bar
    status_label = tk.Label(root, text="New game started.", anchor='w')
    status_label.grid(row=1, column=0, columnspan=2, sticky='we', padx=10, pady=5)
    
    root.mainloop()

create_ui()