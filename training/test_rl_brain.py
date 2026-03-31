import numpy as np

# 1. Load the trained brain
try:
    q_table = np.load("models/q_table.npy")
    print("✅ Q-Table successfully loaded!")
    print(f"Q-Table Shape: {q_table.shape}\n")
except FileNotFoundError:
    print("❌ Error: q_table.npy not found. Did you run the training script?")
    exit()

# Action mapping (Based on your Phase 1 prompt)
agent_actions = {0: "Light Attack", 1: "Heavy Attack", 2: "Block"}


def ask_garg(player_hp_bin, enemy_hp_bin, player_honor_bin):
    """Interrogates the Q-table for the best action."""
    # Look up the state in the Q-table
    state_q_values = q_table[player_hp_bin, enemy_hp_bin, player_honor_bin]

    # Find the action with the highest Q-value (argmax)
    best_action_index = np.argmax(state_q_values)

    return agent_actions[best_action_index], state_q_values

# --- TEST SCENARIOS ---


print("=== RUNNING INFERENCE TESTS ===\n")

# Scenario A: The player is honorable (Honor Bin 2), both have high HP (Bin 3)
action, values = ask_garg(player_hp_bin=3, enemy_hp_bin=3, player_honor_bin=2)
print("Scenario A: Player is HONORABLE.")
print(f"Garg chooses to: {action}")
print(f"Q-Values for [Light, Heavy, Block]: {np.round(values, 2)}\n")

# Scenario B: The player is DISHONORABLE (Honor Bin 0), both have high HP (Bin 3)
# Because of our +15 reward rule, Garg should absolutely choose Heavy Attack here.
action, values = ask_garg(player_hp_bin=3, enemy_hp_bin=3, player_honor_bin=0)
print("Scenario B: Player is DISHONORABLE (Used poison/dirt).")
print(f"Garg chooses to: {action}")
print(f"Q-Values for [Light, Heavy, Block]: {np.round(values, 2)}\n")

# Scenario C: Garg is dying (Enemy HP Bin 1), Player is healthy (Player HP Bin 3)
action, values = ask_garg(player_hp_bin=3, enemy_hp_bin=1, player_honor_bin=1)
print("Scenario C: Garg is DYING, Player is Healthy.")
print(f"Garg chooses to: {action}")
print(f"Q-Values for [Light, Heavy, Block]: {np.round(values, 2)}\n")
