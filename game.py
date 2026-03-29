# src/game.py
# Echoes of the Arena — PyGame Main Entry Point
# Run with: python src/game.py

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import pygame
import pygame.gfxdraw
import threading
import time

# ── Screen constants ──────────────────────────────────────────────────────────
WIDTH, HEIGHT = 1280, 720
FPS           = 60
TITLE         = "Echoes of the Arena"

# ── Colour palette ────────────────────────────────────────────────────────────
C_BG          = ( 10,  8,  6)
C_BG2         = ( 18, 12,  8)
C_GOLD        = (212,175, 55)
C_GOLD_DIM    = (140,110, 30)
C_RED         = (183, 28, 28)
C_GREEN       = ( 46,125, 50)
C_WHITE       = (224,224,224)
C_GREY        = ( 80, 70, 60)
C_DARK        = ( 25, 18, 12)
C_DARKER      = ( 14, 10,  8)
C_SAND        = ( 90, 65, 35)
C_SAND2       = ( 60, 42, 20)
C_BLOOD       = ( 80,  0,  0)
C_BLUE        = ( 33,150,243)
C_CYAN        = (  0,188,212)
C_ORANGE      = (255,140,  0)

pygame.init()
pygame.font.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
pygame.display.set_caption(TITLE)
clock  = pygame.time.Clock()

# ── Font loader ───────────────────────────────────────────────────────────────
def load_font(size, bold=False):
    """Load system serif font with fallback."""
    for name in ["Georgia", "Palatino Linotype", "Times New Roman",
                 "serif", "freesans"]:
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            continue
    return pygame.font.Font(None, size)

FONT_TITLE   = load_font(52, bold=True)
FONT_HEADING = load_font(36, bold=True)
FONT_BODY    = load_font(22)
FONT_SMALL   = load_font(17)
FONT_BADGE   = load_font(20, bold=True)
FONT_HUD     = load_font(24, bold=True)
FONT_TINY    = load_font(14)

# ── Asset loader ──────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(BASE_DIR, "..", "assets", "images")

def load_sprite(name, size=(100, 100)):
    path = os.path.join(ASSETS_DIR, f"{name}.png")
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(img, size)
    except Exception:
        # Coloured rectangle fallback
        surf = pygame.Surface(size, pygame.SRCALPHA)
        colour = C_GREEN if "hero" in name else C_RED
        pygame.draw.rect(surf, colour, (0, 0, *size), border_radius=6)
        # Draw a stick figure silhouette
        cx, cy = size[0]//2, size[1]//2
        pygame.draw.circle(surf, C_WHITE, (cx, cy-30), 12)
        pygame.draw.line(surf, C_WHITE, (cx, cy-18), (cx, cy+20), 3)
        pygame.draw.line(surf, C_WHITE, (cx-18, cy-5), (cx+18, cy-5), 3)
        pygame.draw.line(surf, C_WHITE, (cx, cy+20), (cx-14, cy+44), 3)
        pygame.draw.line(surf, C_WHITE, (cx, cy+20), (cx+14, cy+44), 3)
        return surf

SPRITE_HERO       = load_sprite("hero",       (110, 140))
SPRITE_HERO_HURT  = load_sprite("hero_hurt",  (110, 140))
SPRITE_ENEMY      = load_sprite("enemy",      (110, 140))
SPRITE_ENEMY_HURT = load_sprite("enemy_hurt", (110, 140))

# ── Drawing helpers ───────────────────────────────────────────────────────────

def draw_text(surf, text, font, colour, x, y, align="left", shadow=True):
    """Render text with optional drop shadow."""
    if shadow:
        s = font.render(text, True, (0, 0, 0))
        r = s.get_rect()
        if   align == "center": r.centerx = x
        elif align == "right":  r.right   = x
        else:                   r.left    = x
        r.top = y + 2
        surf.blit(s, r)
    s = font.render(text, True, colour)
    r = s.get_rect()
    if   align == "center": r.centerx = x
    elif align == "right":  r.right   = x
    else:                   r.left    = x
    r.top = y
    surf.blit(s, r)
    return r


def draw_bar(surf, x, y, w, h, value, max_val, colour, bg=C_DARK, border=C_GREY):
    """Draw a game-style HP / honour bar."""
    pygame.draw.rect(surf, bg,     (x, y, w, h), border_radius=2)
    pct = max(0, min(1, value / max_val))
    if pct > 0:
        fw = int((w - 2) * pct)
        pygame.draw.rect(surf, colour, (x+1, y+1, fw, h-2), border_radius=2)
        # Shine line
        pygame.draw.rect(surf, tuple(min(255,c+60) for c in colour),
                         (x+1, y+1, fw, 3), border_radius=2)
    pygame.draw.rect(surf, border,  (x, y, w, h), 1, border_radius=2)


def draw_panel(surf, x, y, w, h, border_colour=C_GOLD_DIM, alpha=200):
    """Draw a semi-transparent dark panel."""
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    panel.fill((*C_DARKER, alpha))
    surf.blit(panel, (x, y))
    pygame.draw.rect(surf, border_colour, (x, y, w, h), 1, border_radius=3)
    # Top accent line
    pygame.draw.rect(surf, border_colour, (x, y, w, 2), border_radius=2)


