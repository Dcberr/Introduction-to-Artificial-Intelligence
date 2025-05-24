import numpy as np
import random
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import os

BOARD_SIZE = 15
EMPTY, PLAYER, OPPONENT = 0, 1, 2

class QNetwork(nn.Module):
    def __init__(self):
        super(QNetwork, self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
        )
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * BOARD_SIZE * BOARD_SIZE, 512),
            nn.ReLU(),
            nn.Linear(512, BOARD_SIZE * BOARD_SIZE)
        )

    def forward(self, x):
        x = x.unsqueeze(1)  # Add channel dimension
        x = self.conv(x)
        return self.fc(x)

class DeepCaroAgent:
    def __init__(self, epsilon=0.1):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.q_net = QNetwork().to(self.device)
        self.target_net = QNetwork().to(self.device)
        model_path = "best_deepcaro.pt"
        if os.path.exists(model_path):
            self.q_net.load_state_dict(torch.load(model_path, map_location=self.device))
            self.target_net.load_state_dict(self.q_net.state_dict())
        elif os.path.exists("./data/pretrained_deepcaro.pt"):
            self.q_net.load_state_dict(torch.load("./data/pretrained_deepcaro.pt", map_location=self.device))
            self.target_net.load_state_dict(self.q_net.state_dict())
            print("[INFO] Loaded pretrained model.")
        else:
            print("[INFO] No model found. Starting from scratch.")

        self.optimizer = optim.Adam(self.q_net.parameters(), lr=0.001)
        self.criterion = nn.MSELoss()
        self.memory = deque(maxlen=20000)
        self.batch_size = 64
        self.epsilon = epsilon
        self.gamma = 0.99
        self.update_steps = 0
        self.name = "DeepCaroAgent"
        self.move_stats = {"blocks": 0, "opportunities": 0, "total_moves": 0}

    def get_action(self, board):
        flat_board = torch.FloatTensor(board).unsqueeze(0).to(self.device)
        if random.random() < self.epsilon:
            empty_cells = np.argwhere(board == EMPTY)
            return tuple(random.choice(empty_cells))
        with torch.no_grad():
            q_values = self.q_net(flat_board).reshape(BOARD_SIZE, BOARD_SIZE)
            mask = torch.FloatTensor((board == EMPTY).astype(np.float32)).to(self.device)
            q_values = q_values * mask - (1 - mask) * 1e10
            move = torch.argmax(q_values).item()
            return divmod(move, BOARD_SIZE)

    def store_experience(self, state, action, reward, next_state, done):
        self.memory.append((state.copy(), action, reward, next_state.copy(), done))

    def train_step(self):
        if len(self.memory) < self.batch_size:
            return

        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        states = torch.FloatTensor(np.array(states)).to(self.device)
        next_states = torch.FloatTensor(np.array(next_states)).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)

        q_values = self.q_net(states).reshape(-1, BOARD_SIZE, BOARD_SIZE)
        next_q_values = self.target_net(next_states).reshape(-1, BOARD_SIZE, BOARD_SIZE)
        next_q_values_online = self.q_net(next_states).reshape(-1, BOARD_SIZE, BOARD_SIZE)

        target_q = q_values.clone().detach()

        for i, (a, r, done) in enumerate(zip(actions, rewards, dones)):
            x, y = a
            best_next_action = torch.argmax(next_q_values_online[i]).item()
            x_a, y_a = divmod(best_next_action, BOARD_SIZE)
            max_next_q = next_q_values[i, x_a, y_a].item()
            target = r if done else r + self.gamma * max_next_q
            target_q[i, x, y] = target

        loss = self.criterion(q_values, target_q)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        self.soft_update()

    def soft_update(self, tau=0.01):
        for target_param, param in zip(self.target_net.parameters(), self.q_net.parameters()):
            target_param.data.copy_(tau * param.data + (1.0 - tau) * target_param.data)

    def find_best_move(self, board):
        self.move_stats["total_moves"] += 1
        return self.get_action(board)
