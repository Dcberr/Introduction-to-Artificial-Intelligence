import tkinter as tk
from tkinter import messagebox, Button, Frame, Label, OptionMenu, StringVar, Radiobutton
import time
import numpy as np
import random
from CaroAI import (
    create_board, find_best_move, check_win, evaluate_board, get_pattern,
    PLAYER, OPPONENT, EMPTY, BOARD_SIZE, PATTERN_SCORES, DIRECTIONS
)

# Định nghĩa các màu sắc
Black = "#000000"
White = "#FFFFFF"
CELL_SIZE = 20
BOARD_COLOR = "#E6C88C"  # Màu vàng gỗ cho bàn cờ
GRID_COLOR = "#8B4513"   # Màu nâu đậm cho đường kẻ
BG_COLOR = "#F8F9FA"     # Màu nền xám nhạt
AI_COLOR = Black     # Màu đen cho AI thông minh
RANDOM_COLOR = "#D62828" # Màu đỏ cho AI ngẫu nhiên
DELAY = 500              # Độ trễ giữa các nước đi (miligiây)

class RandomAgent:
    """Agent ngẫu nhiên với 3 cấp độ chơi: Thấp, Trung bình, Cao"""
    def __init__(self, level="Low"):
        self.level = level.capitalize()
        self.name = f"Random Agent ({self.level})"
        self.move_stats = {
            "blocks": 0,  # Số lần chặn thắng đối thủ
            "opportunities": 0,  # Số lần tạo cơ hội thắng
            "total_moves": 0  # Tổng số nước đi
        }
    
    def get_available_moves(self, board):
        """Lấy danh sách các nước đi khả dụng, ưu tiên các ô gần quân cờ đã đặt"""
        moves = set()
        has_pieces = False
        
        # Tạo danh sách vị trí xung quanh - phạm vi thu hẹp dần theo cấp độ
        proximity_range = 3 if self.level == "Low" else (2 if self.level == "Medium" else 1)
        
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if board[i][j] != 0:
                    has_pieces = True
                    # Tìm các ô xung quanh với phạm vi tùy theo cấp độ
                    for dx in range(-proximity_range, proximity_range + 1):
                        for dy in range(-proximity_range, proximity_range + 1):
                            ni, nj = i + dx, j + dy
                            if 0 <= ni < BOARD_SIZE and 0 <= nj < BOARD_SIZE and board[ni][nj] == 0:
                                moves.add((ni, nj))
        
        # Nếu bàn cờ trống, cấp độ Low chọn random, cấp độ Medium và High chọn trung tâm
        if not has_pieces:
            center = BOARD_SIZE // 2
            if self.level == "Low":
                # Cấp thấp: chọn bất kỳ ô nào trong vùng trung tâm mở rộng
                radius = 3
                return [(center + dx, center + dy) 
                        for dx in range(-radius, radius + 1) 
                        for dy in range(-radius, radius + 1)
                        if 0 <= center + dx < BOARD_SIZE and 0 <= center + dy < BOARD_SIZE]
            else:
                # Cấp trung và cao: chọn ô trung tâm hoặc gần trung tâm
                return [(center, center)]
        
        if not moves:
            return [(i, j) for i in range(BOARD_SIZE) for j in range(BOARD_SIZE) if board[i][j] == 0]
        
        return list(moves)
    
    def score_move(self, board, move, player):
        """Đánh giá nước đi dựa trên mẫu và kiểm tra thắng/chặn"""
        x, y = move
        score = 0
        
        # Hệ số chiến thuật - khác nhau tùy theo cấp độ
        win_bonus = 1000000
        block_bonus = 50000 if self.level == "Low" else 500000 if self.level == "Medium" else 900000
        pattern_weight = 0.3 if self.level == "Low" else 0.7 if self.level == "Medium" else 1.0
        
        # Kiểm tra thắng ngay lập tức
        board[x][y] = player
        if check_win(board, player):
            score += win_bonus
            self.move_stats["opportunities"] += 1
        board[x][y] = 0
        
        # Kiểm tra chặn đối thủ - không quan trọng ở cấp thấp, rất quan trọng ở cấp cao
        opponent = PLAYER if player == OPPONENT else OPPONENT
        board[x][y] = opponent
        if check_win(board, opponent):
            score += block_bonus
            self.move_stats["blocks"] += 1
        board[x][y] = 0
        
        # Đánh giá dựa trên mẫu - ảnh hưởng tùy theo cấp độ
        board[x][y] = player
        pattern_score = 0
        for dx, dy in DIRECTIONS:
            for offset in range(-4, 1):
                pattern = get_pattern(board, x + offset * dx, y + offset * dy, dx, dy)
                if pattern and pattern in PATTERN_SCORES:
                    pattern_score += PATTERN_SCORES[pattern]
        board[x][y] = 0
        
        # Thêm điểm cho mẫu, nhưng tỷ trọng khác nhau theo cấp độ
        score += pattern_score * pattern_weight
        
        # Thêm một chút ngẫu nhiên - cấp thấp nhiều ngẫu nhiên, cấp cao ít ngẫu nhiên
        random_factor = 5000 if self.level == "Low" else 1000 if self.level == "Medium" else 100
        score += random.randint(0, random_factor)
        
        # Cấp độ cao ưu tiên vị trí trung tâm hơn
        if self.level == "High":
            center = BOARD_SIZE // 2
            distance_to_center = abs(x - center) + abs(y - center)
            center_bonus = max(0, (BOARD_SIZE - distance_to_center) * 50)
            score += center_bonus
        
        return score
    
    def find_best_move(self, board):
        """Chọn nước đi dựa trên cấp độ của agent"""
        moves = self.get_available_moves(board)
        if not moves:
            return None
        
        self.move_stats["total_moves"] += 1
        
        if self.level == "Low":
            # Cấp độ thấp: chủ yếu ngẫu nhiên, nhưng đôi khi xem xét điểm số
            # 70% thời gian chọn hoàn toàn ngẫu nhiên
            if random.random() < 0.7:
                return random.choice(moves)
            
            # 30% thời gian chọn từ top 8 nước đi được đánh giá
            scored_moves = [(self.score_move(board, move, OPPONENT), move) for move in moves]
            scored_moves.sort(reverse=True)
            top_moves = [move for score, move in scored_moves[:8]]
            return random.choice(top_moves) if top_moves else random.choice(moves)
            
        elif self.level == "Medium":
            # Cấp độ trung bình: chọn từ top 5 nước đi, nhưng vẫn có một số yếu tố ngẫu nhiên
            scored_moves = [(self.score_move(board, move, OPPONENT), move) for move in moves]
            scored_moves.sort(reverse=True)
            
            # Nếu có nước thắng ngay lập tức, 80% khả năng sẽ chọn nó
            if scored_moves[0][0] >= 900000 and random.random() < 0.8:
                return scored_moves[0][1]
                
            # Chọn ngẫu nhiên từ 5 nước đi tốt nhất
            top_moves = [move for score, move in scored_moves[:5]]
            return random.choice(top_moves) if top_moves else random.choice(moves)
            
        else:  # Cấp độ cao: thông minh nhất, gần như luôn chọn nước tốt nhất
            scored_moves = [(self.score_move(board, move, OPPONENT), move) for move in moves]
            scored_moves.sort(reverse=True)
            
            # Nếu có nước thắng hoặc chặn, luôn chọn nó
            if scored_moves[0][0] >= 500000:
                return scored_moves[0][1]
                
            # 80% thời gian chọn nước đi tốt nhất
            if random.random() < 0.8:
                return scored_moves[0][1]
                
            # 20% thời gian chọn từ top 3 nước đi tốt nhất
            top_moves = [move for score, move in scored_moves[:3]]
            return random.choice(top_moves) if top_moves else random.choice(moves)

