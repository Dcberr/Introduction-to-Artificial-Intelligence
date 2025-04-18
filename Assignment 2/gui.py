import tkinter as tk
from tkinter import messagebox, Button, Frame, Label, PhotoImage
import time
from logic import create_board, find_best_move, check_win, PLAYER, OPPONENT, EMPTY
import os
from PIL import Image, ImageTk

# Các thông số giao diện
CELL_SIZE = 30  # Tăng kích thước ô 
BOARD_SIZE = 15
BOARD_COLOR = "#E6C88C"  # Màu vàng gỗ cho bàn cờ
GRID_COLOR = "#8B4513"   # Màu nâu đậm cho đường kẻ
PLAYER_COLOR = "#000000" # Màu đen cho người chơi
OPPONENT_COLOR = "#D62828" # Màu đỏ cho máy
BG_COLOR = "#F8F9FA"     # Màu nền xám nhạt

class CaroGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Cờ Caro - Gomoku Game")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_COLOR)
        
        # Thêm icon cho ứng dụng (nếu có)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Khởi tạo game
        self.board = create_board()
        self.game_over = False
        self.player_turn = True
        self.move_count = 0
        self.last_move = None
        self.history = []  # Lưu lịch sử các nước đi
        
        # Khung chính
        main_frame = Frame(root, bg=BG_COLOR)
        main_frame.pack(padx=25, pady=20)
        
        # Tiêu đề game
        title_frame = Frame(main_frame, bg=BG_COLOR)
        title_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        title_label = Label(title_frame, text="Cờ Caro - Gomoku", 
                          font=("Helvetica", 20, "bold"), bg=BG_COLOR, fg="#2C3E50")
        title_label.pack()
        
        subtitle_label = Label(title_frame, text="Người chơi vs Máy", 
                              font=("Helvetica", 12), bg=BG_COLOR, fg="#34495E")
        subtitle_label.pack()
        
        # Khung thông tin
        info_frame = Frame(main_frame, bg=BG_COLOR, bd=2, relief=tk.GROOVE)
        info_frame.pack(side=tk.TOP, fill=tk.X, pady=10, padx=10)
        
        # Hiển thị lượt chơi
        turn_frame = Frame(info_frame, bg=BG_COLOR, pady=8, padx=15)
        turn_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        turn_title = Label(turn_frame, text="LƯỢT:", font=("Helvetica", 11), bg=BG_COLOR, fg="#7D3C98")
        turn_title.pack(anchor="w")
        
        self.turn_label = Label(turn_frame, text="Người chơi (X)", 
                             font=("Helvetica", 13, "bold"), bg=BG_COLOR, fg="#2C3E50")
        self.turn_label.pack(anchor="w")
        
        # Hiển thị số nước đi
        move_frame = Frame(info_frame, bg=BG_COLOR, pady=8)
        move_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20)
        
        move_title = Label(move_frame, text="SỐ NƯỚC:", font=("Helvetica", 11), bg=BG_COLOR, fg="#7D3C98")
        move_title.pack(anchor="w")
        
        self.move_count_label = Label(move_frame, text="0", 
                                  font=("Helvetica", 13, "bold"), bg=BG_COLOR, fg="#2C3E50")
        self.move_count_label.pack(anchor="w")
        
        # Hiển thị thời gian suy nghĩ
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
        
        # Canvas cho bàn cờ
        canvas_width = BOARD_SIZE * CELL_SIZE
        canvas_height = BOARD_SIZE * CELL_SIZE
        self.canvas = tk.Canvas(board_frame, width=canvas_width, height=canvas_height, 
                              bg=BOARD_COLOR, highlightthickness=0)
        self.canvas.pack()
        
        # Vẽ lưới bàn cờ
        self.draw_grid()
        
        # Bắt sự kiện click chuột
        self.canvas.bind("<Button-1>", self.on_click)
        
        # Khung trạng thái
        status_frame = Frame(main_frame, bg=BG_COLOR, pady=5)
        status_frame.pack(fill=tk.X)
        
        self.status_label = Label(status_frame, text="Mời bạn đi trước!", 
                               font=("Helvetica", 12, "italic"), bg=BG_COLOR, fg="#16A085")
        self.status_label.pack(pady=5)
        
        # Khung nút điều khiển
        control_frame = Frame(main_frame, bg=BG_COLOR)
        control_frame.pack(pady=10)
        
        self.new_game_btn = Button(control_frame, text="Ván mới", 
                                font=("Helvetica", 12, "bold"), bg="#27AE60", fg="white",
                                command=self.new_game, padx=25, pady=6, 
                                activebackground="#2ECC71", activeforeground="white",
                                relief=tk.RAISED, bd=2)
        self.new_game_btn.pack(side=tk.LEFT, padx=15)
        
        self.undo_btn = Button(control_frame, text="Đi lại", 
                             font=("Helvetica", 12, "bold"), bg="#3498DB", fg="white",
                             command=self.undo_move, padx=25, pady=6,
                             activebackground="#2980B9", activeforeground="white",
                             relief=tk.RAISED, bd=2)
        self.undo_btn.pack(side=tk.LEFT, padx=15)
        
        self.quit_btn = Button(control_frame, text="Thoát", 
                             font=("Helvetica", 12, "bold"), bg="#E74C3C", fg="white",
                             command=self.quit_game, padx=25, pady=6,
                             activebackground="#C0392B", activeforeground="white",
                             relief=tk.RAISED, bd=2)
        self.quit_btn.pack(side=tk.LEFT, padx=15)
        
        # Thêm hover effect cho các button
        self.add_button_hover_effect(self.new_game_btn, "#2ECC71", "#27AE60")
        self.add_button_hover_effect(self.undo_btn, "#2980B9", "#3498DB")
        self.add_button_hover_effect(self.quit_btn, "#C0392B", "#E74C3C")
        
        # Lưu trạng thái bàn cờ trước đó để undo
        self.previous_board = None
    
    def add_button_hover_effect(self, button, hover_color, normal_color):
        """Thêm hiệu ứng hover cho button"""
        button.bind("<Enter>", lambda e: button.config(bg=hover_color))
        button.bind("<Leave>", lambda e: button.config(bg=normal_color))
    
    def draw_grid(self):
        """Vẽ lưới bàn cờ"""
        # Vẽ các đường ngang
        for i in range(BOARD_SIZE + 1):
            y = i * CELL_SIZE
            self.canvas.create_line(0, y, BOARD_SIZE * CELL_SIZE, y, fill=GRID_COLOR, width=1)
        
        # Vẽ các đường dọc
        for i in range(BOARD_SIZE + 1):
            x = i * CELL_SIZE
            self.canvas.create_line(x, 0, x, BOARD_SIZE * CELL_SIZE, fill=GRID_COLOR, width=1)
        
        # Đánh dấu các điểm mốc (hoshis)
        hoshi_points = [3, 7, 11]
        for i in hoshi_points:
            for j in hoshi_points:
                x = j * CELL_SIZE
                y = i * CELL_SIZE
                self.canvas.create_oval(x-4, y-4, x+4, y+4, fill=GRID_COLOR)
    
    def draw_board(self):
        """Vẽ lại bàn cờ với các quân cờ hiện tại"""
        # Xóa tất cả các quân cờ
        self.canvas.delete("piece")
        self.canvas.delete("last_move")
        
        # Vẽ tất cả các quân cờ
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                x = j * CELL_SIZE + CELL_SIZE // 2
                y = i * CELL_SIZE + CELL_SIZE // 2
                
                if self.board[i][j] == PLAYER:
                    # Vẽ quân X cho người chơi
                    size = CELL_SIZE // 3
                    self.canvas.create_line(x-size, y-size, x+size, y+size, 
                                          fill=PLAYER_COLOR, width=3, tags="piece")
                    self.canvas.create_line(x-size, y+size, x+size, y-size, 
                                          fill=PLAYER_COLOR, width=3, tags="piece")
                    
                elif self.board[i][j] == OPPONENT:
                    # Vẽ quân O cho máy
                    size = CELL_SIZE // 3
                    self.canvas.create_oval(x-size, y-size, x+size, y+size, 
                                          outline=OPPONENT_COLOR, width=3, tags="piece")
        
        # Đánh dấu nước đi cuối cùng
        if self.last_move:
            i, j = self.last_move
            x = j * CELL_SIZE + CELL_SIZE // 2
            y = i * CELL_SIZE + CELL_SIZE // 2
            
            # Đánh dấu nước đi cuối với hình vuông xanh lá nổi bật
            self.canvas.create_rectangle(x-CELL_SIZE//4, y-CELL_SIZE//4, 
                                       x+CELL_SIZE//4, y+CELL_SIZE//4, 
                                       outline="#2ECC71", width=2, tags="last_move")
        
        # Cập nhật số nước đi
        self.move_count_label.config(text=str(self.move_count))
    
    def on_click(self, event):
        """Xử lý sự kiện khi người chơi click vào bàn cờ"""
        if self.game_over or not self.player_turn:
            return
        
        # Xác định ô được click
        row = event.y // CELL_SIZE
        col = event.x // CELL_SIZE
        
        # Kiểm tra nước đi hợp lệ
        if not self.is_within_bounds(row, col) or self.board[row][col] != EMPTY:
            return
        
        # Lưu trạng thái hiện tại để undo
        self.previous_board = [row[:] for row in self.board]  # Sao chép sâu
        self.history.append((row, col, PLAYER))  # Lưu lịch sử nước đi
        
        # Đánh dấu nước đi của người chơi
        self.board[row][col] = PLAYER
        self.last_move = (row, col)
        self.move_count += 1
        
        # Cập nhật giao diện
        self.draw_board()
        
        # Kiểm tra thắng/thua
        if check_win(self.board, PLAYER):
            self.show_result("Bạn đã thắng! Chúc mừng! 🎉", "win")
            return
        
        # Kiểm tra hòa
        if self.is_board_full():
            self.show_result("Ván đấu hòa! Cả hai đều xuất sắc! 👏", "draw")
            return
        
        # Chuyển lượt cho máy
        self.player_turn = False
        self.turn_label.config(text="Máy (O)", fg="#D62828")
        self.status_label.config(text="Máy đang suy nghĩ...", fg="#E67E22")
        self.root.update()
        
        # Cho máy đi sau một khoảng thời gian ngắn
        self.root.after(300, self.agent_move)
    
    def agent_move(self):
        """Xử lý nước đi của máy"""
        if self.game_over:
            return
        
        # Ghi nhận thời gian bắt đầu
        start_time = time.time()
        
        # Tìm nước đi tốt nhất cho máy
        move = find_best_move(self.board)
        
        # Ghi nhận thời gian kết thúc
        elapsed_time = time.time() - start_time
        self.time_label.config(text=f"{elapsed_time:.3f}s")
        
        if move:
            row, col = move
            self.board[row][col] = OPPONENT
            self.last_move = (row, col)
            self.move_count += 1
            self.history.append((row, col, OPPONENT))  # Lưu lịch sử nước đi
            
            # Cập nhật giao diện
            self.draw_board()
            
            # Kiểm tra thắng/thua
            if check_win(self.board, OPPONENT):
                self.show_result("Máy đã thắng! Hãy cố gắng lần sau! 🤖", "lose")
                return
            
            # Kiểm tra hòa
            if self.is_board_full():
                self.show_result("Ván đấu hòa! Cả hai đều xuất sắc! 👏", "draw")
                return
        
        # Chuyển lượt về người chơi
        self.player_turn = True
        self.turn_label.config(text="Người chơi (X)", fg="#2C3E50")
        self.status_label.config(text="Đến lượt bạn!", fg="#16A085")
    
    def show_result(self, text, result_type):
        """Hiển thị kết quả trận đấu"""
        self.game_over = True
        
        # Đặt màu sắc cho các loại kết quả khác nhau
        if result_type == "win":
            color = "#27AE60"  # Xanh lá
            bg_color = "#E8F8F5"
        elif result_type == "lose":
            color = "#C0392B"  # Đỏ
            bg_color = "#FDEDEC"
        else:  # draw
            color = "#D35400"  # Cam
            bg_color = "#FEF5E7"
        
        self.status_label.config(text=text, font=("Helvetica", 14, "bold"), fg=color)
        
        # Hiệu ứng đổi màu sau khi kết thúc
        self.canvas.config(bg=bg_color)
        self.root.update()
        
        # Hiển thị hộp thoại thông báo
        messagebox.showinfo("Kết thúc trận đấu", text)
    
    def new_game(self):
        """Bắt đầu ván mới"""
        self.board = create_board()
        self.game_over = False
        self.player_turn = True
        self.move_count = 0
        self.last_move = None
        self.previous_board = None
        self.history = []
        
        # Cập nhật giao diện
        self.canvas.config(bg=BOARD_COLOR)
        self.draw_board()
        self.turn_label.config(text="Người chơi (X)", fg="#2C3E50")
        self.status_label.config(text="Mời bạn đi trước!", font=("Helvetica", 12, "italic"), fg="#16A085")
        self.time_label.config(text="0.000s")
        self.move_count_label.config(text="0")
    
    def undo_move(self):
        """Quay lại nước đi trước đó"""
        if len(self.history) < 2 or self.game_over:
            messagebox.showinfo("Thông báo", "Không thể đi lại!")
            return
        
        # Xóa 2 nước đi cuối cùng (người chơi và máy)
        self.history.pop()  # Xóa nước đi của máy
        self.history.pop()  # Xóa nước đi của người chơi
        
        # Khôi phục bàn cờ từ lịch sử
        self.board = create_board()
        for move in self.history:
            row, col, player = move
            self.board[row][col] = player
        
        # Cập nhật thông tin
        self.move_count = len(self.history)
        
        # Cập nhật nước đi cuối cùng
        if self.history:
            self.last_move = (self.history[-1][0], self.history[-1][1])
        else:
            self.last_move = None
        
        # Cập nhật giao diện
        self.draw_board()
        self.player_turn = True
        self.turn_label.config(text="Người chơi (X)", fg="#2C3E50")
        self.status_label.config(text="Đến lượt bạn!", fg="#16A085")
    
    def is_within_bounds(self, x, y):
        """Kiểm tra tọa độ nằm trong bàn cờ"""
        return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE
    
    def is_board_full(self):
        """Kiểm tra bàn cờ đã đầy chưa"""
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if self.board[i][j] == EMPTY:
                    return False
        return True
    
    def quit_game(self):
        """Thoát game"""
        if messagebox.askyesno("Xác nhận thoát", "Bạn có chắc muốn thoát game?"):
            self.root.destroy()

# ========================
# MAIN
# ========================
if __name__ == "__main__":
    root = tk.Tk()
    app = CaroGUI(root)
    root.mainloop()