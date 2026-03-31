# src/cv_combat.py
# Echoes of the Arena — Hand Gesture Combat Controller
# Uses OpenCV + MediaPipe to capture webcam frames and classify
# the player's hand gesture into one of 4 combat actions.
#
# Gesture → Combat Action mapping:
#   Closed Fist      → 'Honorable Strike'
#   Peace Sign       → 'Defend'
#   Open Palm        → 'Use Potion'
#   Horn Sign        → 'Dishonorable Poison'

import cv2
import mediapipe as mp
import numpy as np

# ════════════════════════════════════════════════════════════════════════════
# MEDIAPIPE INITIALISATION
# ════════════════════════════════════════════════════════════════════════════

mp_hands   = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Hands instance — kept module-level so it is initialised once.
# min_detection_confidence / min_tracking_confidence tuned for live gameplay.
hands_detector = mp_hands.Hands(
    static_image_mode=False,       # video stream, not individual images
    max_num_hands=1,               # track only the dominant hand
    min_detection_confidence=0.70,
    min_tracking_confidence=0.60,
)

# ════════════════════════════════════════════════════════════════════════════
# LANDMARK INDEX CONSTANTS  (MediaPipe hand landmark IDs)
# ════════════════════════════════════════════════════════════════════════════
#
#  Wrist          : 0
#  Thumb          : 1  2  3  4   (CMC → MCP → IP → TIP)
#  Index finger   : 5  6  7  8   (MCP → PIP → DIP → TIP)
#  Middle finger  : 9 10 11 12
#  Ring finger    :13 14 15 16
#  Pinky finger   :17 18 19 20
#  Palm center is approximated as the midpoint of landmarks 0, 5, 9, 13, 17

WRIST       = 0

THUMB_TIP   = 4
INDEX_TIP   = 8
MIDDLE_TIP  = 12
RING_TIP    = 16
PINKY_TIP   = 20

INDEX_MCP   = 5
MIDDLE_MCP  = 9
RING_MCP    = 13
PINKY_MCP   = 17

INDEX_PIP   = 6
MIDDLE_PIP  = 10
RING_PIP    = 14
PINKY_PIP   = 18


# ════════════════════════════════════════════════════════════════════════════
# MATHS HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _landmark_to_array(landmark) -> np.ndarray:
    """Convert a single MediaPipe NormalizedLandmark to a (3,) numpy array."""
    return np.array([landmark.x, landmark.y, landmark.z], dtype=np.float32)


def _euclidean(a: np.ndarray, b: np.ndarray) -> float:
    """Euclidean distance between two 3-D landmark positions."""
    return float(np.linalg.norm(a - b))


def _palm_center(lm_list) -> np.ndarray:
    """
    Approximate palm center as the mean position of the five MCP / wrist
    anchor landmarks: Wrist (0), Index MCP (5), Middle MCP (9),
    Ring MCP (13), Pinky MCP (17).
    """
    anchors = [WRIST, INDEX_MCP, MIDDLE_MCP, RING_MCP, PINKY_MCP]
    points  = np.stack([_landmark_to_array(lm_list[i]) for i in anchors])
    return points.mean(axis=0)


def _is_finger_extended(tip_idx: int, pip_idx: int, lm_list, palm: np.ndarray,
                         extension_ratio: float = 1.6) -> bool:
    """
    A finger is considered *extended* when its tip is significantly farther
    from the palm center than its PIP (proximal inter-phalangeal) joint is.

    Ratio threshold of 1.6 means the tip must be 60 % farther than the PIP
    to count as extended — robust to slight hand tilts.
    """
    tip_dist = _euclidean(_landmark_to_array(lm_list[tip_idx]), palm)
    pip_dist = _euclidean(_landmark_to_array(lm_list[pip_idx]), palm)

    if pip_dist < 1e-6:          # guard against degenerate case
        return False
    return (tip_dist / pip_dist) > extension_ratio


