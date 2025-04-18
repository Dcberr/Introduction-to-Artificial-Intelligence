import time
import psutil
import os
from collections import deque
import heapq
import copy

class ChessPiece:
    def __init__(self, piece_type, position):
        self.piece_type = piece_type
        self.position = position
        
    def __repr__(self):
        return f"{self.get_full_name()} at {self.get_position_str()}"
    
    def get_full_name(self):
        piece_names = {
            'K': 'King',
            'Q': 'Queen',
            'R': 'Rook',
            'B': 'Bishop',
            'N': 'Knight',
            'P': 'Pawn'
        }
        return piece_names.get(self.piece_type, self.piece_type)
        
    def get_position_str(self):
        row, col = self.position
        col_letter = chr(col + ord('a'))
        row_number = 8 - row
        return f"{col_letter}{row_number}"

class Move:
    def __init__(self, piece, from_pos, to_pos, captured_piece):
        self.piece = piece
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.captured_piece = captured_piece
        
    def __repr__(self):
        from_pos_str = self._pos_to_str(self.from_pos)
        to_pos_str = self._pos_to_str(self.to_pos)
        return f"{self.piece.get_full_name()} at {from_pos_str} captured {self.captured_piece.get_full_name()} at {to_pos_str}"
    
    def _pos_to_str(self, pos):
        row, col = pos
        col_letter = chr(col + ord('a'))
        row_number = 8 - row
        return f"{col_letter}{row_number}"

class ChessState:
    def __init__(self, pieces, last_move=None):
        self.pieces = pieces
        self.board_size = 8
        self.last_move = last_move
        
    def __hash__(self):
        return hash(tuple(sorted((p.piece_type, p.position) for p in self.pieces)))
    
    def __eq__(self, other):
        if not isinstance(other, ChessState):
            return False
        return self.__hash__() == other.__hash__()
    
    def __repr__(self):
        return f"ChessState with {len(self.pieces)} pieces"
    
    def is_goal(self):
        return len(self.pieces) == 1
    
    def get_valid_moves(self, piece):
        moves = []
        row, col = piece.position
        
        if piece.piece_type == 'P':  # Pawn
            captures = [(row-1, col-1), (row-1, col+1)]
            for new_pos in captures:
                if self._is_valid_capture(piece, new_pos):
                    moves.append(new_pos)
                    
        elif piece.piece_type == 'R':  # Rook
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            moves.extend(self._get_sliding_moves(piece, directions))
            
        elif piece.piece_type == 'B':  # Bishop
            directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            moves.extend(self._get_sliding_moves(piece, directions))
            
        elif piece.piece_type == 'N':  # Knight
            knight_moves = [
                (row+2, col+1), (row+2, col-1),
                (row-2, col+1), (row-2, col-1),
                (row+1, col+2), (row+1, col-2),
                (row-1, col+2), (row-1, col-2)
            ]
            for new_pos in knight_moves:
                if self._is_valid_capture(piece, new_pos):
                    moves.append(new_pos)
                    
        elif piece.piece_type == 'Q':  # Queen
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0),
                         (1, 1), (1, -1), (-1, 1), (-1, -1)]
            moves.extend(self._get_sliding_moves(piece, directions))
            
        elif piece.piece_type == 'K':  # King
            king_moves = [
                (row+dr, col+dc)
                for dr in [-1, 0, 1]
                for dc in [-1, 0, 1]
                if (dr, dc) != (0, 0)
            ]
            for new_pos in king_moves:
                if self._is_valid_capture(piece, new_pos):
                    moves.append(new_pos)
                    
        return moves
    
    def _is_valid_capture(self, piece, new_pos):
        row, col = new_pos
        if not (0 <= row < self.board_size and 0 <= col < self.board_size):
            return False
            
        # Check if there's a piece to capture at the new position
        for p in self.pieces:
            if p.position == new_pos and p != piece:
                return True
        return False
    
    def _get_sliding_moves(self, piece, directions):
        moves = []
        for dr, dc in directions:
            row, col = piece.position
            while True:
                row, col = row + dr, col + dc
                if not (0 <= row < self.board_size and 0 <= col < self.board_size):
                    break
                if self._is_valid_capture(piece, (row, col)):
                    moves.append((row, col))
                    break
                if any(p.position == (row, col) for p in self.pieces):
                    break
        return moves
    
    def get_next_states(self):
        next_states = []
        for piece in self.pieces:
            valid_moves = self.get_valid_moves(piece)
            for move_to in valid_moves:
                new_pieces = []
                captured_piece = None
                original_pos = piece.position
                
                for p in self.pieces:
                    if p.position == move_to:  # This is the captured piece
                        captured_piece = p
                    elif p == piece:  # This is the moving piece
                        new_piece = ChessPiece(p.piece_type, move_to)
                        new_pieces.append(new_piece)
                    else:  # Other pieces remain unchanged
                        new_pieces.append(copy.deepcopy(p))
                
                # Create a Move object to track this capture
                move_info = Move(
                    piece,  # Original piece
                    original_pos,  # From position
                    move_to,  # To position
                    captured_piece  # Captured piece
                )
                next_states.append(ChessState(new_pieces, move_info))
        return next_states

