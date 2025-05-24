import pickle
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from entity.DeepAgent import DeepCaroAgent, BOARD_SIZE

# Load expert data
with open("expert_data.pkl", "rb") as f:
    dataset = pickle.load(f)

print(f"Loaded {len(dataset)} samples")

# Initialize model
agent = DeepCaroAgent(epsilon=0.0)
model = agent.q_net
model.train()

device = agent.device
model.to(device)

# Loss + Optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Convert dataset to tensors
X = []
y = []

for state, action in dataset:
    X.append(state)
    y.append(action[0] * BOARD_SIZE + action[1])

X = torch.FloatTensor(np.array(X)).to(device)  # (N, 15, 15)
y = torch.LongTensor(y).to(device)             # (N,)

# Pretrain
batch_size = 128
epochs = 5

for epoch in range(epochs):
    perm = torch.randperm(X.size(0))
    total_loss = 0

    for i in range(0, X.size(0), batch_size):
        idx = perm[i:i+batch_size]
        x_batch = X[idx]
        y_batch = y[idx]

        output = model(x_batch).to(device)
        loss = criterion(output, y_batch)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    print(f"Epoch {epoch+1}/{epochs} - Loss: {total_loss:.4f}")

# Save model
torch.save(model.state_dict(), "pretrained_deepcaro.pt")
print("✅ Saved pretrained model to pretrained_deepcaro.pt")


