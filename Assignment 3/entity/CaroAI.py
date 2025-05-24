import copy
import hashlib
import time
import numpy as np
from functools import lru_cache

# ========================
# CÁC HẰNG SỐ & CẤU HÌNH
# ========================
# Kích thước bàn cờ 15x15
BOARD_SIZE = 15
# Kích thước pixel mỗi ô (dùng cho giao diện đồ họa)
CELL_SIZE = 30
# Các trạng thái ô: trống (0), người chơi (1), AI (2)
EMPTY = 0
PLAYER = 1      # Người chơi
OPPONENT = 2    # AI
# Số quân liên tiếp cần để chiến thắng (5 quân)
WIN_CONDITION = 5

# Điểm số cho các mẫu cờ khác nhau - dùng trong đánh giá bàn cờ
# Mỗi mẫu là một chuỗi 5 ô liên tiếp theo một hướng
# Giá trị điểm càng cao thì mẫu càng nguy hiểm/có lợi
PATTERN_SCORES = {
    (PLAYER, PLAYER, PLAYER, PLAYER, PLAYER): 1000000,    # Người chơi thắng (5 quân liên tiếp)
    (PLAYER, PLAYER, PLAYER, PLAYER, EMPTY): 10000,       # 4 quân liên tiếp với 1 đầu mở
    (EMPTY, PLAYER, PLAYER, PLAYER, PLAYER): 10000,
    (PLAYER, PLAYER, PLAYER, EMPTY, PLAYER): 10000,
    (PLAYER, PLAYER, EMPTY, PLAYER, PLAYER): 10000,
    (PLAYER, EMPTY, PLAYER, PLAYER, PLAYER): 10000,
    (PLAYER, PLAYER, PLAYER, EMPTY, EMPTY): 1000,         # 3 quân liên tiếp với 2 đầu mở
    (EMPTY, EMPTY, PLAYER, PLAYER, PLAYER): 1000,
    (PLAYER, PLAYER, EMPTY, PLAYER, EMPTY): 1000,
    (EMPTY, PLAYER, EMPTY, PLAYER, PLAYER): 1000,
    (PLAYER, EMPTY, PLAYER, PLAYER, EMPTY): 1000,
    (EMPTY, PLAYER, PLAYER, EMPTY, PLAYER): 1000,
    (PLAYER, EMPTY, EMPTY, PLAYER, PLAYER): 1000,
    (PLAYER, PLAYER, EMPTY, EMPTY, PLAYER): 1000,
    (PLAYER, PLAYER, EMPTY, EMPTY, EMPTY): 100,           # 2 quân liên tiếp với nhiều khoảng trống
    (EMPTY, EMPTY, EMPTY, PLAYER, PLAYER): 100,
    (PLAYER, EMPTY, PLAYER, EMPTY, EMPTY): 100,
    (EMPTY, EMPTY, PLAYER, EMPTY, PLAYER): 100,
    (PLAYER, EMPTY, EMPTY, EMPTY, PLAYER): 100,
    (EMPTY, PLAYER, EMPTY, EMPTY, PLAYER): 100,
    (PLAYER, EMPTY, EMPTY, PLAYER, EMPTY): 100,
    (EMPTY, PLAYER, PLAYER, EMPTY, EMPTY): 100,
    (EMPTY, EMPTY, PLAYER, PLAYER, EMPTY): 100,
    (PLAYER, EMPTY, PLAYER, EMPTY, PLAYER): 100,
}

# Tạo bản sao của các mẫu cho đối thủ (AI) bằng cách đảo các giá trị
# PLAYER thành OPPONENT và ngược lại
OPPONENT_PATTERN_SCORES = {}
for pattern, score in PATTERN_SCORES.items():
    # Đảo giá trị PLAYER/OPPONENT trong mẫu
    opponent_pattern = tuple(OPPONENT if p == PLAYER else (EMPTY if p == EMPTY else PLAYER) for p in pattern)
    # Điểm số của đối thủ được nhân với 0.9 để ưu tiên tấn công hơn phòng thủ
    OPPONENT_PATTERN_SCORES[opponent_pattern] = -score * 0.9

# Kết hợp cả hai bộ mẫu vào một từ điển
PATTERN_SCORES.update(OPPONENT_PATTERN_SCORES)

# Các vector hướng để kiểm tra: ngang, dọc, chéo xuống, chéo lên
DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]

# Bảng chuyển vị lưu trữ kết quả đánh giá đã tính trước để tối ưu hóa
transposition_table = {}

