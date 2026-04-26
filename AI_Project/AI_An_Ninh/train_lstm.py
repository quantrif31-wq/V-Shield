import numpy as np
import torch
import torch.nn as nn
import os

# ===== LOAD DATA =====
data = np.load("hanh_vi/ngat/data/dataset.npz")

X = data["X"]
y = data["y"]

print("X shape:", X.shape)

# ===== MODEL =====
class Model(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(8, 64, batch_first=True)
        self.fc = nn.Linear(64, 2)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])


model = Model()

optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.CrossEntropyLoss()

X = torch.tensor(X).float()
y = torch.tensor(y).long()

# ===== TRAIN =====
for epoch in range(10):
    output = model(X)
    loss = loss_fn(output, y)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    print(f"Epoch {epoch} - Loss: {loss.item()}")

# ===== SAVE =====
os.makedirs("outputs", exist_ok=True)

torch.save({
    "model_state": model.state_dict()
}, "outputs/lstm_best.pt")

print("TRAIN DONE")