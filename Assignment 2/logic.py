import copy
import hashlib
import time
import numpy as np
from functools import lru_cache

# ========================
# CONSTANTS & CONFIG
# ========================
BOARD_SIZE = 15
CELL_SIZE = 30
EMPTY = 0
PLAYER = 1      # Agent
OPPONENT = 2    # Người chơi
WIN_CONDITION = 5

# Pattern scores for evaluation
PATTERN_SCORES = {
    (PLAYER, PLAYER, PLAYER, PLAYER, PLAYER): 1000000,    # Win
    (PLAYER, PLAYER, PLAYER, PLAYER, EMPTY): 10000,      # Open four
    (EMPTY, PLAYER, PLAYER, PLAYER, PLAYER): 10000,
    (PLAYER, PLAYER, PLAYER, EMPTY, PLAYER): 10000,
    (PLAYER, PLAYER, EMPTY, PLAYER, PLAYER): 10000,
    (PLAYER, EMPTY, PLAYER, PLAYER, PLAYER): 10000,
    (PLAYER, PLAYER, PLAYER, EMPTY, EMPTY): 1000,        # Open three
    (EMPTY, EMPTY, PLAYER, PLAYER, PLAYER): 1000,
    (PLAYER, PLAYER, EMPTY, PLAYER, EMPTY): 1000,
    (EMPTY, PLAYER, EMPTY, PLAYER, PLAYER): 1000,
    (PLAYER, EMPTY, PLAYER, PLAYER, EMPTY): 1000,
    (EMPTY, PLAYER, PLAYER, EMPTY, PLAYER): 1000,
    (PLAYER, EMPTY, EMPTY, PLAYER, PLAYER): 1000,
    (PLAYER, PLAYER, EMPTY, EMPTY, PLAYER): 1000,
    (PLAYER, PLAYER, EMPTY, EMPTY, EMPTY): 100,          # Open two
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

# Mirror the patterns for opponent
OPPONENT_PATTERN_SCORES = {}
for pattern, score in PATTERN_SCORES.items():
    opponent_pattern = tuple(OPPONENT if p == PLAYER else (EMPTY if p == EMPTY else PLAYER) for p in pattern)
    # Opponent patterns are slightly less valuable to prioritize offense
    OPPONENT_PATTERN_SCORES[opponent_pattern] = -score * 0.9

# Combine both pattern sets
PATTERN_SCORES.update(OPPONENT_PATTERN_SCORES)

# Direction vectors
DIRECTIONS = [(0, 1), (1, 0), (1, 1), (1, -1)]

# Cache for transposition table
transposition_table = {}

# ========================
# GAME LOGIC
# ========================
def create_board():
    return np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.int8)

def is_within_bounds(x, y):
    return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE

def check_win(board, player):
    # Check win condition more efficiently
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] != player:
                continue
            
            # Check all 4 directions
            for dx, dy in DIRECTIONS:
                count = 1  # Start with 1 for the current position
                
                # Check forward
                for k in range(1, WIN_CONDITION):
                    x, y = i + dx * k, j + dy * k
                    if not is_within_bounds(x, y) or board[x][y] != player:
                        break
                    count += 1
                
                if count == WIN_CONDITION:
                    return True
    
    return False

def board_hash(board):
    return hashlib.md5(board.tobytes()).hexdigest()

def get_pattern(board, start_x, start_y, dx, dy, length=5):
    """Extract a pattern of specified length starting from (start_x, start_y) in direction (dx, dy)"""
    pattern = []
    for i in range(length):
        x, y = start_x + i * dx, start_y + i * dy
        if not is_within_bounds(x, y):
            return None  # Pattern extends beyond board
        pattern.append(board[x][y])
    return tuple(pattern)

def evaluate_board(board):
    """Evaluate the board position using pattern matching"""
    key = board_hash(board)
    if key in transposition_table:
        return transposition_table[key]
    
    score = 0
    
    # Check all possible 5-in-a-row patterns
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            for dx, dy in DIRECTIONS:
                pattern = get_pattern(board, i, j, dx, dy)
                if pattern is not None and pattern in PATTERN_SCORES:
                    score += PATTERN_SCORES[pattern]
    
    transposition_table[key] = score
    return score