# ========================
# LOGIC TRÒ CHƠI
# ========================
def create_board():
    """Tạo bàn cờ mới với kích thước BOARD_SIZE x BOARD_SIZE"""
    return np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.int8)

def is_within_bounds(x, y):
    """Kiểm tra xem tọa độ (x, y) có nằm trong bàn cờ không"""
    return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE

def check_win(board, player):
    """Kiểm tra xem người chơi đã thắng chưa bằng cách tìm 5 quân liên tiếp"""
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            # Chỉ kiểm tra từ các ô có quân của người chơi
            if board[i][j] != player:
                continue
            
            # Kiểm tra cả 4 hướng từ vị trí hiện tại
            for dx, dy in DIRECTIONS:
                count = 1  # Bắt đầu với 1 cho vị trí hiện tại
                
                # Kiểm tra theo hướng
                for k in range(1, WIN_CONDITION):
                    x, y = i + dx * k, j + dy * k
                    if not is_within_bounds(x, y) or board[x][y] != player:
                        break
                    count += 1
                
                if count == WIN_CONDITION:
                    return True
    
    return False

def board_hash(board):
    """Tạo một giá trị hash duy nhất cho trạng thái bàn cờ để lưu vào bảng transposition"""
    return hashlib.md5(board.tobytes()).hexdigest()

def get_pattern(board, start_x, start_y, dx, dy, length=5):
    """Trích xuất một mẫu với độ dài xác định, bắt đầu từ (start_x, start_y) theo hướng (dx, dy)"""
    pattern = []
    for i in range(length):
        x, y = start_x + i * dx, start_y + i * dy
        if not is_within_bounds(x, y):
            return None  # Mẫu nằm ngoài bàn cờ
        pattern.append(board[x][y])
    return tuple(pattern)

def evaluate_board(board):
    """Đánh giá trạng thái bàn cờ bằng cách so khớp các mẫu"""
    # Tạo hash của bàn cờ để kiểm tra trong bảng transposition
    key = board_hash(board)
    if key in transposition_table:
        return transposition_table[key]  # Trả về giá trị đã tính trước nếu có
    
    score = 0
    
    # Kiểm tra tất cả các mẫu 5 ô có thể có trên bàn cờ
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            for dx, dy in DIRECTIONS:
                pattern = get_pattern(board, i, j, dx, dy)
                if pattern is not None and pattern in PATTERN_SCORES:
                    score += PATTERN_SCORES[pattern]
    
    # Lưu kết quả vào bảng transposition để sử dụng lại sau này
    transposition_table[key] = score
    return score

def get_available_moves(board):
    """Lấy danh sách các nước đi khả dụng, ưu tiên các ô gần quân cờ đã đặt"""
    moves = set()
    has_pieces = False
    
    # Lần kiểm tra đầu: tìm các ô kề với quân cờ đã có
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] != 0:
                has_pieces = True
                # Kiểm tra các ô lân cận (trong phạm vi 2 ô)
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        ni, nj = i + dx, j + dy
                        if is_within_bounds(ni, nj) and board[ni][nj] == 0:
                            moves.add((ni, nj))
    
    # Nếu bàn cờ trống, đề xuất ô trung tâm
    if not has_pieces:
        center = BOARD_SIZE // 2
        return [(center, center)]
    
    # Nếu không tìm thấy nước đi hợp lệ (hiếm khi xảy ra), trả về tất cả các ô trống
    if not moves:
        return [(i, j) for i in range(BOARD_SIZE) for j in range(BOARD_SIZE) if board[i][j] == 0]
    
    return list(moves)

def score_move(board, move, player):
    """Đánh giá nhanh một nước đi tiềm năng mà không cần thuật toán minimax đầy đủ"""
    x, y = move
    board[x][y] = player  # Thử nước đi
    score = evaluate_board(board)  # Đánh giá trạng thái
    board[x][y] = 0  # Hoàn tác nước đi
    return score

