# src/app.py
# Echoes of the Arena — Grand Integration (Phase 5)
# Quad-Model architecture wired into a seamless game loop:
#   CV (gestures) → Tabular QL (Garg) → DQN Overseer → RAG Merchant

import os
import sys
import streamlit as st

# ── Ensure src/ is on the path when running from project root ────────────────
sys.path.insert(0, os.path.dirname(__file__))

from state_manager import init_game_state, reset_game_state

# ════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Echoes of the Arena",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ════════════════════════════════════════════════════════════════════════════
# CSS — Dark Medieval AAA Theme
# ════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=MedievalSharp&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');

#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }

/* ── Global dark background ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #0a0806 !important;
    color: #e0e0e0;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0e0a08 0%, #080604 100%) !important;
    border-right: 1px solid #1a1208 !important;
}

/* ── Hide all Streamlit padding/gaps in combat ── */
[data-testid="stMainBlockContainer"] {
    padding-top: 0.5rem !important;
    padding-left: 0.5rem !important;
    padding-right: 0.5rem !important;
}
.block-container { padding: 0.5rem 1rem !important; max-width: 100% !important; }

/* ── Typography ── */
h1, h2, h3 {
    font-family: 'MedievalSharp', serif !important;
    color: #d4af37 !important;
    text-shadow: 0 0 18px rgba(212,175,55,0.5), 0 0 40px rgba(212,175,55,0.2);
    letter-spacing: 3px;
}
p, li, span, label, div {
    font-family: 'Crimson Text', serif !important;
    color: #e0e0e0;
    font-size: 1.05rem;
}