def bfs_search(initial_state):
    queue = deque([(initial_state, [])])
    visited = set()
    
    while queue:
        current_state, path = queue.popleft()
        if current_state.is_goal():
            return path
            
        state_hash = hash(current_state)
        if state_hash in visited:
            continue
            
        visited.add(state_hash)
        
        for next_state in current_state.get_next_states():
            if hash(next_state) not in visited:
                new_path = path + [next_state]
                queue.append((next_state, new_path))
    
    return None

def heuristic(state):
    return len(state.pieces) - 1

class PrioritizedState:
    def __init__(self, f_score, steps, state, path):
        self.f_score = f_score
        self.steps = steps
        self.state = state
        self.path = path
        
    def __lt__(self, other):
        if self.f_score == other.f_score:
            return self.steps < other.steps
        return self.f_score < other.f_score

def a_star_search(initial_state):
    frontier = [PrioritizedState(heuristic(initial_state), 0, initial_state, [])]
    visited = set()
    
    while frontier:
        current = heapq.heappop(frontier)
        current_state = current.state
        
        if current_state.is_goal():
            return current.path
            
        state_hash = hash(current_state)
        if state_hash in visited:
            continue
            
        visited.add(state_hash)
        
        for next_state in current_state.get_next_states():
            if hash(next_state) not in visited:
                next_steps = current.steps + 1
                h_score = heuristic(next_state)
                f_score = next_steps + h_score
                new_path = current.path + [next_state]
                heapq.heappush(frontier, 
                    PrioritizedState(f_score, next_steps, next_state, new_path))
    
    return None

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024  # Convert bytes to kB

def print_performance_metrics(start_time, start_memory, algorithm_name):
    end_time = time.time()
    end_memory = get_memory_usage()
    
    execution_time = (end_time - start_time) * 1000  # Convert seconds to milliseconds
    memory_used = end_memory - start_memory
    
    print(f"\n{algorithm_name} Performance:")
    print(f"Execution time: {execution_time:.2f} ms")
    print(f"Memory used: {memory_used:.2f} kB")

def print_solution(path):
    if path is None:
        print("No solution found!")
        return
        
    print(f"Solution found in {len(path)} moves:")
    for i, state in enumerate(path):
        print(f"\nMove {i + 1}:")
        if state.last_move:
            print(f"Capture: {state.last_move}")
        print("Remaining pieces:")
        for piece in state.pieces:
            print(f"  {piece}")

def create_piece_from_input():
    """Create a chess state from user input"""
    pieces = []
    piece_positions = {}  # To track occupied positions
    
    piece_types = {
        'king': 'K',
        'queen': 'Q',
        'rook': 'R',
        'bishop': 'B',
        'knight': 'N',
        'pawn': 'P'
    }
    
    print("Enter chess pieces one by one like this: knight c5)")
    print("Type 'done' when finished")
    
    while True:
        user_input = input("> ").strip().lower()
        
        if user_input == 'done':
            if len(pieces) < 2:
                print("Need at least 2 pieces to create a valid puzzle. Please add more pieces.")
                continue
            break
            
        try:
            parts = user_input.split()
            if len(parts) != 2:
                print("Invalid format. Use format like this : knight c5")
                continue
                
            piece_name, position_str = parts
            
            if piece_name not in piece_types:
                print(f"Invalid piece type. Use one of: {', '.join(piece_types.keys())}")
                continue
                
            piece_type = piece_types[piece_name]
            
            # Transfer position from character to cordinate (e.g., 'c5' to (3, 2))
            if (len(position_str) != 2 or 
                not ('a' <= position_str[0] <= 'h') or 
                not ('1' <= position_str[1] <= '8')):
                print("Invalid position. Use chess cordition (example: c5)")
                continue
                
            col = ord(position_str[0]) - ord('a')
            row = 8 - int(position_str[1])
            position = (row, col)
            
            # Check if position already occupied
            if position in piece_positions:
                old_piece_index = piece_positions[position]
                pieces[old_piece_index] = ChessPiece(piece_type, position)
                print(f"Replaced piece at {position_str}")
            else:
                # Add new piece
                pieces.append(ChessPiece(piece_type, position))
                piece_positions[position] = len(pieces) - 1
                print(f"Added {piece_name} at {position_str}")
                
        except Exception as e:
            print(f"Error processing input: {e}")
    
    return ChessState(pieces)

if __name__ == "__main__":
    print("Setting up Chess Ranger...")
    initial_state = create_piece_from_input()
    
    print("\nChess board:")
    for piece in initial_state.pieces:
        print(f"  {piece}")
    
    print("\nTesting BFS:")
    start_memory_bfs = get_memory_usage()
    start_time_bfs = time.time()
    bfs_solution = bfs_search(initial_state)
    print_solution(bfs_solution)
    print_performance_metrics(start_time_bfs, start_memory_bfs, "BFS")
    
    print("\nTesting A*:")
    start_memory_astar = get_memory_usage()
    start_time_astar = time.time()
    astar_solution = a_star_search(initial_state)
    print_solution(astar_solution)
    print_performance_metrics(start_time_astar, start_memory_astar, "A*")