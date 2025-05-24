import numpy as np
import pickle
from entity.CaroAI import create_board, check_win, PLAYER, OPPONENT, EMPTY
from entity.DeepAgent import BOARD_SIZE
from UI.GUI import SmartAgent  # bạn đã có sẵn SmartAgent
import random

class RuleBasedAgent:
    def __init__(self):
        from entity.CaroAI import get_available_moves, check_win
        self.get_available_moves = get_available_moves
        self.check_win = check_win
        self.name = "RuleBasedAgent"

    def find_best_move(self, board):
        moves = self.get_available_moves(board)

        # Win immediately
        for move in moves:
            x, y = move
            board[x][y] = PLAYER
            if self.check_win(board, PLAYER):
                board[x][y] = EMPTY
                return move
            board[x][y] = EMPTY

        # Block opponent
        for move in moves:
            x, y = move
            board[x][y] = OPPONENT
            if self.check_win(board, OPPONENT):
                board[x][y] = EMPTY
                return move
            board[x][y] = EMPTY

        # Otherwise pick center or random
        center = BOARD_SIZE // 2
        if board[center][center] == EMPTY:
            return (center, center)
        return random.choice(moves)


def generate_data(n_games=1000, save_path="expert_data.pkl"):
    data = []
    agent1 = RuleBasedAgent()
    agent2 = RuleBasedAgent()

    for game_idx in range(n_games):
        board = create_board()
        current_agent = agent1
        current_player = PLAYER
        game_steps = []

        for _ in range(BOARD_SIZE * BOARD_SIZE):
            move = current_agent.find_best_move(board)
            if not move:
                break

            board_copy = board.copy()
            game_steps.append((board_copy, move, current_player))
            board[move] = current_player

            if check_win(board, current_player):
                break

            current_agent = agent2 if current_agent == agent1 else agent1
            current_player = OPPONENT if current_player == PLAYER else PLAYER

        for state, action, who in game_steps:
            if who == PLAYER:
                data.append((state, action))

        if (game_idx + 1) % 50 == 0:
            print(f"[{game_idx + 1}/{n_games}] games generated")

    with open(save_path, "wb") as f:
        pickle.dump(data, f)
    print(f"✅ Saved {len(data)} samples to {save_path}")


if __name__ == "__main__":
    generate_data()

# import numpy as np
# import pickle
# from CaroAI import create_board, check_win, PLAYER, OPPONENT, EMPTY
# from GUI import SmartAgent
# from DeepAgent import BOARD_SIZE
# import random

# class RuleBasedAgent:
#     def __init__(self):
#         from CaroAI import get_available_moves, check_win
#         self.get_available_moves = get_available_moves
#         self.check_win = check_win
#         self.name = "RuleBasedAgent"

#     def find_best_move(self, board):
#         moves = self.get_available_moves(board)

#         for move in moves:
#             x, y = move
#             board[x][y] = OPPONENT
#             if self.check_win(board, OPPONENT):
#                 board[x][y] = EMPTY
#                 return move
#             board[x][y] = EMPTY

#         for move in moves:
#             x, y = move
#             board[x][y] = PLAYER
#             if self.check_win(board, PLAYER):
#                 board[x][y] = EMPTY
#                 return move
#             board[x][y] = EMPTY

#         center = BOARD_SIZE // 2
#         if board[center][center] == EMPTY:
#             return (center, center)
#         return random.choice(moves)

# def generate_data(n_games=20, save_path="expert_data.pkl"):
#     data = []
#     smart = SmartAgent()
#     rule = RuleBasedAgent()

#     for game_idx in range(n_games):
#         board = create_board()
#         current_player = PLAYER
#         current_agent = smart
#         other_agent = rule
#         game_steps = []

#         for _ in range(BOARD_SIZE * BOARD_SIZE):
#             move = current_agent.find_best_move(board)
#             if not move:
#                 break

#             board_copy = board.copy()
#             if current_agent == smart:
#                 game_steps.append((board_copy, move))

#             board[move] = current_player

#             if check_win(board, current_player):
#                 break

#             current_agent, other_agent = other_agent, current_agent
#             current_player = OPPONENT if current_player == PLAYER else PLAYER

#         data.extend(game_steps)

#         if (game_idx + 1) % 20 == 0:
#             print(f"[{game_idx + 1}/{n_games}] games processed")

#     with open(save_path, "wb") as f:
#         pickle.dump(data, f)
#     print(f"✅ Saved {len(data)} expert samples to {save_path}")

# if __name__ == "__main__":
#     generate_data(n_games=20)
