# training/generate_overseer_data.py
# Echoes of the Arena — Narrative Overseer Dataset Generator
# Generates 50,000 synthetic rows of combat state + reward data
# and saves to data/overseer_dataset.csv

import os
import numpy as np
import pandas as pd

# ── Config ───────────────────────────────────────────────────────────────────
NUM_ROWS = 50_000
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "overseer_dataset.csv")
SEED = 42

np.random.seed(SEED)

# ── Actions ──────────────────────────────────────────────────────────────────
# 0 = Neutral
# 1 = Buff Player  (Crowd Cheer  — easier fight)
# 2 = Nerf Player  (Ambush       — harder fight)


def compute_reward(player_hp: np.ndarray, action: np.ndarray) -> np.ndarray:
    """
    Reward logic — the Overseer's goal is to keep TENSION HIGH.

    Base reward from HP tension:
      - HP in [20, 70]  → +10  (sweet spot: player is challenged but alive)
      - HP == 100       → -10  (too easy, no drama)
      - HP == 0         → -10  (player dead, no fun)
      - HP in (70, 100) → scaled negative (getting too comfortable)
      - HP in (0, 20)   → scaled negative (about to die, drama ruined)

    Action bonus/penalty:
      - Action 1 (Buff)  applied when HP < 30  → +5  (good call, saves player)
      - Action 1 (Buff)  applied when HP > 70  → -5  (bad call, makes it too easy)
      - Action 2 (Nerf)  applied when HP > 70  → +5  (good call, raises stakes)
      - Action 2 (Nerf)  applied when HP < 30  → -5  (bad call, might kill player)
      - Action 0 (Neutral) always              →  0
    """
    reward = np.zeros(len(player_hp), dtype=np.float32)

    # ── Base HP tension reward ────────────────────────────────────────────
    in_sweet_spot = (player_hp >= 20) & (player_hp <= 70)
    too_easy = player_hp >= 95
    too_hard = player_hp <= 5

    reward[in_sweet_spot] += 10.0
    reward[too_easy] -= 10.0
    reward[too_hard] -= 10.0

    # Gradual penalty as HP drifts above 70 (comfort zone)
    drifting_high = (player_hp > 70) & (player_hp < 95)
    reward[drifting_high] -= ((player_hp[drifting_high] - 70) / 25.0) * 8.0

    # Gradual penalty as HP drifts below 20 (danger zone)
    drifting_low = (player_hp > 5) & (player_hp < 20)
    reward[drifting_low] -= ((20 - player_hp[drifting_low]) / 15.0) * 8.0

    # ── Action quality bonus ──────────────────────────────────────────────
    buff_good = (action == 1) & (player_hp < 30)
    buff_bad = (action == 1) & (player_hp > 70)
    nerf_good = (action == 2) & (player_hp > 70)
    nerf_bad = (action == 2) & (player_hp < 30)

    reward[buff_good] += 5.0
    reward[buff_bad] -= 5.0
    reward[nerf_good] += 5.0
    reward[nerf_bad] -= 5.0

    return reward


def generate_dataset(n: int = NUM_ROWS) -> pd.DataFrame:
    """Generate n rows of synthetic Overseer training data."""

    player_hp = np.random.randint(0,  101, size=n)
    honor_score = np.random.randint(0,  101, size=n)
    win_streak = np.random.randint(0,   11, size=n)
    action = np.random.randint(0,    3, size=n)   # 0, 1, or 2

    reward = compute_reward(player_hp, action)

    df = pd.DataFrame({
        "player_hp":   player_hp,
        "honor_score": honor_score,
        "win_streak":  win_streak,
        "action_taken": action,
        "reward":      reward,
    })
    return df


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Generating {NUM_ROWS:,} rows of Overseer training data...")
    df = generate_dataset(NUM_ROWS)

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved → {OUTPUT_CSV}")
    print(f"\nDataset shape : {df.shape}")
    print(f"Action counts :\n{df['action_taken'].value_counts().sort_index()}")
    print(f"\nReward stats  :\n{df['reward'].describe().round(2)}")