def alpha_beta_pruning(board, depth, alpha, beta, maximizing_player, last_move=None):
    """Thuật toán minimax kết hợp cắt tỉa alpha-beta để tìm nước đi tốt nhất"""
    # Kiểm tra trạng thái kết thúc hoặc đã đạt độ sâu tối đa
    if depth == 0:
        return evaluate_board(board), None
    
    # Lấy danh sách các nước đi khả dụng và sắp xếp chúng để cắt tỉa tốt hơn
    moves = get_available_moves(board)
    if not moves:
        return 0, None  # Hòa - không còn nước đi nào
    
    # Sắp xếp nước đi theo đánh giá nhanh để cải thiện hiệu quả cắt tỉa
    player = PLAYER if maximizing_player else OPPONENT
    moves.sort(key=lambda move: score_move(board, move, player), reverse=maximizing_player)
    
    best_move = moves[0]  # Mặc định là nước đi đầu tiên
    
    if maximizing_player:
        # Lượt của người chơi tối đa hóa điểm số
        best_score = float('-inf')
        for move in moves:
            x, y = move
            board[x][y] = PLAYER
            
            # Kiểm tra thắng ngay lập tức
            if check_win(board, PLAYER):
                board[x][y] = 0  # Hoàn tác
                return 1000000, move
            
            # Đệ quy với độ sâu giảm dần và đổi lượt
            score, _ = alpha_beta_pruning(board, depth - 1, alpha, beta, False, move)
            board[x][y] = 0  # Hoàn tác nước đi
            
            # Cập nhật điểm số và nước đi tốt nhất
            if score > best_score:
                best_score = score
                best_move = move
            
            # Cập nhật alpha và kiểm tra cắt tỉa beta
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break  # Cắt tỉa beta
                
        return best_score, best_move
    else:
        # Lượt của đối thủ tối thiểu hóa điểm số
        best_score = float('inf')
        for move in moves:
            x, y = move
            board[x][y] = OPPONENT
            
            # Kiểm tra thắng ngay lập tức
            if check_win(board, OPPONENT):
                board[x][y] = 0  # Hoàn tác
                return -1000000, move
            
            # Đệ quy với độ sâu giảm dần và đổi lượt
            score, _ = alpha_beta_pruning(board, depth - 1, alpha, beta, True, move)
            board[x][y] = 0  # Hoàn tác nước đi
            
            # Cập nhật điểm số và nước đi tốt nhất
            if score < best_score:
                best_score = score
                best_move = move
            
            # Cập nhật beta và kiểm tra cắt tỉa alpha
            beta = min(beta, best_score)
            if beta <= alpha:
                break  # Cắt tỉa alpha
                
        return best_score, best_move

def find_best_move(board):
    """Tìm nước đi tốt nhất cho AI sử dụng kỹ thuật đào sâu lặp"""
    # Chuyển đổi sang mảng numpy nếu chưa phải
    if not isinstance(board, np.ndarray):
        board = np.array(board, dtype=np.int8)
    
    # Xóa bảng transposition để tránh vấn đề bộ nhớ
    transposition_table.clear()
    
    # Đếm số ô trống để xác định giai đoạn trò chơi
    empty_count = np.sum(board == 0)
    
    # Điều chỉnh độ sâu tìm kiếm dựa trên giai đoạn trò chơi
    if empty_count > 200:  # Giai đoạn đầu game
        depth = 2
    elif empty_count > 150:  # Giai đoạn giữa game
        depth = 3
    else:  # Giai đoạn cuối game
        depth = 4
    
    start_time = time.time()
    
    # Lấy danh sách các nước đi khả dụng
    immediate_moves = get_available_moves(board)
    
    # Đầu tiên kiểm tra xem AI có thể thắng trong một nước đi không
    for move in immediate_moves:
        x, y = move
        board[x][y] = OPPONENT  # AI là OPPONENT (giá trị 2)
        if check_win(board, OPPONENT):
            board[x][y] = 0  # Hoàn tác
            print(f"AI tìm thấy nước đi chiến thắng trong {time.time() - start_time:.3f} giây")
            return move
        board[x][y] = 0  # Hoàn tác
    
    # Sau đó kiểm tra xem cần chặn nước thắng của đối thủ không
    for move in immediate_moves:
        x, y = move
        board[x][y] = PLAYER  # Người chơi là PLAYER (giá trị 1)
        if check_win(board, PLAYER):
            board[x][y] = 0  # Hoàn tác
            print(f"AI chặn nước thắng trong {time.time() - start_time:.3f} giây")
            return move
        board[x][y] = 0  # Hoàn tác
    
    # Nếu không có nước thắng/chặn ngay lập tức, sử dụng đào sâu lặp
    best_move = None
    for current_depth in range(1, depth + 1):
        try:
            # Thực hiện tìm kiếm với độ sâu tăng dần
            _, move = alpha_beta_pruning(board, current_depth, float('-inf'), float('inf'), True)
            best_move = move
            
            # Kiểm tra nếu đang hết thời gian
            if time.time() - start_time > 2.5:  # Dừng nếu gần đến 3 giây
                break
        except Exception as e:
            print(f"Lỗi ở độ sâu {current_depth}: {e}")
            if best_move is not None:
                break
    
    print(f"AI tính toán nước đi trong {time.time() - start_time:.3f} giây ở độ sâu {current_depth}")
    return best_move