def draw_button(surf, text, font, x, y, w, h, active=True,
                border=C_GOLD_DIM, text_col=C_GOLD):
    """Draw a stone-block style button. Returns rect."""
    rect = pygame.Rect(x, y, w, h)
    if active:
        pygame.draw.rect(surf, C_DARK,  rect, border_radius=2)
        pygame.draw.rect(surf, border,  rect, 1, border_radius=2)
        # Hover glow
        mx, my = pygame.mouse.get_pos()
        if rect.collidepoint(mx, my):
            glow = pygame.Surface((w, h), pygame.SRCALPHA)
            glow.fill((*C_GOLD, 25))
            surf.blit(glow, (x, y))
            pygame.draw.rect(surf, C_GOLD, rect, 1, border_radius=2)
    else:
        pygame.draw.rect(surf, C_DARKER, rect, border_radius=2)
        pygame.draw.rect(surf, C_GREY,   rect, 1, border_radius=2)
        text_col = C_GREY

    tw = font.render(text, True, text_col).get_width()
    draw_text(surf, text, font, text_col, x + w//2 - tw//2, y + h//2 - font.get_height()//2,
              shadow=active)
    return rect


def draw_arena_background(surf):
    """Draw the arena pit background — crowd, sand, torches."""
    # Sky / upper darkness
    surf.fill(C_BG)

    # Crowd — repeating silhouette pattern
    for cx in range(0, WIDTH, 18):
        h_var = 28 + (cx * 7 % 22)
        pygame.draw.ellipse(surf, (20, 14, 9),
                            (cx - 6, 55 - h_var, 14, h_var))

    # Crowd tier line
    pygame.draw.rect(surf, (35, 24, 14), (0, 55, WIDTH, 8))

    # Arena floor gradient (sand)
    for i in range(200):
        t     = i / 200
        r     = int(C_BG[0]  + (C_SAND2[0]  - C_BG[0])  * t)
        g     = int(C_BG[1]  + (C_SAND2[1]  - C_BG[1])  * t)
        b     = int(C_BG[2]  + (C_SAND2[2]  - C_BG[2])  * t)
        pygame.draw.line(surf, (r, g, b), (0, HEIGHT - 200 + i), (WIDTH, HEIGHT - 200 + i))

    # Blood stains on sand
    for (bx, by, bw, bh) in [(520, HEIGHT-145, 80, 22),
                               (720, HEIGHT-160, 55, 16),
                               (300, HEIGHT-135, 65, 18)]:
        s = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (*C_BLOOD, 80), (0, 0, bw, bh))
        surf.blit(s, (bx, by))

    # Torch glows (left and right)
    for tx, ty in [(60, 120), (WIDTH - 60, 120)]:
        for r, a in [(120, 12), (80, 20), (45, 35), (20, 60)]:
            s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*C_ORANGE, a), (r, r), r)
            surf.blit(s, (tx - r, ty - r))

    # VS text (large, faint centre)
    vs_surf = FONT_TITLE.render("VS", True, (*C_GOLD_DIM, 35))
    # Can't set alpha on a font surface directly — use a surface
    vs_bg   = pygame.Surface(vs_surf.get_size(), pygame.SRCALPHA)
    vs_bg.blit(vs_surf, (0, 0))
    vs_bg.set_alpha(35)
    screen.blit(vs_bg, (WIDTH//2 - vs_bg.get_width()//2, HEIGHT//2 - 80))


# ── Floating text particles ───────────────────────────────────────────────────
class FloatingText:
    def __init__(self, text, x, y, colour, font=None):
        self.text   = text
        self.x      = float(x)
        self.y      = float(y)
        self.colour = colour
        self.font   = font or FONT_HEADING
        self.alpha  = 255
        self.vy     = -1.8
        self.life   = 90   # frames

    def update(self):
        self.y     += self.vy
        self.vy    *= 0.97
        self.life  -= 1
        self.alpha  = max(0, int(255 * self.life / 90))

    def draw(self, surf):
        if self.alpha <= 0:
            return
        s = self.font.render(self.text, True, self.colour)
        s.set_alpha(self.alpha)
        surf.blit(s, (int(self.x) - s.get_width()//2, int(self.y)))

    @property
    def dead(self):
        return self.life <= 0


# ── Input box ─────────────────────────────────────────────────────────────────
class InputBox:
    def __init__(self, x, y, w, h, placeholder=""):
        self.rect        = pygame.Rect(x, y, w, h)
        self.text        = ""
        self.placeholder = placeholder
        self.active      = False
        self.cursor_tick = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key not in (pygame.K_RETURN, pygame.K_ESCAPE):
                if len(self.text) < 80:
                    self.text += event.unicode
        return self.active and event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN

    def draw(self, surf):
        self.cursor_tick += 1
        border = C_GOLD if self.active else C_GREY
        pygame.draw.rect(surf, C_DARKER, self.rect, border_radius=2)
        pygame.draw.rect(surf, border,   self.rect, 1, border_radius=2)

        if self.text:
            draw_text(surf, self.text, FONT_BODY, C_WHITE,
                      self.rect.x + 10, self.rect.y + self.rect.h//2 - FONT_BODY.get_height()//2)
        else:
            draw_text(surf, self.placeholder, FONT_BODY, C_GREY,
                      self.rect.x + 10, self.rect.y + self.rect.h//2 - FONT_BODY.get_height()//2,
                      shadow=False)
        # Cursor
        if self.active and self.cursor_tick % 60 < 30:
            tw = FONT_BODY.render(self.text, True, C_WHITE).get_width() if self.text else 0
            cx = self.rect.x + 10 + tw + 2
            cy = self.rect.y + 6
            pygame.draw.rect(surf, C_GOLD, (cx, cy, 2, self.rect.h - 12))

    def clear(self):
        self.text = ""


# ── Gesture camera thread ─────────────────────────────────────────────────────
class GestureCamera:
    """Runs webcam + MediaPipe in a background thread."""
    def __init__(self):
        self.gesture    = None
        self.frame      = None   # BGR numpy array
        self.lock       = threading.Lock()
        self._running   = False
        self._thread    = None

    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _loop(self):
        import cv2
        import mediapipe as mp
        from cv_combat import classify_gesture

        hands = mp.solutions.hands.Hands(
            static_image_mode=False, max_num_hands=1,
            min_detection_confidence=0.70, min_tracking_confidence=0.60)
        mp_draw = mp.solutions.drawing_utils
        cap     = cv2.VideoCapture(0)

        while self._running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                continue
            frame = cv2.flip(frame, 1)
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            result = hands.process(rgb)
            rgb.flags.writeable = True

            detected = None
            if result.multi_hand_landmarks:
                hl = result.multi_hand_landmarks[0]
                mp_draw.draw_landmarks(frame, hl, mp.solutions.hands.HAND_CONNECTIONS)
                detected = classify_gesture(hl.landmark)
                if detected:
                    cv2.putText(frame, detected, (10, 32),
                                cv2.FONT_HERSHEY_DUPLEX, 0.7, (50, 220, 50), 2)

            with self.lock:
                self.gesture = detected
                self.frame   = frame

            time.sleep(0.03)   # ~30 fps for gesture cam

        cap.release()

    def get_gesture(self):
        with self.lock:
            return self.gesture

    def get_pygame_surface(self, size=(220, 165)):
        """Convert latest BGR frame to a pygame surface."""
        with self.lock:
            frame = self.frame
        if frame is None:
            return None
        import cv2
        import numpy as np
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb = cv2.resize(frame_rgb, size)
        return pygame.surfarray.make_surface(frame_rgb.swapaxes(0, 1))


# ── Game state (thin wrapper around Python dict) ──────────────────────────────
class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.player_hp           = 100
        self.enemy_hp            = 100
        self.potions             = 3
        self.round_count         = 1
        self.honor_score         = 50
        self.story_path          = None
        self.merchant_deal_status= "ongoing"
        self.game_phase          = "Prologue"
        self.action_history      = []
        self.chat_history        = []
        self.rumor               = ""
        self.last_taunt          = ""
        self.last_gesture        = None
        self.sentiment_label     = None
        self.overseer_event      = ""


# ════════════════════════════════════════════════════════════════════════════
# SCREENS
# ════════════════════════════════════════════════════════════════════════════

from ui.prologue  import PrologueScreen
from ui.combat    import CombatScreen
from ui.aftermath import AftermathScreen
from ui.tavern    import TavernScreen
from ui.epilogue  import EpilogueScreen

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    gs      = GameState()
    cam     = GestureCamera()
    cam.start()

    screens = {
        "Prologue":  PrologueScreen(screen, gs, FONT_TITLE, FONT_HEADING,
                                    FONT_BODY, FONT_SMALL, FONT_BADGE, FONT_HUD, FONT_TINY),
        "Combat":    CombatScreen(screen, gs, cam, FONT_TITLE, FONT_HEADING,
                                   FONT_BODY, FONT_SMALL, FONT_BADGE, FONT_HUD, FONT_TINY),
        "Aftermath": AftermathScreen(screen, gs, FONT_TITLE, FONT_HEADING,
                                      FONT_BODY, FONT_SMALL, FONT_BADGE, FONT_HUD, FONT_TINY),
        "Tavern":    TavernScreen(screen, gs, FONT_TITLE, FONT_HEADING,
                                   FONT_BODY, FONT_SMALL, FONT_BADGE, FONT_HUD, FONT_TINY),
        "Epilogue":  EpilogueScreen(screen, gs, FONT_TITLE, FONT_HEADING,
                                     FONT_BODY, FONT_SMALL, FONT_BADGE, FONT_HUD, FONT_TINY),
    }

    running = True
    while running:
        dt     = clock.tick(FPS) / 1000.0
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()

        current = screens.get(gs.game_phase)
        if current:
            current.update(dt, events)
            current.draw()
        else:
            gs.game_phase = "Prologue"

        pygame.display.flip()

    cam.stop()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