def get_available_moves(board):
    """Get available moves, prioritizing cells adjacent to existing pieces"""
    moves = set()
    has_pieces = False
    
    # First pass: check for moves adjacent to existing pieces
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            if board[i][j] != 0:
                has_pieces = True
                # Check adjacent cells (within 2 spaces)
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        ni, nj = i + dx, j + dy
                        if is_within_bounds(ni, nj) and board[ni][nj] == 0:
                            moves.add((ni, nj))
    
    # If no pieces on board yet, suggest center
    if not has_pieces:
        center = BOARD_SIZE // 2
        return [(center, center)]
    
    # If no valid moves found (very rare), return all empty cells
    if not moves:
        return [(i, j) for i in range(BOARD_SIZE) for j in range(BOARD_SIZE) if board[i][j] == 0]
    
    return list(moves)

def score_move(board, move, player):
    """Quickly score a potential move without full minimax"""
    x, y = move
    board[x][y] = player
    score = evaluate_board(board)
    board[x][y] = 0  # Reset the move
    return score

def alpha_beta_pruning(board, depth, alpha, beta, maximizing_player, last_move=None):
    """Minimax algorithm with alpha-beta pruning"""
    # Check if this is a terminal state or max depth reached
    if depth == 0:
        return evaluate_board(board), None
    
    # Get available moves and sort them for better pruning
    moves = get_available_moves(board)
    if not moves:
        return 0, None  # Draw
    
    # Sort moves by a quick evaluation for better pruning
    player = PLAYER if maximizing_player else OPPONENT
    moves.sort(key=lambda move: score_move(board, move, player), reverse=maximizing_player)
    
    best_move = moves[0]  # Default to first move
    
    if maximizing_player:
        best_score = float('-inf')
        for move in moves:
            x, y = move
            board[x][y] = PLAYER
            
            # Check for immediate win
            if check_win(board, PLAYER):
                board[x][y] = 0  # Reset
                return 1000000, move
            
            score, _ = alpha_beta_pruning(board, depth - 1, alpha, beta, False, move)
            board[x][y] = 0  # Reset the move
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break  # Beta cutoff
                
        return best_score, best_move
    else:
        best_score = float('inf')
        for move in moves:
            x, y = move
            board[x][y] = OPPONENT
            
            # Check for immediate win
            if check_win(board, OPPONENT):
                board[x][y] = 0  # Reset
                return -1000000, move
            
            score, _ = alpha_beta_pruning(board, depth - 1, alpha, beta, True, move)
            board[x][y] = 0  # Reset the move
            
            if score < best_score:
                best_score = score
                best_move = move
            
            beta = min(beta, best_score)
            if beta <= alpha:
                break  # Alpha cutoff
                
        return best_score, best_move

def find_best_move(board):
    """Find the best move for the AI using iterative deepening"""
    # Convert to numpy array if it's not already
    if not isinstance(board, np.ndarray):
        board = np.array(board, dtype=np.int8)
    
    # Clear transposition table to avoid memory issues
    transposition_table.clear()
    
    # Count empty spaces to determine game phase
    empty_count = np.sum(board == 0)
    
    # Adjust depth based on game phase
    if empty_count > 200:  # Early game
        depth = 2
    elif empty_count > 150:  # Mid game
        depth = 3
    else:  # Late game
        depth = 4
    
    start_time = time.time()
    
    # Check for immediate winning moves or blocking moves first
    immediate_moves = get_available_moves(board)
    
    # First check if we can win in one move
    for move in immediate_moves:
        x, y = move
        board[x][y] = OPPONENT  # Our AI is OPPONENT (value 2)
        if check_win(board, OPPONENT):
            board[x][y] = 0  # Reset
            print(f"AI found winning move in {time.time() - start_time:.3f} seconds")
            return move
        board[x][y] = 0  # Reset
    
    # Then check if we need to block opponent's win
    for move in immediate_moves:
        x, y = move
        board[x][y] = PLAYER  # Player is PLAYER (value 1)
        if check_win(board, PLAYER):
            board[x][y] = 0  # Reset
            print(f"AI blocked winning move in {time.time() - start_time:.3f} seconds")
            return move
        board[x][y] = 0  # Reset
    
    # If no immediate win/block needed, use iterative deepening
    best_move = None
    for current_depth in range(1, depth + 1):
        try:
            _, move = alpha_beta_pruning(board, current_depth, float('-inf'), float('inf'), True)
            best_move = move
            
            # Check if we're running out of time
            if time.time() - start_time > 2.5:  # Stop if approaching 3 seconds
                break
        except Exception as e:
            print(f"Error at depth {current_depth}: {e}")
            if best_move is not None:
                break
    
    print(f"AI move computed in {time.time() - start_time:.3f} seconds at depth {current_depth}")
    return best_move