class SmartAgent:
    """Đại diện cho AI thông minh sử dụng thuật toán minimax"""
    def __init__(self):
        self.name = "Smart AI"
        self.move_stats = {
            "blocks": 0,
            "opportunities": 0,
            "total_moves": 0
        }
    
    def find_best_move(self, board):
        """Sử dụng thuật toán AI của bạn"""
        self.move_stats["total_moves"] += 1
        move = find_best_move(board)
        if move:
            x, y = move
            board[x][y] = PLAYER
            if check_win(board, PLAYER):
                self.move_stats["opportunities"] += 1
            board[x][y] = OPPONENT
            if check_win(board, OPPONENT):
                self.move_stats["blocks"] += 1
            board[x][y] = 0
        return move

class AIvsRandomGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI vs Random - Trận đấu tự động")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_COLOR)
        
        # Khởi tạo game
        self.board = create_board()
        self.game_over = False
        self.smart_turn = True  # Mặc định Smart AI đi trước
        self.is_running = False  # Trạng thái vòng lặp trò chơi
        self.move_count = 0
        self.last_move = None
        self.history = []
        
        # Khởi tạo agents
        self.random_level = "Low"
        self.first_mover = "Smart"  # Mặc định Smart AI đi trước
        self.smart_agent = SmartAgent()
        self.random_agent = RandomAgent(self.random_level)
        
        # Thiết lập giao diện
        self.setup_ui()
        
        # Lưu thống kê
        self.stats = {
            "smart_wins": 0,
            "random_wins": 0,
            "draws": 0,
            "games": 0,
            "smart_avg_time": 0.0,
            "random_avg_time": 0.0,
            "smart_move_stats": {"blocks": 0, "opportunities": 0, "total": 0},
            "random_move_stats": {"blocks": 0, "opportunities": 0, "total": 0}
        }
        self.game_times = {"smart": [], "random": []}
    
    def setup_ui(self):
        """Thiết lập giao diện người dùng"""
        main_frame = Frame(self.root, bg=BG_COLOR)
        main_frame.pack(padx=25, pady=20)
        
        # Tiêu đề
        title_frame = Frame(main_frame, bg=BG_COLOR)
        title_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        title_label = Label(title_frame, text="AI vs Random - Gomoku", 
                          font=("Helvetica", 20, "bold"), bg=BG_COLOR, fg="#2C3E50")
        title_label.pack()
        
        subtitle_label = Label(title_frame, text="Trận đấu tự động AI", 
                              font=("Helvetica", 12), bg=BG_COLOR, fg="#34495E")
        subtitle_label.pack()
        
        # Chọn cấp độ RandomAgent
        level_frame = Frame(main_frame, bg=BG_COLOR)
        level_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        Label(level_frame, text="Cấp độ Random Agent:", font=("Helvetica", 11), 
             bg=BG_COLOR, fg="#7D3C98").pack(side=tk.LEFT, padx=5)
        self.level_var = StringVar(value=self.random_level)
        level_menu = OptionMenu(level_frame, self.level_var, "Low", "Medium", "High", 
                              command=self.change_random_level)
        level_menu.config(font=("Helvetica", 11), bg=BG_COLOR, fg="#2C3E50")
        level_menu.pack(side=tk.LEFT, padx=5)
        
        # Chọn bên đi trước
        first_mover_frame = Frame(main_frame, bg=BG_COLOR)
        first_mover_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        Label(first_mover_frame, text="Bên đi trước:", font=("Helvetica", 11), 
             bg=BG_COLOR, fg="#7D3C98").pack(side=tk.LEFT, padx=5)
        self.first_mover_var = StringVar(value=self.first_mover)
        Radiobutton(first_mover_frame, text="Smart AI", variable=self.first_mover_var, value="Smart",
                   font=("Helvetica", 11), bg=BG_COLOR, fg="#2C3E50", 
                   command=self.change_first_mover).pack(side=tk.LEFT, padx=5)
        Radiobutton(first_mover_frame, text="Random Agent", variable=self.first_mover_var, value="Random",
                   font=("Helvetica", 11), bg=BG_COLOR, fg="#2C3E50", 
                   command=self.change_first_mover).pack(side=tk.LEFT, padx=5)
        
        # Khung thông tin
        info_frame = Frame(main_frame, bg=BG_COLOR, bd=2, relief=tk.GROOVE)
        info_frame.pack(side=tk.TOP, fill=tk.X, pady=10, padx=10)
        
        turn_frame = Frame(info_frame, bg=BG_COLOR, pady=8, padx=15)
        turn_frame.pack(side=tk.LEFT, fill=tk.Y)
        turn_title = Label(turn_frame, text="LƯỢT:", font=("Helvetica", 11), bg=BG_COLOR, fg="#7D3C98")
        turn_title.pack(anchor="w")
        self.turn_label = Label(turn_frame, text="Smart AI (X)", 
                             font=("Helvetica", 13, "bold"), bg=BG_COLOR, fg="#2C3E50")
        self.turn_label.pack(anchor="w")
        
        move_frame = Frame(info_frame, bg=BG_COLOR, pady=8)
        move_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20)
        move_title = Label(move_frame, text="SỐ NƯỚC:", font=("Helvetica", 11), bg=BG_COLOR, fg="#7D3C98")
        move_title.pack(anchor="w")
        self.move_count_label = Label(move_frame, text="0", 
                                  font=("Helvetica", 13, "bold"), bg=BG_COLOR, fg="#2C3E50")
        self.move_count_label.pack(anchor="w")
        
        time_frame = Frame(info_frame, bg=BG_COLOR, pady=8)
        time_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=15)
        time_title = Label(time_frame, text="THỜI GIAN SUY NGHĨ:", font=("Helvetica", 11), bg=BG_COLOR, fg="#7D3C98")
        time_title.pack(anchor="e")
        self.time_label = Label(time_frame, text="0.000s", 
                             font=("Helvetica", 13, "bold"), bg=BG_COLOR, fg="#2C3E50")
        self.time_label.pack(anchor="e")
        
        # Khung bàn cờ
        board_frame = Frame(main_frame, bg=GRID_COLOR, bd=2, relief=tk.RAISED)
        board_frame.pack(pady=15)
        
        canvas_width = BOARD_SIZE * CELL_SIZE
        canvas_height = BOARD_SIZE * CELL_SIZE
        self.canvas = tk.Canvas(board_frame, width=canvas_width, height=canvas_height, 
                              bg=BOARD_COLOR, highlightthickness=0)
        self.canvas.pack()
        
        self.draw_grid()
        
        # Khung trạng thái
        status_frame = Frame(main_frame, bg=BG_COLOR, pady=5)
        status_frame.pack(fill=tk.X)
        self.status_label = Label(status_frame, text="Nhấn 'Bắt đầu' để chơi!", 
                               font=("Helvetica", 12, "italic"), bg=BG_COLOR, fg="#16A085")
        self.status_label.pack(pady=5)
        
        # Khung thống kê
        stats_frame = Frame(main_frame, bg=BG_COLOR, bd=2, relief=tk.GROOVE)
        stats_frame.pack(fill=tk.X, pady=10, padx=10)
        
        Label(stats_frame, text="THỐNG KÊ:", font=("Helvetica", 12, "bold"), 
             bg=BG_COLOR, fg="#7D3C98").pack(anchor="w", padx=15, pady=5)
        
        stats_content = Frame(stats_frame, bg=BG_COLOR)
        stats_content.pack(fill=tk.X, padx=15, pady=5)
        
        games_frame = Frame(stats_content, bg=BG_COLOR)
        games_frame.pack(side=tk.LEFT, padx=15)
        Label(games_frame, text="Tổng số trận:", font=("Helvetica", 11), 
             bg=BG_COLOR, fg="#2C3E50").pack(anchor="w")
        self.games_label = Label(games_frame, text="0", font=("Helvetica", 13, "bold"), 
                               bg=BG_COLOR, fg="#2C3E50")
        self.games_label.pack(anchor="w")
        
        smart_frame = Frame(stats_content, bg=BG_COLOR)
        smart_frame.pack(side=tk.LEFT, padx=15)
        Label(smart_frame, text="Smart AI thắng:", font=("Helvetica", 11), 
             bg=BG_COLOR, fg="#2C3E50").pack(anchor="w")
        self.smart_label = Label(smart_frame, text="0", font=("Helvetica", 13, "bold"), 
                               bg=BG_COLOR, fg="#27AE60")
        self.smart_label.pack(anchor="w")
        
        random_frame = Frame(stats_content, bg=BG_COLOR)
        random_frame.pack(side=tk.LEFT, padx=15)
        Label(random_frame, text="Random Agent thắng:", font=("Helvetica", 11), 
             bg=BG_COLOR, fg="#2C3E50").pack(anchor="w")
        self.random_label = Label(random_frame, text="0", font=("Helvetica", 13, "bold"), 
                                bg=BG_COLOR, fg="#D62828")
        self.random_label.pack(anchor="w")
        
        draw_frame = Frame(stats_content, bg=BG_COLOR)
        draw_frame.pack(side=tk.LEFT, padx=15)
        Label(draw_frame, text="Hòa:", font=("Helvetica", 11), 
             bg=BG_COLOR, fg="#2C3E50").pack(anchor="w")
        self.draw_label = Label(draw_frame, text="0", font=("Helvetica", 13, "bold"), 
                              bg=BG_COLOR, fg="#D35400")
        self.draw_label.pack(anchor="w")
        
        # Khung nút điều khiển
        control_frame = Frame(main_frame, bg=BG_COLOR)
        control_frame.pack(pady=10)
        
        self.start_btn = Button(control_frame, text="Bắt đầu", 
                              font=("Helvetica", 12, "bold"), bg="#3498DB", fg="white",
                              command=self.start_game, padx=25, pady=6, 
                              activebackground="#2980B9", activeforeground="white",
                              relief=tk.RAISED, bd=2)
        self.start_btn.pack(side=tk.LEFT, padx=15)
        
        self.stop_btn = Button(control_frame, text="Dừng lại", 
                             font=("Helvetica", 12, "bold"), bg="#F1C40F", fg="white",
                             command=self.stop_game, padx=25, pady=6,
                             activebackground="#E67E22", activeforeground="white",
                             relief=tk.RAISED, bd=2)
        self.stop_btn.pack(side=tk.LEFT, padx=15)
        
        self.new_game_btn = Button(control_frame, text="Ván mới", 
                                font=("Helvetica", 12, "bold"), bg="#27AE60", fg="white",
                                command=self.new_game, padx=25, pady=6, 
                                activebackground="#2ECC71", activeforeground="white",
                                relief=tk.RAISED, bd=2)
        self.new_game_btn.pack(side=tk.LEFT, padx=15)
        
        self.quit_btn = Button(control_frame, text="Thoát", 
                             font=("Helvetica", 12, "bold"), bg="#E74C3C", fg="white",
                             command=self.quit_game, padx=25, pady=6,
                             activebackground="#C0392B", activeforeground="white",
                             relief=tk.RAISED, bd=2)
        self.quit_btn.pack(side=tk.LEFT, padx=15)
        
        self.add_button_hover_effect(self.start_btn, "#2980B9", "#3498DB")
        self.add_button_hover_effect(self.stop_btn, "#E67E22", "#F1C40F")
        self.add_button_hover_effect(self.new_game_btn, "#2ECC71", "#27AE60")
        self.add_button_hover_effect(self.quit_btn, "#C0392B", "#E74C3C")
    
    def add_button_hover_effect(self, button, hover_color, normal_color):
        """Thêm hiệu ứng hover cho button"""
        button.bind("<Enter>", lambda e: button.config(bg=hover_color))
        button.bind("<Leave>", lambda e: button.config(bg=normal_color))
    
    def change_random_level(self, level):
        """Thay đổi cấp độ của RandomAgent"""
        self.random_level = level
        self.random_agent = RandomAgent(self.random_level)
        if not self.is_running:
            self.new_game()
    
    def change_first_mover(self):
        """Thay đổi bên đi trước"""
        self.first_mover = self.first_mover_var.get()
        self.smart_turn = (self.first_mover == "Smart")
        if not self.is_running:
            self.new_game()
    
    def draw_grid(self):
        """Vẽ lưới bàn cờ"""
        for i in range(BOARD_SIZE + 1):
            y = i * CELL_SIZE
            self.canvas.create_line(0, y, BOARD_SIZE * CELL_SIZE, y, fill=GRID_COLOR, width=1)
        
        for i in range(BOARD_SIZE + 1):
            x = i * CELL_SIZE
            self.canvas.create_line(x, 0, x, BOARD_SIZE * CELL_SIZE, fill=GRID_COLOR, width=1)
        
        hoshi_points = [3, 7, 11]
        for i in hoshi_points:
            for j in hoshi_points:
                x = j * CELL_SIZE
                y = i * CELL_SIZE
                self.canvas.create_oval(x-4, y-4, x+4, y+4, fill=GRID_COLOR)
    
    def draw_board(self):
        """Vẽ lại bàn cờ với các quân cờ hiện tại"""
        self.canvas.delete("piece")
        self.canvas.delete("last_move")
        
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                x = j * CELL_SIZE + CELL_SIZE // 2
                y = i * CELL_SIZE + CELL_SIZE // 2
                
                if self.board[i][j] == PLAYER:  # Smart AI
                    size = CELL_SIZE // 3
                    self.canvas.create_line(x-size, y-size, x+size, y+size, 
                                          fill=AI_COLOR, width=3, tags="piece")
                    self.canvas.create_line(x-size, y+size, x+size, y-size, 
                                          fill=AI_COLOR, width=3, tags="piece")
                    
                elif self.board[i][j] == OPPONENT:  # Random Agent
                    size = CELL_SIZE // 3
                    self.canvas.create_oval(x-size, y-size, x+size, y+size, 
                                          outline=RANDOM_COLOR, width=3, tags="piece")
        
        if self.last_move:
            i, j = self.last_move
            x = j * CELL_SIZE + CELL_SIZE // 2
            y = i * CELL_SIZE + CELL_SIZE // 2
            mark_color = "#27AE60" if self.board[i][j] == PLAYER else "#E74C3C"
            self.canvas.create_rectangle(x-CELL_SIZE//4, y-CELL_SIZE//4, 
                                      x+CELL_SIZE//4, y+CELL_SIZE//4, 
                                      outline=mark_color, width=2, tags="last_move")
        
        self.move_count_label.config(text=str(self.move_count))
    
    def start_game(self):
        """Bắt đầu hoặc tiếp tục vòng lặp trò chơi"""
        if self.game_over or self.is_running:
            return
        self.is_running = True
        self.status_label.config(text="Trận đấu đang diễn ra!", fg="#16A085")
        self.start_game_loop()
    
    def stop_game(self):
        """Tạm dừng trò chơi"""
        self.is_running = False
        self.status_label.config(text="Trận đấu đã tạm dừng! Nhấn 'Bắt đầu' để tiếp tục.", fg="#E67E22")
    
    def start_game_loop(self):
        """Bắt đầu vòng lặp trò chơi tự động giữa hai AI"""
        if not self.is_running or self.game_over:
            return
        
        current_player = self.smart_agent if self.smart_turn else self.random_agent
        player_mark = PLAYER if self.smart_turn else OPPONENT
        color = "#2C3E50" if self.smart_turn else "#D62828"
        
        self.turn_label.config(text=f"{current_player.name} ({'X' if self.smart_turn else 'O'})", fg=color)
        self.status_label.config(text=f"{current_player.name} đang suy nghĩ...", fg="#16A085")
        self.root.update()
        
        self.root.after(DELAY, lambda: self.make_move(current_player, player_mark))
    
    def make_move(self, agent, player_mark):
        """Thực hiện nước đi cho AI"""
        if not self.is_running or self.game_over:
            return
        
        start_time = time.time()
        move = agent.find_best_move(self.board)
        elapsed_time = time.time() - start_time
        
        if move:
            row, col = move
            self.board[row][col] = player_mark
            self.last_move = (row, col)
            self.move_count += 1
            self.history.append((row, col, player_mark))
            
            self.time_label.config(text=f"{elapsed_time:.3f}s")
            self.draw_board()
            
            # Cập nhật thời gian
            key = "smart" if agent == self.smart_agent else "random"
            self.game_times[key].append(elapsed_time)
            
            if check_win(self.board, player_mark):
                winner = "Smart AI" if player_mark == PLAYER else f"Random Agent ({self.random_level})"
                self.show_result(f"{winner} đã thắng! 🏆", winner)
                return
            
            if self.is_board_full():
                self.show_result("Ván đấu hòa! 🤝", "draw")
                return
        
        self.smart_turn = not self.smart_turn
        self.start_game_loop()
    
    def show_result(self, text, result_type):
        """Hiển thị kết quả trận đấu và cập nhật thống kê"""
        self.game_over = True
        self.is_running = False
        
        self.stats["games"] += 1
        if result_type == "Smart AI":
            self.stats["smart_wins"] += 1
            color = "#27AE60"
        elif result_type.startswith("Random Agent"):
            self.stats["random_wins"] += 1
            color = "#C0392B"
        else:
            self.stats["draws"] += 1
            color = "#D35400"
        
        # Cập nhật thống kê nước đi
        for key, stat in [("smart", self.smart_agent.move_stats), ("random", self.random_agent.move_stats)]:
            self.stats[f"{key}_move_stats"]["blocks"] += stat["blocks"]
            self.stats[f"{key}_move_stats"]["opportunities"] += stat["opportunities"]
            self.stats[f"{key}_move_stats"]["total"] += stat["total_moves"]
        
        # Cập nhật giao diện
        self.games_label.config(text=str(self.stats["games"]))
        self.smart_label.config(text=str(self.stats["smart_wins"]))
        self.random_label.config(text=str(self.stats["random_wins"]))
        self.draw_label.config(text=str(self.stats["draws"]))
        
        self.root.after(3000, self.new_game)
    
    def new_game(self):
        """Bắt đầu ván mới"""
        self.board = create_board()
        self.game_over = False
        self.is_running = False
        self.smart_turn = (self.first_mover == "Smart")
        self.move_count = 0
        self.last_move = None
        self.history = []
        self.smart_agent.move_stats = {"blocks": 0, "opportunities": 0, "total_moves": 0}
        self.random_agent.move_stats = {"blocks": 0, "opportunities": 0, "total_moves": 0}
        
        self.canvas.config(bg=BOARD_COLOR)
        self.draw_board()
        self.turn_label.config(text=f"{'Smart AI' if self.smart_turn else self.random_agent.name} ({'X' if self.smart_turn else 'O'})", fg="#2C3E50")
        self.status_label.config(
            text="Nhấn 'Bắt đầu' để chơi!", 
            font=("Helvetica", 12, "italic"), 
            fg="#16A085"
        )
        self.time_label.config(text="0.000s")
        self.move_count_label.config(text="0")
    
    def is_board_full(self):
        """Kiểm tra bàn cờ đã đầy chưa"""
        return not np.any(self.board == EMPTY)
    
    def quit_game(self):
        """Thoát game"""
        if messagebox.askyesno("Xác nhận thoát", "Bạn có chắc muốn thoát?"):
            # In thống kê cuối cùng
            print("\nThống kê cuối cùng:")
            print(f"Tổng số trận: {self.stats['games']}")
            print(f"Smart AI thắng: {self.stats['smart_wins']} ({self.stats['smart_wins']/self.stats['games']*100:.1f}%)" if self.stats['games'] > 0 else "Smart AI thắng: 0 (0.0%)")
            print(f"Random Agent thắng: {self.stats['random_wins']} ({self.stats['random_wins']/self.stats['games']*100:.1f}%)" if self.stats['games'] > 0 else "Random Agent thắng: 0 (0.0%)")
            print(f"Hòa: {self.stats['draws']} ({self.stats['draws']/self.stats['games']*100:.1f}%)" if self.stats['games'] > 0 else "Hòa: 0 (0.0%)")
            print(f"Thời gian suy nghĩ trung bình Smart AI: {np.mean(self.game_times['smart']):.3f}s" if self.game_times['smart'] else "Thời gian suy nghĩ trung bình Smart AI: N/A")
            print(f"Thời gian suy nghĩ trung bình Random Agent: {np.mean(self.game_times['random']):.3f}s" if self.game_times['random'] else "Thời gian suy nghĩ trung bình Random Agent: N/A")
            print(f"Smart AI: Blocks={self.stats['smart_move_stats']['blocks']}, Opportunities={self.stats['smart_move_stats']['opportunities']}")
            print(f"Random Agent: Blocks={self.stats['random_move_stats']['blocks']}, Opportunities={self.stats['random_move_stats']['opportunities']}")
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AIvsRandomGUI(root)
    root.mainloop()