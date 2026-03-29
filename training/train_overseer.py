# training/train_overseer.py
# Echoes of the Arena — Deep Q-Network Narrative Overseer
# Trains a 3-layer DQN on the generated overseer_dataset.csv
# and saves weights to models/overseer_model.pth

import os
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(__file__)
DATA_CSV    = os.path.join(BASE_DIR, "..", "data",   "overseer_dataset.csv")
MODEL_PATH  = os.path.join(BASE_DIR, "..", "models", "overseer_model.pth")

# ── Hyperparameters ───────────────────────────────────────────────────────────
INPUT_DIM   = 3       # player_hp, honor_score, win_streak
HIDDEN_SIZE = 64
OUTPUT_DIM  = 3       # Q-values for actions 0, 1, 2

BATCH_SIZE  = 256
EPOCHS      = 30
LR          = 1e-3
SEED        = 42

torch.manual_seed(SEED)
np.random.seed(SEED)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ════════════════════════════════════════════════════════════════════════════
# MODEL ARCHITECTURE
# ════════════════════════════════════════════════════════════════════════════

class OverseerDQN(nn.Module):
    """
    3-layer Deep Q-Network for the Narrative Overseer.

    Input  : (batch, 3)  — normalised [player_hp, honor_score, win_streak]
    Output : (batch, 3)  — Q-values for [Neutral, Buff Player, Nerf Player]
    """

    def __init__(self, input_dim: int = INPUT_DIM,
                 hidden: int = HIDDEN_SIZE,
                 output_dim: int = OUTPUT_DIM):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, output_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


# ════════════════════════════════════════════════════════════════════════════
# DATA LOADING & PREPROCESSING
# ════════════════════════════════════════════════════════════════════════════

def load_data(csv_path: str):
    """
    Load the overseer CSV, normalise features to [0,1],
    and build supervised targets:
      For each row the 'correct' Q-value vector has the observed reward
      in the taken-action slot and 0 elsewhere (simplified Bellman target).
    """
    print(f"Loading dataset from {csv_path} ...")
    df = pd.read_csv(csv_path)

    # ── Feature normalisation ──────────────────────────────────────────────
    features = df[["player_hp", "honor_score", "win_streak"]].values.astype(np.float32)
    features[:, 0] /= 100.0   # player_hp   → [0, 1]
    features[:, 1] /= 100.0   # honor_score → [0, 1]
    features[:, 2] /= 10.0    # win_streak  → [0, 1]

    actions = df["action_taken"].values.astype(np.int64)
    rewards = df["reward"].values.astype(np.float32)

    # ── Build Q-target vectors ─────────────────────────────────────────────
    # Shape: (N, 3) — all zeros except the taken action's reward
    q_targets = np.zeros((len(df), OUTPUT_DIM), dtype=np.float32)
    q_targets[np.arange(len(df)), actions] = rewards

    X = torch.tensor(features)
    Y = torch.tensor(q_targets)

    print(f"  Rows: {len(df):,}  |  Features: {X.shape}  |  Targets: {Y.shape}")
    return X, Y


# ════════════════════════════════════════════════════════════════════════════
# TRAINING LOOP
# ════════════════════════════════════════════════════════════════════════════

def train():
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    # ── Data ──────────────────────────────────────────────────────────────
    X, Y     = load_data(DATA_CSV)
    dataset  = TensorDataset(X, Y)
    loader   = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    # ── Model, loss, optimiser ────────────────────────────────────────────
    model     = OverseerDQN().to(DEVICE)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=LR)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)

    print(f"\nTraining OverseerDQN on {DEVICE}")
    print(f"  Architecture : {INPUT_DIM} → {HIDDEN_SIZE} → {HIDDEN_SIZE} → {OUTPUT_DIM}")
    print(f"  Epochs       : {EPOCHS}")
    print(f"  Batch size   : {BATCH_SIZE}")
    print(f"  Optimizer    : Adam (lr={LR})\n")

    best_loss = float("inf")

    for epoch in range(1, EPOCHS + 1):
        model.train()
        epoch_loss = 0.0

        for x_batch, y_batch in loader:
            x_batch = x_batch.to(DEVICE)
            y_batch = y_batch.to(DEVICE)

            optimizer.zero_grad()
            predictions = model(x_batch)
            loss        = criterion(predictions, y_batch)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item() * len(x_batch)

        scheduler.step()
        avg_loss = epoch_loss / len(dataset)

        # Save best checkpoint
        if avg_loss < best_loss:
            best_loss = avg_loss
            torch.save(model.state_dict(), MODEL_PATH)
            checkpoint_marker = " ✓ saved"
        else:
            checkpoint_marker = ""

        if epoch % 5 == 0 or epoch == 1:
            print(f"  Epoch [{epoch:>3}/{EPOCHS}]  "
                  f"Loss: {avg_loss:.6f}  "
                  f"LR: {scheduler.get_last_lr()[0]:.6f}"
                  f"{checkpoint_marker}")

    print(f"\nTraining complete.")
    print(f"Best loss      : {best_loss:.6f}")
    print(f"Model saved → {MODEL_PATH}")


# ════════════════════════════════════════════════════════════════════════════
# QUICK SANITY CHECK
# ════════════════════════════════════════════════════════════════════════════

def evaluate_sample():
    """Run a few sample states through the trained model and print actions."""
    model = OverseerDQN().to(DEVICE)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()

    action_names = ["Neutral", "Buff Player (Crowd Cheer)", "Nerf Player (Ambush)"]

    samples = [
        [100.0, 50.0, 0.0],   # HP=100 — too easy, expect Nerf
        [15.0,  30.0, 2.0],   # HP=15  — near death, expect Buff
        [50.0,  80.0, 5.0],   # HP=50  — sweet spot, expect Neutral
    ]

    print("\nSample inference:")
    print(f"  {'State (hp/honor/streak)':<30} {'Q-values':<40} Action")
    print("  " + "─" * 85)

    for s in samples:
        norm = [s[0]/100, s[1]/100, s[2]/10]
        x    = torch.tensor([norm], dtype=torch.float32).to(DEVICE)
        with torch.no_grad():
            q = model(x).cpu().numpy()[0]
        action = int(np.argmax(q))
        label  = f"hp={int(s[0])} honor={int(s[1])} streak={int(s[2])}"
        print(f"  {label:<30} {str(q.round(3)):<40} {action_names[action]}")


if __name__ == "__main__":
    train()
    evaluate_sample()
