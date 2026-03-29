# src/rl_overseer.py
# Echoes of the Arena — Narrative Overseer Inference
# Loads the trained DQN and returns narrative action decisions
# based on current game state.  Called from app.py each round.

import os
import numpy as np
import torch
import torch.nn as nn

# ── Path to saved weights ─────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "..", "models", "overseer_model.pth")

# ── Inference device ──────────────────────────────────────────────────────────
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ── Action mapping ────────────────────────────────────────────────────────────
ACTION_MAP = {
    0: "Neutral",
    1: "Buff Player",
    2: "Nerf Player",
}

ACTION_DESCRIPTIONS = {
    "Neutral":      "The crowd watches in silence. The Overseer holds his hand.",
    "Buff Player":  "The crowd ROARS — Kaelen feels a surge of strength! (+15 HP)",
    "Nerf Player":  "A hooded figure hurls a smoke bomb — Kaelen is momentarily blinded! (-10 HP)",
}


# ════════════════════════════════════════════════════════════════════════════
# MODEL DEFINITION  (must match training/train_overseer.py exactly)
# ════════════════════════════════════════════════════════════════════════════

class OverseerDQN(nn.Module):
    def __init__(self, input_dim: int = 3, hidden: int = 64, output_dim: int = 3):
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
# MODEL LOADER  (singleton — loaded once, reused every call)
# ════════════════════════════════════════════════════════════════════════════

_model: OverseerDQN | None = None


def _load_model() -> OverseerDQN:
    """Load model weights once and cache the instance."""
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Overseer model not found at '{MODEL_PATH}'.\n"
                "Run  python training/train_overseer.py  first."
            )
        _model = OverseerDQN().to(DEVICE)
        _model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
        _model.eval()
        print(f"[rl_overseer] Model loaded from {MODEL_PATH}")
    return _model


# ════════════════════════════════════════════════════════════════════════════
# PUBLIC INFERENCE API
# ════════════════════════════════════════════════════════════════════════════

def get_overseer_action(
    player_hp:   int,
    honor_score: int,
    win_streak:  int,
    epsilon:     float = 0.05,
) -> dict:
    """
    Given the current game state, return the Overseer's chosen narrative action.

    Parameters
    ----------
    player_hp    : int   Current player HP (0–100)
    honor_score  : int   Current honour score (0–100)
    win_streak   : int   Consecutive wins so far (0–10)
    epsilon      : float Exploration rate — small random action probability
                         (keeps the game unpredictable; default 5%)

    Returns
    -------
    dict with keys:
        action_id     (int)  : 0 | 1 | 2
        action_name   (str)  : 'Neutral' | 'Buff Player' | 'Nerf Player'
        description   (str)  : Flavour text to display in the UI
        q_values      (list) : Raw Q-values for all 3 actions
        hp_delta      (int)  : HP change to apply to player (+15 / -10 / 0)
    """
    # ── ε-greedy exploration ──────────────────────────────────────────────
    if np.random.random() < epsilon:
        action_id = int(np.random.randint(0, 3))
        q_values  = [0.0, 0.0, 0.0]
    else:
        model = _load_model()

        # Normalise inputs to [0, 1] (same scale as training)
        norm = [
            np.clip(player_hp,   0, 100) / 100.0,
            np.clip(honor_score, 0, 100) / 100.0,
            np.clip(win_streak,  0,  10) /  10.0,
        ]
        x = torch.tensor([norm], dtype=torch.float32).to(DEVICE)

        with torch.no_grad():
            q = model(x).cpu().numpy()[0]

        action_id = int(np.argmax(q))
        q_values  = q.tolist()

    action_name = ACTION_MAP[action_id]
    description = ACTION_DESCRIPTIONS[action_name]

    # ── HP delta ──────────────────────────────────────────────────────────
    hp_delta_map = {
        "Neutral":     0,
        "Buff Player": +15,
        "Nerf Player": -10,
    }

    return {
        "action_id":   action_id,
        "action_name": action_name,
        "description": description,
        "q_values":    q_values,
        "hp_delta":    hp_delta_map[action_name],
    }


def get_overseer_action_safe(
    player_hp:   int,
    honor_score: int,
    win_streak:  int,
) -> dict:
    """
    Wrapper around get_overseer_action with full error handling.
    Returns a Neutral action if the model isn't available yet.
    Safe to call from app.py before training has been run.
    """
    try:
        return get_overseer_action(player_hp, honor_score, win_streak)
    except FileNotFoundError:
        print("[rl_overseer] WARNING: Model not trained yet — defaulting to Neutral.")
        return {
            "action_id":   0,
            "action_name": "Neutral",
            "description": "The Overseer watches from the shadows, not yet ready to intervene.",
            "q_values":    [0.0, 0.0, 0.0],
            "hp_delta":    0,
        }
    except Exception as e:
        print(f"[rl_overseer] ERROR: {e} — defaulting to Neutral.")
        return {
            "action_id":   0,
            "action_name": "Neutral",
            "description": "The Overseer hesitates.",
            "q_values":    [0.0, 0.0, 0.0],
            "hp_delta":    0,
        }


# ════════════════════════════════════════════════════════════════════════════
# QUICK TEST  (python src/rl_overseer.py)
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    test_states = [
        {"player_hp": 100, "honor_score": 50, "win_streak": 0},
        {"player_hp": 15,  "honor_score": 30, "win_streak": 2},
        {"player_hp": 50,  "honor_score": 80, "win_streak": 5},
        {"player_hp": 5,   "honor_score": 10, "win_streak": 0},
    ]

    print("Overseer Inference Test")
    print("─" * 60)
    for state in test_states:
        result = get_overseer_action_safe(**state)
        print(f"State : hp={state['player_hp']:>3}  "
              f"honor={state['honor_score']:>3}  "
              f"streak={state['win_streak']}")
        print(f"  → {result['action_name']} (hp_delta={result['hp_delta']:+d})")
        print(f"     {result['description']}")
        print()