# ════════════════════════════════════════════════════════════════════════════
# CORE GESTURE CLASSIFIER
# ════════════════════════════════════════════════════════════════════════════

def classify_gesture(landmarks) -> str | None:
    """
    Classify a MediaPipe hand landmark list into one of 4 combat gestures.

    Parameters
    ----------
    landmarks : mediapipe.framework.formats.landmark_pb2.NormalizedLandmarkList
        The `.landmark` attribute of a detected hand result
        (i.e. `results.multi_hand_landmarks[0].landmark`).

    Returns
    -------
    str | None
        One of:
          'Honorable Strike'    — Closed Fist
          'Defend'              — Peace Sign  (Index + Middle extended)
          'Use Potion'          — Open Palm   (all 5 fingers extended)
          'Dishonorable Poison' — Horn Sign   (Index + Pinky extended)
          None                  — gesture unrecognised
    """
    lm = landmarks          # shorthand
    palm = _palm_center(lm)

    # ── Per-finger extension flags ───────────────────────────────────────
    index_up  = _is_finger_extended(INDEX_TIP,  INDEX_PIP,  lm, palm)
    middle_up = _is_finger_extended(MIDDLE_TIP, MIDDLE_PIP, lm, palm)
    ring_up   = _is_finger_extended(RING_TIP,   RING_PIP,   lm, palm)
    pinky_up  = _is_finger_extended(PINKY_TIP,  PINKY_PIP,  lm, palm)

    # ── Closed Fist ───────────────────────────────────────────────────────
    # All four fingers folded (none extended).
    # Additional check: all fingertips are close to the palm center.
    if not index_up and not middle_up and not ring_up and not pinky_up:
        # Verify all tips are genuinely close to palm (not just ambiguous)
        tip_indices = [INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]
        avg_tip_dist = np.mean([
            _euclidean(_landmark_to_array(lm[t]), palm) for t in tip_indices
        ])
        # Palm diameter proxy: wrist → middle MCP distance
        palm_diam = _euclidean(
            _landmark_to_array(lm[WRIST]),
            _landmark_to_array(lm[MIDDLE_MCP]),
        )
        if palm_diam > 1e-6 and (avg_tip_dist / palm_diam) < 1.2:
            return "Honorable Strike"

    # ── Open Palm ─────────────────────────────────────────────────────────
    # All four fingers extended (thumb is excluded — hard to track reliably).
    if index_up and middle_up and ring_up and pinky_up:
        return "Use Potion"

    # ── Peace Sign ────────────────────────────────────────────────────────
    # Index AND Middle extended; Ring AND Pinky folded.
    if index_up and middle_up and not ring_up and not pinky_up:
        return "Defend"

    # ── Horn Sign ─────────────────────────────────────────────────────────
    # Index AND Pinky extended; Middle AND Ring folded.
    if index_up and not middle_up and not ring_up and pinky_up:
        return "Dishonorable Poison"

    # ── Unrecognised ──────────────────────────────────────────────────────
    return None


# ════════════════════════════════════════════════════════════════════════════
# FRAME CAPTURE  (called once per Streamlit rerun from app.py)
# ════════════════════════════════════════════════════════════════════════════