/* ── Buttons — stone block style ── */
.stButton > button {
    font-family: 'MedievalSharp', serif !important;
    background: linear-gradient(180deg, #2a2016 0%, #1a1208 100%) !important;
    color: #d4af37 !important;
    border: 1px solid #5a4020 !important;
    border-radius: 2px !important;
    padding: 0.55rem 1.5rem !important;
    font-size: 0.85rem !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    box-shadow: 0 3px 10px rgba(0,0,0,0.8), inset 0 1px 0 rgba(212,175,55,0.1) !important;
    transition: all 0.15s ease !important;
    clip-path: polygon(4px 0%, 100% 0%, calc(100% - 4px) 100%, 0% 100%);
}
.stButton > button:hover {
    background: linear-gradient(180deg, #3a2e1a 0%, #2a1e0e 100%) !important;
    border-color: #d4af37 !important;
    color: #ffd700 !important;
    box-shadow: 0 3px 20px rgba(212,175,55,0.4), inset 0 1px 0 rgba(212,175,55,0.2) !important;
    transform: translateY(-2px) !important;
}
.stButton > button:active { transform: translateY(0px) !important; }
.stButton > button:disabled { opacity: 0.25 !important; cursor: not-allowed !important; }

/* ── Progress bars — styled as HP bars ── */
[data-testid="stProgress"] > div {
    background: #111 !important;
    border: 1px solid #222 !important;
    border-radius: 2px !important;
    height: 14px !important;
}
[data-testid="stProgress"] > div > div {
    border-radius: 2px !important;
    box-shadow: 0 0 8px currentColor !important;
}

/* ── Combat panels ── */
.combat-panel {
    background: linear-gradient(180deg, #120e0a 0%, #0a0806 100%);
    border: 1px solid #2a1e10;
    border-radius: 2px;
    padding: 1rem 1.2rem;
    min-height: 260px;
    position: relative;
    box-shadow: inset 0 0 30px rgba(0,0,0,0.5);
}
.combat-panel::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
}
.combat-panel-player::before { background: linear-gradient(90deg, transparent, #2e7d32, transparent); }
.combat-panel-enemy::before  { background: linear-gradient(90deg, transparent, #b71c1c, transparent); }

/* ── Webcam area ── */
.webcam-placeholder {
    background: linear-gradient(180deg, #0e0a08, #080604);
    border: 1px solid #1a1208;
    border-radius: 2px;
    text-align: center;
    padding: 2rem 1rem;
    color: #333;
    font-family: 'Crimson Text', serif;
    font-size: 0.9rem;
}

/* ── webrtc widget ── */
[data-testid="stVerticalBlock"] video {
    border-radius: 2px !important;
    border: 1px solid #2a1e10 !important;
    box-shadow: 0 0 20px rgba(0,0,0,0.8) !important;
}

/* ── Prologue / story text ── */
.prologue-text {
    font-family: 'Crimson Text', serif !important;
    font-size: 1.2rem; line-height: 2rem; color: #c0a882;
    background: linear-gradient(180deg, #120e0a 0%, #0a0806 100%);
    border-left: 3px solid #d4af37;
    padding: 1.5rem 2rem; border-radius: 0 2px 2px 0;
    margin: 1rem 0 2rem 0;
    box-shadow: inset 0 0 40px rgba(0,0,0,0.4);
}
.prologue-text em { color: #d4af37; font-style: italic; }

/* ── Gesture badge ── */
.gesture-badge {
    background: linear-gradient(180deg, #1a1208, #0e0a06);
    border: 1px solid #d4af37;
    border-radius: 2px;
    padding: 0.5rem 1rem;
    font-family: 'MedievalSharp', serif;
    color: #d4af37;
    font-size: 0.9rem;
    text-align: center;
    margin: 0.4rem 0;
    box-shadow: 0 0 12px rgba(212,175,55,0.2);
    letter-spacing: 1px;
}

/* ── Round badge ── */
.round-badge {
    font-family: 'MedievalSharp', serif;
    color: #d4af37;
    font-size: 1rem;
    text-align: center;
    letter-spacing: 4px;
    margin-bottom: 0.4rem;
    text-shadow: 0 0 12px rgba(212,175,55,0.4);
}

/* ── Overseer event ── */
.overseer-event {
    background: linear-gradient(90deg, #1a1008, transparent);
    border-left: 3px solid #d4af37;
    padding: 0.6rem 1rem;
    border-radius: 0 2px 2px 0;
    font-style: italic;
    color: #d4af37;
    text-shadow: 0 0 8px rgba(212,175,55,0.4);
}

/* ── HR dividers ── */
hr {
    border: none !important;
    border-top: 1px solid #1a1208 !important;
    margin: 0.5rem 0 !important;
}

/* ── Metrics in sidebar ── */
[data-testid="stMetric"] {
    background: linear-gradient(180deg, #120e0a, #0a0806);
    border: 1px solid #1a1208;
    border-radius: 2px;
    padding: 0.5rem 1rem;
}
[data-testid="stMetricValue"] { color: #d4af37 !important; font-family: 'MedievalSharp', serif !important; }
[data-testid="stMetricLabel"] { color: #666 !important; font-size: 0.75rem !important; }

/* ── Chat messages (Tavern) ── */
[data-testid="stChatMessage"] {
    background: linear-gradient(180deg, #120e0a, #0e0a08) !important;
    border: 1px solid #1a1208 !important;
    border-radius: 2px !important;
}

/* ── Text input ── */
.stTextInput input {
    background: #0e0a08 !important;
    border: 1px solid #2a1e10 !important;
    border-radius: 2px !important;
    color: #c0a882 !important;
    font-family: 'Crimson Text', serif !important;
}
.stTextInput input:focus {
    border-color: #d4af37 !important;
    box-shadow: 0 0 8px rgba(212,175,55,0.3) !important;
}

/* ── Info / warning / success boxes ── */
[data-testid="stAlert"] {
    border-radius: 2px !important;
    border-left-width: 3px !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0a0806; }
::-webkit-scrollbar-thumb { background: #2a1e10; border-radius: 2px; }

/* ── Expanders ── */
[data-testid="stExpander"] {
    background: #0e0a08 !important;
    border: 1px solid #1a1208 !important;
    border-radius: 2px !important;
}
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# STATE INIT
# ════════════════════════════════════════════════════════════════════════════
init_game_state()

# ════════════════════════════════════════════════════════════════════════════
# LAZY MODEL LOADERS  — cached so models load only once per session
# ════════════════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner="Loading CV combat module...")
def load_cv():
    from cv_combat import capture_gesture_frame, get_gesture_effects
    return capture_gesture_frame, get_gesture_effects


@st.cache_resource(show_spinner="Loading Garg's combat brain...")
def load_gladiator():
    from rl_gladiator import get_garg_action
    return get_garg_action


@st.cache_resource(show_spinner="Loading Narrative Overseer...")
def load_overseer():
    from rl_overseer import get_overseer_action_safe
    return get_overseer_action_safe


@st.cache_resource(show_spinner="Loading RAG Merchant pipeline...")
def load_merchant():
    from rag_merchant import chat_with_merchant
    return chat_with_merchant


# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR — persistent across all phases
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚔️ War Record")
    st.metric("Round",   st.session_state.round_count)
    st.metric("Honour",  f"{st.session_state.honor_score} / 100")
    st.metric("Potions", f"🧪 {st.session_state.potions}")
    st.divider()

    if st.session_state.story_path:
        color = "#2e7d32" if "Rebel" in str(st.session_state.story_path) else "#b71c1c"
        st.markdown(
            f"<p style='color:{color};font-family:MedievalSharp,serif;'>"
            f"⚔️ {st.session_state.story_path}</p>",
            unsafe_allow_html=True,
        )

    if st.session_state.action_history:
        with st.expander("📜 Combat Log", expanded=False):
            for entry in st.session_state.action_history[-8:]:
                st.write(f"• {entry}")

    st.divider()
    if st.button("🔄 Restart", use_container_width=True):
        reset_game_state()
        st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# PHASE ROUTER
# ════════════════════════════════════════════════════════════════════════════
phase = st.session_state.game_phase


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  PROLOGUE                                                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝
if phase == "Prologue":

    st.markdown(
        "<h1 style='text-align:center;letter-spacing:6px;'>⚔ ECHOES OF THE ARENA ⚔</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center;color:#555;font-size:0.9rem;letter-spacing:3px;'>"
        "— A TALE OF BLOOD, DEBT, AND BETRAYAL —</p>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    st.markdown("""
<div class="prologue-text">
<p>They called you <em>Commander Kaelen</em> — decorated soldier, sworn protector of the
Verath Dominion. You built your reputation blade by blade across a dozen campaigns.
You trusted your men. You trusted your lieutenant.</p>
<p>You were wrong.</p>
<p>A single forged document. A whisper in the right ear. Six words to the High Council:
<em>"Commander Kaelen sold the eastern gate."</em>
Your medals were stripped in a public square. Your sentence was not death. It was worse.</p>
<p><em>Debt-slavery to the Arena.</em></p>
<p>Forty-seven fights. But the <em>forty-eighth</em> is different.</p>
<p>Standing at the far end of the pit — visor raised so you can see his face —
is <em>Garg "The Unbroken"</em>, your former lieutenant. The man who framed you.</p>
<p>High Senator Vane watches from his gilded box. He expects a spectacle.</p>
<p style='color:#d4af37;font-size:1.3rem;text-align:center;margin-top:1.5rem;'>
The gates are opening, Commander. How you fight will decide everything.
</p>
</div>
""", unsafe_allow_html=True)

    st.info(
        "🖐 **Gesture Controls** — hold in front of webcam, then click Lock In Move:\n\n"
        "✊ **Closed Fist** = Honorable Strike (10 dmg, +5 honour)  |  "
        "✌ **Peace Sign** = Defend (blocks next hit, +3 honour)\n\n"
        "🖐 **Open Palm** = Use Potion (heals 25 HP, -2 honour)  |  "
        "🤘 **Horn Sign** = Dishonorable Poison (15 dmg, -10 honour)"
    )

    st.markdown("---")
    _, col_c, _ = st.columns([2, 1, 2])
    with col_c:
        if st.button("⚔  Enter the Arena", use_container_width=True):
            st.session_state.game_phase = "Combat"
            st.rerun()


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  COMBAT                                                                  ║
# ╚══════════════════════════════════════════════════════════════════════════╝
elif phase == "Combat":

    # ── Lazy imports for this phase only ─────────────────────────────────
    try:
        from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
        import av
        WEBRTC_AVAILABLE = True
    except ImportError:
        WEBRTC_AVAILABLE = False

    from combat_ui import render_arena, ARENA_CSS
    import streamlit.components.v1 as components

    st.markdown(
        f"<div class='round-badge'>— ROUND {st.session_state.round_count} —</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<h2 style='text-align:center;'>⚔  The Pit of Verath  ⚔</h2>",
                unsafe_allow_html=True)
    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════
    # ANIMATED ARENA — rendered inside an iframe to bypass Streamlit's
    # HTML sanitiser which strips <div>, base64 <img>, and position CSS.
    # st.components.v1.html() renders a full unsanitised HTML document.
    # ════════════════════════════════════════════════════════════════════
    hero_state   = st.session_state.get("hero_anim_state",  "idle")
    enemy_state  = st.session_state.get("enemy_anim_state", "idle")
    overseer_ev  = st.session_state.get("overseer_anim",    "")
    last_pdmg    = st.session_state.get("last_player_dmg",  0)
    last_edmg    = st.session_state.get("last_enemy_dmg",   0)
    last_heal_v  = st.session_state.get("last_heal_val",    0)
    last_action  = st.session_state.get("last_action_label","")

    arena_body = render_arena(
        player_hp       = st.session_state.player_hp,
        enemy_hp        = st.session_state.enemy_hp,
        hero_state      = hero_state,
        enemy_state     = enemy_state,
        overseer_event  = overseer_ev,
        last_action     = last_action,
        last_player_dmg = last_pdmg,
        last_enemy_dmg  = last_edmg,
        last_heal       = last_heal_v,
    )

    full_arena_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=MedievalSharp&family=Crimson+Text:wght@400;600&display=swap" rel="stylesheet">
{ARENA_CSS}
<style>body {{ margin:0; padding:0; background:#0e0e0e; overflow:hidden; }}</style>
</head>
<body>{arena_body}</body>
</html>"""

    components.html(full_arena_html, height=360, scrolling=False)

    # Reset animation state after one render
    if hero_state  != "idle": st.session_state.hero_anim_state  = "idle"
    if enemy_state != "idle": st.session_state.enemy_anim_state = "idle"
    if overseer_ev:           st.session_state.overseer_anim    = ""
    if last_pdmg:             st.session_state.last_player_dmg  = 0
    if last_edmg:             st.session_state.last_enemy_dmg   = 0
    if last_heal_v:           st.session_state.last_heal_val    = 0
    if last_action:           st.session_state.last_action_label= ""

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════
    # THREE-COLUMN LAYOUT: stats | webcam | stats
    # ════════════════════════════════════════════════════════════════════
    col_player, col_cam, col_enemy = st.columns([3, 4, 3])

    # ── PLAYER stats ─────────────────────────────────────────────────────
    with col_player:
        st.markdown("<div class='combat-panel combat-panel-player'>", unsafe_allow_html=True)
        st.markdown("### 🛡 Kaelen")
        st.markdown("<p style='color:#888;font-size:0.85rem;'>Former Commander · Debt-Slave</p>",
                    unsafe_allow_html=True)
        st.markdown(f"**HP: {st.session_state.player_hp} / 100**")
        st.progress(max(0, st.session_state.player_hp) / 100)
        st.markdown("<br>", unsafe_allow_html=True)
        potion_icons = "🧪 " * st.session_state.potions + "🫙 " * (3 - st.session_state.potions)
        st.markdown(f"**Potions:** {potion_icons}")
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='color:#888;font-size:0.85rem;margin-bottom:4px;'>"
            f"Honour: {st.session_state.honor_score}/100</div>",
            unsafe_allow_html=True,
        )
        st.progress(st.session_state.honor_score / 100)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── WEBCAM — live streamlit-webrtc feed ───────────────────────────────
    with col_cam:

        if WEBRTC_AVAILABLE:
            # ── WebRTC Video Processor with MediaPipe ─────────────────────
            import threading

            class GestureProcessor(VideoProcessorBase):
                def __init__(self):
                    self.gesture = None
                    self.lock    = threading.Lock()
                    try:
                        import mediapipe as mp
                        from cv_combat import classify_gesture
                        self._hands    = mp.solutions.hands.Hands(
                            static_image_mode=False,
                            max_num_hands=1,
                            min_detection_confidence=0.70,
                            min_tracking_confidence=0.60,
                        )
                        self._mp_draw  = mp.solutions.drawing_utils
                        self._mp_hands = mp.solutions.hands
                        self._classify = classify_gesture
                        self._ready    = True
                    except Exception:
                        self._ready = False

                def recv(self, frame):
                    import cv2 as _cv2
                    import numpy as _np
                    img = frame.to_ndarray(format="bgr24")
                    img = _cv2.flip(img, 1)

                    if self._ready:
                        rgb = _cv2.cvtColor(img, _cv2.COLOR_BGR2RGB)
                        rgb.flags.writeable = False
                        results = self._hands.process(rgb)
                        rgb.flags.writeable = True

                        if results.multi_hand_landmarks:
                            hl = results.multi_hand_landmarks[0]
                            self._mp_draw.draw_landmarks(
                                img, hl, self._mp_hands.HAND_CONNECTIONS)
                            detected = self._classify(hl.landmark)
                            with self.lock:
                                self.gesture = detected

                            if detected:
                                _cv2.putText(img, detected, (20, 50),
                                    _cv2.FONT_HERSHEY_DUPLEX, 0.9,
                                    (50, 200, 50), 2, _cv2.LINE_AA)
                        else:
                            with self.lock:
                                self.gesture = None

                    return av.VideoFrame.from_ndarray(img, format="bgr24")

            # RTC config — STUN server for NAT traversal
            rtc_config = RTCConfiguration({
                "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
            })

            ctx = webrtc_streamer(
                key="gesture-cam",
                video_processor_factory=GestureProcessor,
                rtc_configuration=rtc_config,
                media_stream_constraints={"video": True, "audio": False},
                async_processing=True,
            )

            # ── Read gesture from the processor thread ────────────────────
            # webrtc runs in a background thread — session_state cannot be
            # written from there. Instead we read on every Streamlit rerun
            # via a dedicated "Capture Current Gesture" button, which forces
            # a rerun and pulls the latest value from the processor lock.
            live_gesture = None
            if ctx.video_processor:
                with ctx.video_processor.lock:
                    live_gesture = ctx.video_processor.gesture

            # Show capture button only when camera is running
            if ctx.state.playing:
                if st.button("📸 Capture Current Gesture",
                             use_container_width=True,
                             help="Click when your gesture is clearly visible"):
                    if live_gesture:
                        st.session_state.last_gesture = live_gesture
                        st.rerun()
                    else:
                        st.warning("No gesture detected — hold your hand clearly in frame.")

                # Also show what's currently visible in the feed
                if live_gesture:
                    st.markdown(
                        f"<div style='text-align:center;color:#4caf50;"
                        f"font-family:MedievalSharp,serif;font-size:0.9rem;"
                        f"margin-top:4px;'>👁 Live: {live_gesture}</div>",
                        unsafe_allow_html=True,
                    )

        else:
            # ── Fallback: single-frame capture button ─────────────────────
            st.warning("streamlit-webrtc not installed. Using snapshot mode.\n"
                       "Run: `pip install streamlit-webrtc aiortc`")
            if st.button("📷 Capture Gesture", use_container_width=True):
                try:
                    capture_fn, _ = load_cv()
                    g, frame_bgr  = capture_fn(camera_index=0)
                    if frame_bgr is not None:
                        import cv2
                        _, buf = cv2.imencode(".jpg", frame_bgr)
                        st.session_state.last_frame_bytes = buf.tobytes()
                        st.session_state.last_gesture     = g
                except Exception as e:
                    st.error(f"Camera error: {e}")

            if st.session_state.get("last_frame_bytes"):
                st.image(st.session_state.last_frame_bytes,
                         channels="BGR", use_container_width=True)

        # ── Gesture badge ─────────────────────────────────────────────────
        dg = st.session_state.last_gesture
        if dg:
            gesture_colors = {
                "Honorable Strike":    "#4caf50",
                "Defend":              "#2196f3",
                "Use Potion":          "#00bcd4",
                "Dishonorable Poison": "#e53935",
            }
            gc = gesture_colors.get(dg, "#d4af37")
            st.markdown(
                f"<div class='gesture-badge' style='border-color:{gc};color:{gc};'>"
                f"🖐 DETECTED: {dg}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='gesture-badge' style='opacity:0.35;'>"
                "Show a hand gesture to the camera...</div>",
                unsafe_allow_html=True,
            )

        # ── Garg's last taunt ─────────────────────────────────────────────
        if st.session_state.last_taunt:
            st.markdown(
                f"<p style='text-align:center;color:#cf6679;font-style:italic;"
                f"font-size:1.0rem;margin-top:0.5rem;'>"
                f"💬 &ldquo;{st.session_state.last_taunt}&rdquo;</p>"
                f"<p style='text-align:center;color:#555;font-size:0.75rem;'>"
                f"— Garg \"The Unbroken\"</p>",
                unsafe_allow_html=True,
            )

    # ── ENEMY stats ───────────────────────────────────────────────────────
    with col_enemy:
        st.markdown("<div class='combat-panel combat-panel-enemy'>", unsafe_allow_html=True)
        st.markdown("### 💀 Garg")
        st.markdown("<p style='color:#888;font-size:0.85rem;'>\"The Unbroken\" · Traitor</p>",
                    unsafe_allow_html=True)
        st.markdown(f"**HP: {st.session_state.enemy_hp} / 100**")
        st.progress(max(0, st.session_state.enemy_hp) / 100)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<p style='color:#888;font-size:0.85rem;'>"
            "Garg watches your every move.<br>He has not forgotten what you were.</p>",
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<h3 style='text-align:center;'>Choose Your Move, Commander</h3>",
                unsafe_allow_html=True)

    btn1, btn2, btn3, btn4 = st.columns(4)

    with btn1:
        lock_btn = st.button(
            "⚔ Lock In Gesture",
            use_container_width=True,
            disabled=not st.session_state.last_gesture,
            help="Lock in the gesture shown above to execute your move",
        )
    with btn2:
        potion_btn = st.button(
            "🧪 Use Potion",
            use_container_width=True,
            disabled=st.session_state.potions <= 0,
        )
    with btn3:
        text_attack = st.text_input(
            "Type a move",
            placeholder="No webcam? Describe your attack...",
            label_visibility="collapsed",
        )
    with btn4:
        text_btn = st.button("⚔ Strike", use_container_width=True,
                             disabled=not text_attack)

    # ══════════════════════════════════════════════════════════════════════
    # GESTURE LOCK-IN  — full quad-model pipeline
    # ══════════════════════════════════════════════════════════════════════
    def run_combat_round(gesture_used: str | None, text_used: str | None):
        """Full combat round: player → Garg QL → Overseer DQN → win/loss."""

        # ── 1. PLAYER ACTION ─────────────────────────────────────────────
        if gesture_used:
            try:
                _, get_effects = load_cv()
                effects = get_effects(gesture_used)
            except Exception:
                effects = {"honor_delta": 0, "player_damage": 10,
                           "heals": False, "blocks": False}

            if effects["heals"]:
                if st.session_state.potions > 0:
                    heal = min(25, 100 - st.session_state.player_hp)
                    st.session_state.player_hp        = min(100, st.session_state.player_hp + heal)
                    st.session_state.potions         -= 1
                    st.session_state.honor_score      = max(0, st.session_state.honor_score - 2)
                    st.session_state.last_heal_val    = heal
                    st.session_state.hero_anim_state  = "heal"
                    log = f"Used Potion — healed {heal} HP"
                else:
                    log = "No potions left!"
                    effects["blocks"] = False
                    st.session_state.hero_anim_state = "idle"
            else:
                dmg = effects["player_damage"]
                st.session_state.enemy_hp         = max(0, st.session_state.enemy_hp - dmg)
                st.session_state.honor_score      = max(0, min(100,
                    st.session_state.honor_score + effects["honor_delta"]))
                st.session_state.last_enemy_dmg   = dmg
                st.session_state.hero_anim_state  = "poison" if gesture_used == "Dishonorable Poison" else "attack"
                st.session_state.enemy_anim_state = "hurt"
                log = f"{gesture_used} — dealt {dmg} dmg to Garg"

            blocked = effects.get("blocks", False)
            if blocked:
                st.session_state.hero_anim_state  = "idle"
                st.session_state.enemy_anim_state = "idle"
        else:
            dmg = 12
            st.session_state.enemy_hp         = max(0, st.session_state.enemy_hp - dmg)
            st.session_state.last_enemy_dmg   = dmg
            st.session_state.hero_anim_state  = "attack"
            st.session_state.enemy_anim_state = "hurt"
            log     = f"{text_used} — dealt {dmg} dmg"
            blocked = False

        st.session_state.last_action_label = log
        st.session_state.action_history.append(
            f"R{st.session_state.round_count} [Kaelen]: {log}"
        )

        # Early win
        if st.session_state.enemy_hp <= 0:
            st.session_state.enemy_hp         = 0
            st.session_state.enemy_anim_state = "dead"
            st.session_state.game_phase       = "Aftermath"
            return

        # ── 2. GARG COUNTER-ATTACK ────────────────────────────────────────
        if not blocked:
            try:
                get_garg_action = load_gladiator()
                garg = get_garg_action(
                    st.session_state.player_hp,
                    st.session_state.enemy_hp,
                    st.session_state.round_count,
                )
                st.session_state.player_hp        = max(0, st.session_state.player_hp - garg["damage"])
                st.session_state.last_taunt       = garg["taunt"]
                st.session_state.last_player_dmg  = garg["damage"]
                st.session_state.enemy_anim_state = "attack"
                st.session_state.hero_anim_state  = "hurt"
                st.session_state.action_history.append(
                    f"R{st.session_state.round_count} [Garg]: {garg['name']} — {garg['damage']} dmg"
                )
            except Exception:
                st.session_state.player_hp        = max(0, st.session_state.player_hp - 10)
                st.session_state.last_taunt       = "Garg snarls and drives his elbow into your ribs!"
                st.session_state.last_player_dmg  = 10
                st.session_state.hero_anim_state  = "hurt"
        else:
            st.session_state.last_taunt = "Garg's blow glances off your guard — he looks surprised."
            st.session_state.action_history.append(
                f"R{st.session_state.round_count} [Kaelen]: BLOCKED Garg's attack!"
            )

        # ── 3. OVERSEER INTERVENTION ──────────────────────────────────────
        try:
            get_overseer = load_overseer()
            overseer = get_overseer(
                st.session_state.player_hp,
                st.session_state.honor_score,
                min(st.session_state.round_count, 10),
            )
            if overseer["action_id"] == 1:
                st.session_state.player_hp      = min(100, st.session_state.player_hp + 10)
                st.session_state.overseer_event = overseer["description"]
                st.session_state.overseer_anim  = "buff"
                st.toast(f"✨ {overseer['description']}", icon="⚡")
            elif overseer["action_id"] == 2:
                st.session_state.player_hp      = max(0, st.session_state.player_hp - 10)
                st.session_state.overseer_event = overseer["description"]
                st.session_state.overseer_anim  = "nerf"
                st.toast(f"💀 {overseer['description']}", icon="⚡")
            else:
                st.session_state.overseer_anim  = ""
                st.session_state.overseer_event = ""
        except Exception:
            st.session_state.overseer_anim  = ""
            st.session_state.overseer_event = ""

        # ── 4. ADVANCE & WIN/LOSS CHECK ───────────────────────────────────
        st.session_state.round_count += 1
        st.session_state.last_gesture = None

        if st.session_state.player_hp <= 0:
            st.session_state.player_hp       = 0
            st.session_state.hero_anim_state = "dead"
            st.session_state.game_phase      = "Defeated"

        if st.session_state.enemy_hp <= 0:
            st.session_state.enemy_hp         = 0
            st.session_state.enemy_anim_state = "dead"
            st.session_state.game_phase       = "Aftermath"

    # ── Button handlers ───────────────────────────────────────────────────
    if lock_btn and st.session_state.last_gesture:
        run_combat_round(gesture_used=st.session_state.last_gesture, text_used=None)
        st.rerun()

    if potion_btn and st.session_state.potions > 0:
        heal = min(25, 100 - st.session_state.player_hp)
        st.session_state.player_hp   = min(100, st.session_state.player_hp + heal)
        st.session_state.potions    -= 1
        st.session_state.honor_score = max(0, st.session_state.honor_score - 2)
        st.session_state.action_history.append(
            f"R{st.session_state.round_count}: Used Potion — healed {heal} HP"
        )
        st.rerun()

    if text_btn and text_attack:
        run_combat_round(gesture_used=None, text_used=text_attack)
        st.rerun()


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  AFTERMATH                                                               ║
# ╚══════════════════════════════════════════════════════════════════════════╝
elif phase == "Aftermath":

    st.markdown("<h1 style='text-align:center;'>⚔ Aftermath ⚔</h1>",
                unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("""
<div class="prologue-text">
<p>Garg collapses to one knee, his weapon skidding across the sand.
The crowd is deafening. High Senator Vane rises from his gilded box, one hand raised.</p>
<p>His thumb turns slowly downward.</p>
<p><em>He demands you finish it.</em></p>
<p>But you have survived forty-eight fights. You did not survive by doing what Senators demanded.</p>
<p style='color:#d4af37;font-size:1.2rem;text-align:center;margin-top:1rem;'>
What does Kaelen do?
</p>
</div>
""", unsafe_allow_html=True)

    with st.expander("📜 Full Fight Record", expanded=False):
        for entry in st.session_state.action_history:
            st.write(f"• {entry}")
        st.write(f"**Final Honour: {st.session_state.honor_score}/100**")

    st.markdown("---")
    col_rebel, col_merc = st.columns(2)

    with col_rebel:
        st.markdown("""
<div class="prologue-text" style="border-left-color:#2e7d32;">
<p>You lower your blade. Garg looks up — confused, then ashamed.
The crowd murmurs. A few, in the back rows, begin to cheer.</p>
<p style='color:#4caf50;'>⚔ The Rebel Path opens.</p>
</div>
""", unsafe_allow_html=True)
        honour_ok = st.session_state.honor_score > 50
        if not honour_ok:
            st.warning(
                f"⚠ Honour too low ({st.session_state.honor_score}/100). "
                f"You must have > 50 honour to spare Garg."
            )
        if st.button("🕊 Spare Garg — Rebel Path",
                     disabled=not honour_ok, use_container_width=True):
            st.session_state.story_path  = "Rebel Path"
            st.session_state.game_phase  = "Merchant_Negotiation"
            st.rerun()

    with col_merc:
        st.markdown("""
<div class="prologue-text" style="border-left-color:#b71c1c;">
<p>You drive the final blow. The crowd erupts.
Senator Vane smiles and sits back down. Business as usual.</p>
<p style='color:#ef5350;'>🗡 The Mercenary Path opens.</p>
</div>
""", unsafe_allow_html=True)
        if st.button("💀 Kill Garg — Mercenary Path", use_container_width=True):
            st.session_state.story_path  = "Mercenary Path"
            st.session_state.honor_score = max(0, st.session_state.honor_score - 20)
            st.session_state.game_phase  = "Merchant_Negotiation"
            st.rerun()


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  DEFEATED                                                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝
elif phase == "Defeated":

    st.markdown("<h1 style='text-align:center;color:#b71c1c;'>💀 Defeated 💀</h1>",
                unsafe_allow_html=True)
    st.markdown("""
<div class="prologue-text" style="border-left-color:#b71c1c;">
<p>Garg's boot presses against your throat. The crowd's chant is deafening.</p>
<p>The Overseer signals. <em>It is over.</em></p>
<p>You are dragged from the sand. Kaelen's forty-eighth fight. His last.</p>
</div>
""", unsafe_allow_html=True)

    with st.expander("📜 Your Final Moves", expanded=True):
        for entry in st.session_state.action_history:
            st.write(f"• {entry}")

    st.markdown("---")
    if st.button("🔄 Rise Again, Commander"):
        reset_game_state()
        st.rerun()


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  MERCHANT NEGOTIATION  (RAG + FAISS + Ollama)                           ║
# ╚══════════════════════════════════════════════════════════════════════════╝
elif phase == "Merchant_Negotiation":

    st.markdown("<h1 style='text-align:center;'>🍻 The Broken Shield Tavern</h1>",
                unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center;color:#555;letter-spacing:2px;font-size:0.9rem;'>"
        "— WHERE SECRETS ARE CURRENCY —</p>",
        unsafe_allow_html=True,
    )

    if st.session_state.story_path == "Rebel Path":
        st.success("⚔ You walk in as someone who showed mercy. Word travels fast in this city.")
    else:
        st.warning("🗡 You enter with fresh blood on your hands. Everyone in the room notices.")

    st.markdown("---")

    # Merchant intro scene — shown once
    if not st.session_state.chat_history:
        st.markdown("""
<div class="prologue-text">
<p>Behind the bar, <em>Aldric</em> polishes a goblet without looking up.
His eyes finally meet yours — and harden instantly.</p>
<p><em>"I know who you are, friend. I know what happened in that pit today.
Choose your words with me very carefully."</em></p>
<p style='color:#888;font-size:0.95rem;'>
🎯 <strong>Goal:</strong> Negotiate to purchase Aldric's legendary blade for 500 gold.
Your honour score and chosen path affect his prices and willingness to deal.
</p>
</div>
""", unsafe_allow_html=True)

    # ── Chat history ──────────────────────────────────────────────────────
    for msg in st.session_state.chat_history:
        avatar = "🧑" if msg["role"] == "user" else "🧙"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])
            if msg.get("deal_status") and msg["deal_status"] != "ongoing":
                color = "#2e7d32" if msg["deal_status"] == "success" else "#b71c1c"
                label = "✅ DEAL STRUCK" if msg["deal_status"] == "success" else "❌ DEAL BROKEN"
                st.markdown(
                    f"<p style='color:{color};font-size:0.85rem;font-weight:bold;'>{label}</p>",
                    unsafe_allow_html=True,
                )

    # ── Deal concluded — show exit button ─────────────────────────────────
    deal_done = st.session_state.merchant_deal_status in ("success", "failed")

    if deal_done:
        if st.session_state.merchant_deal_status == "success":
            st.success("✅ Aldric reaches under the counter and produces the legendary blade.")
        else:
            st.error("❌ Aldric slams a hand on the counter. 'Get out before I call the guards.'")

        if st.button("Leave the Tavern — Enter the Epilogue ➡️"):
            st.session_state.game_phase = "Epilogue"
            st.rerun()

    else:
        # ── Live chat input ───────────────────────────────────────────────
        player_input = st.chat_input("Speak to Aldric...")

        if player_input:
            st.session_state.chat_history.append({
                "role": "user", "content": player_input,
            })
            with st.chat_message("user", avatar="🧑"):
                st.write(player_input)

            # RAG pipeline call
            with st.chat_message("assistant", avatar="🧙"):
                with st.spinner("Aldric considers his words carefully..."):
                    try:
                        chat_fn = load_merchant()
                        result  = chat_fn(
                            user_message=player_input,
                            current_honor=st.session_state.honor_score,
                            story_path=st.session_state.story_path,
                        )
                        dialogue    = result.get("dialogue",    "Aldric stares at you in silence.")
                        deal_status = result.get("deal_status", "ongoing")
                    except Exception as e:
                        dialogue    = f"Aldric mutters something inaudible. ({e})"
                        deal_status = "ongoing"

                st.write(dialogue)

                if deal_status != "ongoing":
                    color = "#2e7d32" if deal_status == "success" else "#b71c1c"
                    label = "✅ DEAL STRUCK" if deal_status == "success" else "❌ DEAL BROKEN"
                    st.markdown(
                        f"<p style='color:{color};font-weight:bold;'>{label}</p>",
                        unsafe_allow_html=True,
                    )

            st.session_state.chat_history.append({
                "role":        "assistant",
                "content":     dialogue,
                "deal_status": deal_status,
            })

            if deal_status in ("success", "failed"):
                st.session_state.merchant_deal_status = deal_status

            st.rerun()


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  EPILOGUE                                                                ║
# ╚══════════════════════════════════════════════════════════════════════════╝
elif phase == "Epilogue":

    st.markdown("<h1 style='text-align:center;'>📜 Epilogue</h1>", unsafe_allow_html=True)
    st.markdown("---")

    if st.session_state.story_path == "Rebel Path":
        st.markdown("""
<div class="prologue-text">
<p>The blade feels right in your hand. Heavier than it looks.
The kind of weight that means something.</p>
<p>Word has spread through the lower districts overnight.
A Commander returned from the dead. A man who spared his enemy
when the entire Dominion demanded blood.</p>
<p>By morning, three former soldiers are waiting outside the tavern door.</p>
<p><em>The rebellion has its symbol.</em></p>
<p style='color:#4caf50;font-size:1.3rem;text-align:center;margin-top:1.5rem;'>
⚔ REBEL PATH — COMPLETE
</p>
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown("""
<div class="prologue-text">
<p>You tuck the blade into your belt and walk out without looking back.</p>
<p>Senator Vane's messenger is waiting for you in the alley outside.
A new contract. A bigger arena. More gold than you have ever seen.</p>
<p>You used to fight for justice. Now you fight for whoever pays most.</p>
<p><em>At least you're honest about it now.</em></p>
<p style='color:#ef5350;font-size:1.3rem;text-align:center;margin-top:1.5rem;'>
🗡 MERCENARY PATH — COMPLETE
</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ⚔ Final Record")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rounds Fought",  st.session_state.round_count)
    c2.metric("Final Honour",   st.session_state.honor_score)
    c3.metric("Story Path",     st.session_state.story_path or "—")
    c4.metric("Potions Left",   st.session_state.potions)

    st.markdown("---")
    if st.button("🔄 Play Again — A New Story"):
        reset_game_state()
        st.rerun()
