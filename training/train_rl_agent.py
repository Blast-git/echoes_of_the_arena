"""
=============================================================================
  Echoes of the Arena — Reinforcement Learning Agent Training Script
  File: training/train_rl_agent.py
=============================================================================

  Q-Learning (Bellman Equation):
  Q(s,a) <- Q(s,a) + alpha * [r + gamma * max_a' Q(s',a') - Q(s,a)]

  Where:
    Q(s,a)              = current Q-value for state s, action a
    alpha               = learning rate (how fast we update)
    r                   = immediate reward received
    gamma               = discount factor (how much we value future rewards)
    max_a' Q(s',a')     = best possible Q-value in the next state s'

=============================================================================
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── Reproducibility ──────────────────────────────────────────────────────────
np.random.seed(42)

# ── Hyperparameters ──────────────────────────────────────────────────────────
EPISODES        = 10_000
ALPHA           = 0.1       # Learning rate
GAMMA           = 0.95      # Discount factor
EPSILON_START   = 1.0       # Initial exploration rate
EPSILON_END     = 0.05      # Minimum exploration rate
EPSILON_DECAY   = 0.9995    # Decay multiplier per episode
ROLLING_WINDOW  = 200       # Window for rolling-average reward plot

# ── Action Indices ────────────────────────────────────────────────────────────
# Player (simulated bot) actions
PLAYER_HONORABLE_STRIKE  = 0
PLAYER_DEFEND            = 1
PLAYER_DISHONORABLE_POISON = 2

# Agent (enemy gladiator) actions
AGENT_LIGHT_ATTACK = 0
AGENT_HEAVY_ATTACK = 1
AGENT_BLOCK        = 2

N_AGENT_ACTIONS = 3

# ── State-space dimensions ───────────────────────────────────────────────────
# player_hp_bin:    0=Dead | 1=Low(1-30) | 2=Med(31-70) | 3=High(71-100)  → 4
# enemy_hp_bin:     0=Dead | 1=Low(1-30) | 2=Med(31-70) | 3=High(71-100)  → 4
# player_honor_bin: 0=Dishonorable(<40) | 1=Neutral(40-60) | 2=Honorable(>60) → 3
STATE_DIMS = (4, 4, 3)


# =============================================================================
#  Helper utilities
# =============================================================================

def discretize_hp(hp: float) -> int:
    """Map a continuous HP value to a bin index."""
    if hp <= 0:
        return 0
    elif hp <= 30:
        return 1
    elif hp <= 70:
        return 2
    else:
        return 3


def discretize_honor(honor: float) -> int:
    """Map a continuous Honor score to a bin index."""
    if honor < 40:
        return 0   # Dishonorable
    elif honor <= 60:
        return 1   # Neutral
    else:
        return 2   # Honorable


# =============================================================================
#  Arena Environment
# =============================================================================

class ArenaEnv:
    """
    Custom Gladiator Arena environment for Q-Learning.

    State  : (player_hp_bin, enemy_hp_bin, player_honor_bin)
    Actions: 0=Light Attack | 1=Heavy Attack | 2=Block  (agent perspective)
    """

    # Base combat constants
    HP_MAX          = 100
    HONOR_MAX       = 100

    # Damage / effect tables
    LIGHT_DMG       = (8,  15)    # (min, max)
    HEAVY_DMG       = (18, 30)
    HONORABLE_DMG   = (10, 18)
    POISON_DMG_BASE = 12          # fixed per tick; counts as dishonorable
    DEFEND_BLOCK    = 0.5         # 50 % damage reduction for player on defend

    # Honor impact
    HONOR_PENALTY_POISON  = -20
    HONOR_BONUS_HONORABLE =  10

    def __init__(self):
        self.reset()

    # ------------------------------------------------------------------
    def reset(self) -> tuple:
        """Reset to a fresh episode and return the initial discrete state."""
        self.player_hp    = float(self.HP_MAX)
        self.enemy_hp     = float(self.HP_MAX)
        self.player_honor = float(np.random.randint(30, 71))  # start neutral-ish
        self.done         = False
        return self._get_state()

    # ------------------------------------------------------------------
    def _get_state(self) -> tuple:
        return (
            discretize_hp(self.player_hp),
            discretize_hp(self.enemy_hp),
            discretize_honor(self.player_honor),
        )

    # ------------------------------------------------------------------
    def _simulate_player_action(self) -> int:
        """
        Heuristic bot for the player:
          - Prefers Honorable Strike (60 %)
          - Defends when low HP (25 %)
          - Uses Poison occasionally (15 %) → makes player Dishonorable
        """
        if self.player_hp < 30:
            probs = [0.30, 0.50, 0.20]
        else:
            probs = [0.60, 0.25, 0.15]
        return int(np.random.choice(3, p=probs))

    # ------------------------------------------------------------------
    def step(self, agent_action: int) -> tuple:
        """
        Execute one combat round.

        Returns
        -------
        next_state : tuple
        reward     : float
        done       : bool
        info       : dict  (debug metadata)
        """
        assert not self.done, "Episode already finished — call reset()."

        player_action = self._simulate_player_action()
        reward        = 0.0
        info          = {
            "player_action": player_action,
            "agent_action" : agent_action,
        }

        # ── Player attacks enemy ─────────────────────────────────────
        player_dmg = 0.0
        if player_action == PLAYER_HONORABLE_STRIKE:
            player_dmg = float(np.random.randint(*self.HONORABLE_DMG))
            self.player_honor = min(self.HONOR_MAX,
                                    self.player_honor + self.HONOR_BONUS_HONORABLE)

        elif player_action == PLAYER_DEFEND:
            # No damage this round; block handled below
            pass

        elif player_action == PLAYER_DISHONORABLE_POISON:
            player_dmg = float(self.POISON_DMG_BASE)
            self.player_honor = max(0,
                                    self.player_honor + self.HONOR_PENALTY_POISON)

        # ── Agent acts ───────────────────────────────────────────────
        agent_dmg          = 0.0
        blocked_this_round = False

        if agent_action == AGENT_LIGHT_ATTACK:
            agent_dmg = float(np.random.randint(*self.LIGHT_DMG))

        elif agent_action == AGENT_HEAVY_ATTACK:
            agent_dmg = float(np.random.randint(*self.HEAVY_DMG))

            # ── KEY ML CONDITION ──────────────────────────────────────
            # If the player is acting dishonorably (honor_bin == 0),
            # reward the agent +15 for choosing Heavy Attack to punish them.
            if discretize_honor(self.player_honor) == 0:
                reward += 15.0
                info["dishonorable_punishment_bonus"] = True

        elif agent_action == AGENT_BLOCK:
            blocked_this_round = True   # absorb player damage

        # ── Apply damage ─────────────────────────────────────────────
        # Agent blocks → player damage halved (or nullified on full block)
        if blocked_this_round:
            player_dmg *= (1.0 - self.DEFEND_BLOCK)

        # Player defends → agent damage halved
        if player_action == PLAYER_DEFEND:
            agent_dmg *= (1.0 - self.DEFEND_BLOCK)

        self.enemy_hp  = max(0.0, self.enemy_hp  - player_dmg)
        self.player_hp = max(0.0, self.player_hp - agent_dmg)

        info["player_dmg"] = player_dmg
        info["agent_dmg"]  = agent_dmg

        # ── Terminal conditions ───────────────────────────────────────
        if self.enemy_hp <= 0:
            reward += -100.0    # Agent (enemy gladiator) lost
            self.done = True
            info["outcome"] = "agent_loss"

        elif self.player_hp <= 0:
            reward += 100.0     # Agent wins!
            self.done = True
            info["outcome"] = "agent_win"

        next_state = self._get_state()
        return next_state, reward, self.done, info


# =============================================================================
#  Q-Learning Training Loop
# =============================================================================

def train() -> np.ndarray:
    """Run Q-Learning for EPISODES episodes. Returns the trained Q-table."""

    env     = ArenaEnv()
    q_table = np.zeros(STATE_DIMS + (N_AGENT_ACTIONS,))  # shape (4,4,3,3)
    epsilon = EPSILON_START

    episode_rewards  = []
    wins             = 0
    losses           = 0

    print("=" * 60)
    print("  Echoes of the Arena — Q-Learning Training")
    print(f"  Episodes : {EPISODES:,}")
    print(f"  α (alpha): {ALPHA}   γ (gamma): {GAMMA}")
    print(f"  ε start  : {EPSILON_START}  →  ε end: {EPSILON_END}")
    print("=" * 60)

    for ep in range(EPISODES):
        state       = env.reset()
        total_reward = 0.0

        while True:
            # ── ε-greedy action selection ─────────────────────────────
            if np.random.rand() < epsilon:
                action = np.random.randint(N_AGENT_ACTIONS)   # explore
            else:
                action = int(np.argmax(q_table[state]))       # exploit

            # ── Step the environment ──────────────────────────────────
            next_state, reward, done, _ = env.step(action)

            # ── Bellman update ────────────────────────────────────────
            # Q(s,a) <- Q(s,a) + alpha * [r + gamma * max Q(s',a') - Q(s,a)]
            best_next_q = np.max(q_table[next_state])
            td_target   = reward + GAMMA * best_next_q * (not done)
            td_error    = td_target - q_table[state + (action,)]
            q_table[state + (action,)] += ALPHA * td_error

            total_reward += reward
            state         = next_state

            if done:
                if reward >= 100:
                    wins  += 1
                elif reward <= -100:
                    losses += 1
                break

        # ── Decay epsilon ─────────────────────────────────────────────
        epsilon = max(EPSILON_END, epsilon * EPSILON_DECAY)
        episode_rewards.append(total_reward)

        # ── Progress log every 1 000 episodes ────────────────────────
        if (ep + 1) % 1_000 == 0:
            recent   = episode_rewards[-1_000:]
            avg_r    = np.mean(recent)
            win_rate = wins  / (ep + 1) * 100
            print(f"  Episode {ep+1:>6,} | ε={epsilon:.4f} | "
                  f"Avg Reward (last 1k): {avg_r:+.2f} | "
                  f"Win rate: {win_rate:.1f}%")

    print("=" * 60)
    print(f"  Training complete!  Total wins: {wins:,}  Losses: {losses:,}")
    print("=" * 60)

    return q_table, episode_rewards


# =============================================================================
#  Visualization
# =============================================================================

def plot_training_curve(episode_rewards: list, save_path: str):
    """Plot rolling average reward and save to disk."""

    rewards  = np.array(episode_rewards)
    episodes = np.arange(1, len(rewards) + 1)

    # Rolling average
    kernel      = np.ones(ROLLING_WINDOW) / ROLLING_WINDOW
    rolling_avg = np.convolve(rewards, kernel, mode="valid")
    roll_ep     = np.arange(ROLLING_WINDOW, len(rewards) + 1)

    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    # Raw rewards (faint)
    ax.plot(episodes, rewards, color="#4a4e8c", alpha=0.25,
            linewidth=0.5, label="Episode reward")

    # Rolling average
    ax.plot(roll_ep, rolling_avg, color="#e94560", linewidth=2.2,
            label=f"Rolling avg (window={ROLLING_WINDOW})")

    # Zero baseline
    ax.axhline(0, color="#ffffff", linewidth=0.6, linestyle="--", alpha=0.4)

    # Cosmetics
    ax.set_title("Echoes of the Arena — Q-Learning Training Curve",
                 color="white", fontsize=14, fontweight="bold", pad=14)
    ax.set_xlabel("Episode", color="#aaaaaa", fontsize=11)
    ax.set_ylabel("Total Reward", color="#aaaaaa", fontsize=11)
    ax.tick_params(colors="#aaaaaa")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444466")

    legend = ax.legend(facecolor="#1a1a2e", edgecolor="#444466",
                       labelcolor="white", fontsize=10)

    # Annotation: mark convergence zone
    conv_x = len(rewards) * 0.7
    ax.axvspan(conv_x, len(rewards), alpha=0.07, color="#e94560",
               label="Convergence zone")
    ax.text(conv_x + len(rewards) * 0.01, ax.get_ylim()[1] * 0.85,
            "Convergence\nzone", color="#e94560", fontsize=8, alpha=0.8)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  Training curve saved → {save_path}")


# =============================================================================
#  Main
# =============================================================================

def main():
    # Ensure output directory exists
    os.makedirs("models", exist_ok=True)

    # Train
    q_table, episode_rewards = train()

    # Save Q-table
    q_table_path = os.path.join("models", "q_table.npy")
    np.save(q_table_path, q_table)
    print(f"  Q-table saved        → {q_table_path}  (shape: {q_table.shape})")

    # Plot & save training curve
    curve_path = os.path.join("models", "training_curve.png")
    plot_training_curve(episode_rewards, curve_path)

    # ── Print learned policy summary ──────────────────────────────────
    action_names = {0: "Light Attack", 1: "Heavy Attack", 2: "Block"}
    hp_bins      = {0: "Dead", 1: "Low HP", 2: "Med HP", 3: "High HP"}
    honor_bins   = {0: "Dishonorable", 1: "Neutral", 2: "Honorable"}

    print("\n  ── Learned Policy Snapshot (best action per state) ──")
    print(f"  {'Player HP':<12} {'Player Honor':<16} {'Agent HP':<10} → Best Action")
    print("  " + "-" * 60)
    for ph in range(1, 4):          # skip Dead
        for ho in range(3):
            for eh in range(1, 4):  # skip Dead
                state      = (ph, eh, ho)
                best_action = int(np.argmax(q_table[state]))
                print(f"  {hp_bins[ph]:<12} {honor_bins[ho]:<16} "
                      f"{hp_bins[eh]:<10} → {action_names[best_action]}")
    print()


if __name__ == "__main__":
    main()