def capture_gesture_frame(camera_index: int = 0) -> tuple[str | None, np.ndarray | None]:
    """
    Open the webcam, grab a single frame, run MediaPipe hand detection,
    annotate the frame, and return the detected gesture + annotated BGR image.

    Parameters
    ----------
    camera_index : int
        OpenCV camera device index (default 0 = built-in webcam).

    Returns
    -------
    gesture : str | None
        The classified gesture string, or None if no hand / gesture detected.
    annotated_frame : np.ndarray | None
        BGR image (H×W×3) with landmark overlay drawn, or None on capture failure.

    Notes
    -----
    This function opens and releases the camera on every call so it is safe
    to invoke from a Streamlit button callback without holding a resource lock.
    For a smoother live feed, use `run_gesture_stream()` in a separate thread.
    """
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        return None, None

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        return None, None

    # Mirror the frame for natural left/right feel
    frame = cv2.flip(frame, 1)

    # MediaPipe requires RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb_frame.flags.writeable = False
    results = hands_detector.process(rgb_frame)
    rgb_frame.flags.writeable = True

    gesture = None
    annotated = frame.copy()

    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]   # first hand only

        # Draw skeleton overlay
        mp_drawing.draw_landmarks(
            annotated,
            hand_landmarks,
            mp_hands.HAND_CONNECTIONS,
            mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style(),
        )

        # Classify gesture
        gesture = classify_gesture(hand_landmarks.landmark)

        # Overlay gesture label on frame
        if gesture:
            label_color = _gesture_color(gesture)
            cv2.putText(
                annotated,
                gesture,
                (20, 50),
                cv2.FONT_HERSHEY_DUPLEX,
                1.1,
                label_color,
                2,
                cv2.LINE_AA,
            )

    return gesture, annotated


def _gesture_color(gesture: str) -> tuple[int, int, int]:
    """Return BGR color for the on-frame gesture label."""
    colors = {
        "Honorable Strike":    (50,  200, 50),    # green
        "Defend":              (50,  150, 255),   # blue
        "Use Potion":          (50,  220, 220),   # cyan
        "Dishonorable Poison": (50,   50, 220),   # red
    }
    return colors.get(gesture, (200, 200, 200))


# ════════════════════════════════════════════════════════════════════════════
# HONOUR DELTA  — maps each gesture to its honour impact
# ════════════════════════════════════════════════════════════════════════════

GESTURE_HONOR_DELTA: dict[str, int] = {
    "Honorable Strike":    +5,   # fighting clean raises honour
    "Defend":              +3,   # defensive play is honourable
    "Use Potion":          -2,   # minor — relying on potions is a crutch
    "Dishonorable Poison": -10,  # using poison is deeply dishonourable
}

GESTURE_PLAYER_DAMAGE: dict[str, int] = {
    "Honorable Strike":    10,   # solid base damage
    "Defend":               0,   # no attack damage — absorbs next hit
    "Use Potion":           0,   # heals; no attack
    "Dishonorable Poison":  15,  # higher damage but costs honour
}


def get_gesture_effects(gesture: str) -> dict:
    """
    Return the game-mechanic effects for a given gesture string.

    Returns
    -------
    dict with keys:
        honor_delta   (int)  : change to apply to honor_score
        player_damage (int)  : damage dealt to enemy HP
        heals         (bool) : whether this gesture triggers a potion use
        blocks        (bool) : whether this gesture blocks incoming damage
    """
    return {
        "honor_delta":   GESTURE_HONOR_DELTA.get(gesture, 0),
        "player_damage": GESTURE_PLAYER_DAMAGE.get(gesture, 0),
        "heals":         gesture == "Use Potion",
        "blocks":        gesture == "Defend",
    }


# ════════════════════════════════════════════════════════════════════════════
# QUICK TEST  (run directly: python cv_combat.py)
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Starting gesture test — press 'q' to quit.")
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = hands_detector.process(rgb)
        rgb.flags.writeable = True

        gesture = None
        if results.multi_hand_landmarks:
            hl = results.multi_hand_landmarks[0]
            mp_drawing.draw_landmarks(
                frame, hl, mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style(),
            )
            gesture = classify_gesture(hl.landmark)

        label = gesture if gesture else "No gesture detected"
        color = _gesture_color(gesture) if gesture else (180, 180, 180)
        cv2.putText(frame, label, (20, 50),
                    cv2.FONT_HERSHEY_DUPLEX, 1.1, color, 2, cv2.LINE_AA)

        cv2.imshow("Echoes of the Arena — Gesture Test", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
