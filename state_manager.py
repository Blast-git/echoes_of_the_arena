# src/state_manager.py
# Echoes of the Arena — Master State Initializer
# All st.session_state keys are defined here and nowhere else.

import streamlit as st


def init_game_state():
    """
    Initialize every session state key for Echoes of the Arena.
    Safe to call on every rerun — existing values are never overwritten.
    """

    # ── Combat Stats ────────────────────────────────────────────────────────
    if "player_hp" not in st.session_state:
        st.session_state.player_hp = 100          # Kaelen's current HP

    if "enemy_hp" not in st.session_state:
        st.session_state.enemy_hp = 100           # Garg's current HP

    if "potions" not in st.session_state:
        st.session_state.potions = 3              # Healing potions remaining

    if "round_count" not in st.session_state:
        st.session_state.round_count = 1          # Current combat round

    # ── Morality / Honour Tracking ───────────────────────────────────────────
    if "honor_score" not in st.session_state:
        st.session_state.honor_score = 50         # 0 = Dishonorable, 100 = Noble

    # ── Narrative State ──────────────────────────────────────────────────────
    if "story_path" not in st.session_state:
        st.session_state.story_path = None        # 'Rebel Path' | 'Mercenary Path' | None

    if "merchant_deal_status" not in st.session_state:
        st.session_state.merchant_deal_status = "ongoing"  # 'ongoing' | 'deal' | 'refused'

    if "action_history" not in st.session_state:
        st.session_state.action_history = []      # List of player attack descriptions

    if "combat_log" not in st.session_state:
        st.session_state.combat_log = []          # Full round-by-round log dicts

    if "rumor" not in st.session_state:
        st.session_state.rumor = ""               # Garg's fabricated rumor string

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []        # Aldric merchant conversation

    if "last_taunt" not in st.session_state:
        st.session_state.last_taunt = ""          # Garg's last spoken taunt

    if "last_gesture" not in st.session_state:
        st.session_state.last_gesture = None      # Most recent webcam gesture detected

    if "sentiment_label" not in st.session_state:
        st.session_state.sentiment_label = None   # 'aggressive' | 'fearful' | 'neutral'

    # ── App Routing ──────────────────────────────────────────────────────────
    if "game_phase" not in st.session_state:
        st.session_state.game_phase = "Prologue"  # 'Prologue'|'Combat'|'Aftermath'|'Tavern'


def reset_game_state():
    """
    Wipe all session state keys to restart the game from scratch.
    Call this when the player clicks 'Play Again'.
    """
    for key in list(st.session_state.keys()):
        del st.session_state[key]
