# src/rl_gladiator.py
# Echoes of the Arena — Tabular Q-Learning Combat AI (Garg's Brain)
# Loads models/q_table.npy and returns Garg's counter-attack decision
# based on discretised game state.

import os
import numpy as np

# ── Path ──────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(__file__)
Q_TABLE_PATH  = os.path.join(BASE_DIR, "..", "models", "q_table.npy")

# ── Action space ──────────────────────────────────────────────────────────────
# Garg's possible combat actions
GARG_ACTIONS = {
    0: {"name": "Heavy Blow",       "damage": 15, "taunt": "Garg roars and drives his shield into your ribs!"},
    1: {"name": "Quick Strike",     "damage": 10, "taunt": "Garg feints left and slashes across your shoulder!"},
    2: {"name": "Defensive Stance", "damage":  5, "taunt": "Garg steps back, studying you with cold eyes."},
    3: {"name": "Crushing Slam",    "damage": 20, "taunt": "Garg leaps forward with a bone-crushing overhead slam!"},
    4: {"name": "Sweep Kick",       "damage":  8, "taunt": "Garg sweeps your legs — you barely keep your footing!"},
}

NUM_ACTIONS = len(GARG_ACTIONS)

# ── State discretisation ──────────────────────────────────────────────────────
# We discretise the continuous state space into bins for table lookup.
# State = (player_hp_bin, enemy_hp_bin, round_bin)
HP_BINS    = [0, 20, 40, 60, 80, 100]   # 5 bins
ROUND_BINS = [0, 2, 4, 6, 8, 10]        # 5 bins

# ── Module-level Q-table cache ────────────────────────────────────────────────
_q_table: np.ndarray | None = None


def _load_q_table() -> np.ndarray:
    """Load q_table.npy once and cache it. Generates a fallback if not found."""
    global _q_table
    if _q_table is not None:
        return _q_table

    if os.path.exists(Q_TABLE_PATH):
        try:
            _q_table = np.load(Q_TABLE_PATH, allow_pickle=True)
            # If loaded shape doesn't match our action space, regenerate
            if _q_table.ndim < 2 or _q_table.shape[-1] != NUM_ACTIONS:
                print(f"[rl_gladiator] Q-table shape {_q_table.shape} "
                      f"incompatible — generating fresh table.")
                _q_table = _generate_default_q_table()
            else:
                print(f"[rl_gladiator] Q-table loaded: {_q_table.shape}")
        except Exception as e:
            print(f"[rl_gladiator] Failed to load q_table.npy: {e} — using default.")
            _q_table = _generate_default_q_table()
    else:
        print(f"[rl_gladiator] q_table.npy not found at {Q_TABLE_PATH} "
              f"— generating heuristic table.")
        _q_table = _generate_default_q_table()

    return _q_table


def _generate_default_q_table() -> np.ndarray:
    """
    Generate a heuristic Q-table when no trained table is available.
    Shape: (hp_bins, hp_bins, round_bins, num_actions) = (5,5,5,5)

    Heuristic:
    - When player HP is low  → Garg prefers Heavy Blow / Crushing Slam
    - When player HP is high → Garg prefers Quick Strike / Sweep Kick
    - When enemy HP is low   → Garg goes defensive
    """
    n_hp = len(HP_BINS) - 1      # 5
    n_r  = len(ROUND_BINS) - 1   # 5
    table = np.zeros((n_hp, n_hp, n_r, NUM_ACTIONS), dtype=np.float32)

    for p in range(n_hp):       # player hp bin
        for e in range(n_hp):   # enemy hp bin
            for r in range(n_r):
                q = np.zeros(NUM_ACTIONS)

                # Player low HP → Garg goes for the kill
                if p <= 1:
                    q[3] = 10.0   # Crushing Slam
                    q[0] = 8.0    # Heavy Blow
                # Player mid HP → balanced aggression
                elif p <= 3:
                    q[1] = 8.0    # Quick Strike
                    q[0] = 7.0    # Heavy Blow
                    q[4] = 6.0    # Sweep Kick
                # Player high HP → wear them down
                else:
                    q[4] = 9.0    # Sweep Kick
                    q[1] = 8.0    # Quick Strike
                    q[2] = 5.0    # Defensive Stance

                # Enemy (Garg) low HP → go defensive
                if e <= 1:
                    q[2] += 5.0   # Defensive Stance bonus

                table[p, e, r] = q

    return table


def _discretise(value: float, bins: list) -> int:
    """Map a continuous value to a bin index."""
    for i in range(len(bins) - 1):
        if value <= bins[i + 1]:
            return i
    return len(bins) - 2


def get_garg_action(
    player_hp:  int,
    enemy_hp:   int,
    round_count: int,
    epsilon:    float = 0.1,
) -> dict:
    """
    Choose Garg's combat action using the Q-table (ε-greedy).

    Parameters
    ----------
    player_hp   : int   Current player HP (0-100)
    enemy_hp    : int   Garg's current HP (0-100)
    round_count : int   Current round number
    epsilon     : float Exploration rate (default 10%)

    Returns
    -------
    dict with keys:
        action_id   (int) : chosen action index
        name        (str) : action name
        damage      (int) : HP to subtract from player
        taunt       (str) : flavour text for UI display
    """
    q = _load_q_table()

    # ε-greedy
    if np.random.random() < epsilon:
        action_id = int(np.random.randint(0, NUM_ACTIONS))
    else:
        p_bin = _discretise(player_hp,   HP_BINS)
        e_bin = _discretise(enemy_hp,    HP_BINS)
        r_bin = _discretise(min(round_count, 10), ROUND_BINS)

        # Handle both flat and shaped Q-tables
        try:
            if q.ndim == 4:
                q_vals = q[p_bin, e_bin, r_bin]
            elif q.ndim == 2:
                state_idx = p_bin * 25 + e_bin * 5 + r_bin
                state_idx = min(state_idx, q.shape[0] - 1)
                q_vals = q[state_idx]
            else:
                q_vals = q.flatten()[:NUM_ACTIONS]
        except IndexError:
            q_vals = np.zeros(NUM_ACTIONS)

        # Pad or trim q_vals to NUM_ACTIONS
        if len(q_vals) < NUM_ACTIONS:
            q_vals = np.pad(q_vals, (0, NUM_ACTIONS - len(q_vals)))
        else:
            q_vals = q_vals[:NUM_ACTIONS]

        action_id = int(np.argmax(q_vals))

    action = GARG_ACTIONS[action_id].copy()
    action["action_id"] = action_id
    return action


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Garg Q-Table Combat Test")
    print("─" * 50)
    states = [
        (100, 50, 1),
        (30,  50, 3),
        (10,  50, 5),
        (50,  10, 8),
    ]
    for ph, eh, rc in states:
        result = get_garg_action(ph, eh, rc)
        print(f"  player_hp={ph:>3}  enemy_hp={eh:>3}  round={rc}"
              f"  →  {result['name']} ({result['damage']} dmg)")
        print(f"     \"{result['taunt']}\"")
