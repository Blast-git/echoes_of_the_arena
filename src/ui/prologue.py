# src/ui/prologue.py  — REDESIGNED v2
import pygame, math
from ui.base import *


STORY_LINES = [
    ("They called you Commander Kaelen —", C_GOLD),
    ("decorated soldier, sworn protector", C_WHITE),
    ("of the Verath Dominion.", C_WHITE),
    ("", None),
    ("A single forged document.", C_GOLD),
    ("A whisper in the right ear.", C_WHITE),
    ('"Commander Kaelen sold the eastern gate."', C_RED_BRIGHT),
    ("", None),
    ("Your sentence was not death.", C_WHITE),
    ("It was worse.", C_RED),
    ("", None),
    ("Debt-slavery to the Arena.", C_GOLD_PALE),
    ("", None),
    ("Forty-seven fights.", C_WHITE),
    ("The forty-eighth is different.", C_GOLD),
    ("", None),
    ("Standing at the far end of the pit —", C_WHITE),
    ("visor raised —", C_WHITE),
    ('is Garg "The Unbroken",', C_RED_BRIGHT),
    ("your former lieutenant.", C_WHITE),
    ("The man who framed you.", C_RED),
    ("", None),
    ("How you fight will decide everything.", C_GOLD),
]

GESTURE_GUIDE = [
    ("✊  CLOSED FIST",   "Honorable Strike — +10 dmg  +5 honour",   C_GREEN),
    ("✌  PEACE SIGN",    "Defend — blocks next hit  +3 honour",      C_BLUE),
    ("🖐  OPEN PALM",     "Use Potion — heals 25 HP  -2 honour",      C_CYAN),
    ("🤘  HORN SIGN",     "Dishonorable Poison — +15 dmg  -10 honour",C_RED),
]


class PrologueScreen(BaseScreen):
    def __init__(self, screen, gs, *fonts):
        super().__init__(screen, gs, *fonts)
        self.scroll_y   = float(HEIGHT + 40)
        self.text_speed = 55
        self.done       = False
        self._stars     = [(pygame.randint(0,WIDTH) if False else
                            __import__('random').randint(0,WIDTH),
                            __import__('random').randint(0,HEIGHT//2),
                            __import__('random').random()) for _ in range(80)]
        self._particles = []
        self._btn_rect  = None

    def _spawn_embers(self):
        import random
        for tx in [60, WIDTH-60]:
            if random.random() < 0.3:
                self._particles.append({
                    'x': float(tx + random.randint(-8,8)),
                    'y': float(110),
                    'vx': random.uniform(-0.4, 0.4),
                    'vy': random.uniform(-1.5, -0.5),
                    'life': random.randint(30,60),
                    'max_life': 60,
                    'col': random.choice([C_ORANGE, C_AMBER, C_RED_BRIGHT])
                })

    def update(self, dt, events):
        super().update(dt, events)
        self._spawn_embers()

        # Update particles
        for p in self._particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
        self._particles = [p for p in self._particles if p['life'] > 0]

        if not self.done:
            self.scroll_y -= self.text_speed * dt
            total_h = len(STORY_LINES) * 34 + 120
            if self.scroll_y < HEIGHT // 2 - total_h:
                self.done = True
                self.scroll_y = HEIGHT // 2 - total_h

        for e in events:
            if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.done = True
            if self.done and e.type == pygame.MOUSEBUTTONDOWN and self._btn_rect:
                if self._btn_rect.collidepoint(e.pos):
                    self.gs.game_phase = "Combat"

    def draw(self):
        s  = self.screen
        # Starfield background
        s.fill(C_VOID)
        for sx, sy, brightness in self._stars:
            flicker = brightness * (0.7 + 0.3 * math.sin(self.tick * 0.03 + sx))
            col = tuple(int(180 * flicker) for _ in range(3))
            s.set_at((sx, sy), col)

        # Torch glows
        for tx, ty in [(60, 110), (WIDTH-60, 110)]:
            flicker = 1.0 + 0.18 * math.sin(self.tick * 0.08 + tx)
            for r, a in [(int(160*flicker),7),(int(100*flicker),14),(int(55*flicker),26),(int(22*flicker),50)]:
                gs2 = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
                pygame.draw.circle(gs2, (*C_ORANGE, a), (r,r), r)
                s.blit(gs2, (tx-r, ty-r))
            # Flame
            for fi in range(3):
                foff = int(3*math.sin(self.tick*0.12+fi*1.3))
                fc = [(255,200,20),(255,100,10),(200,45,5)][fi]
                pygame.draw.ellipse(s, fc, (tx-7+foff, ty-28-fi*6, 14-fi*3, 24-fi*5))
            pygame.draw.rect(s, (60,35,15), (tx-3, ty-6, 6, 20))

        # Ember particles
        for p in self._particles:
            a = int(255 * p['life'] / p['max_life'])
            ps2 = pygame.Surface((4,4), pygame.SRCALPHA)
            pygame.draw.circle(ps2, (*p['col'], a), (2,2), 2)
            s.blit(ps2, (int(p['x'])-2, int(p['y'])-2))

        # --- TITLE ---
        # Decorative top bar
        pygame.draw.rect(s, C_GOLD_DIM, (0, 0, WIDTH, 3))
        for i in range(8):
            pygame.draw.rect(s, C_GOLD, (i*160+80, 0, 60, 3))

        draw_text(s, "⚔  ECHOES  OF  THE  ARENA  ⚔",
                  self.font_title, C_GOLD, WIDTH//2, 28, align="center", outline=True)
        draw_text(s, "— A TALE OF BLOOD, DEBT, AND BETRAYAL —",
                  self.font_small, C_GOLD_DIM, WIDTH//2, 88, align="center")

        # Ornamental divider
        pygame.draw.line(s, C_GOLD_DIM, (80, 118), (WIDTH-80, 118), 1)
        pygame.draw.rect(s, C_GOLD, (WIDTH//2-8, 114, 16, 8))
        pygame.draw.polygon(s, C_GOLD, [(WIDTH//2-16,118),(WIDTH//2+16,118),(WIDTH//2,126)])

        if not self.done:
            # Scrolling story text with vignette
            cy = int(self.scroll_y) + 140
            for text, col in STORY_LINES:
                if text and col:
                    # Alpha by distance from center
                    dist = abs(cy + 17 - HEIGHT//2)
                    fade = max(0, min(255, 255 - max(0, dist - HEIGHT//3) * 2))
                    surf_t = self.font_body.render(text, True, col)
                    surf_t.set_alpha(fade)
                    r = surf_t.get_rect(centerx=WIDTH//2, top=cy)
                    s.blit(surf_t, r)
                cy += 34

            # Bottom fade gradient
            for i in range(80):
                a = int(255 * (i/80) ** 1.5)
                line_s = pygame.Surface((WIDTH, 1), pygame.SRCALPHA)
                line_s.fill((0,0,0,a))
                s.blit(line_s, (0, HEIGHT-80+i))

            # Skip hint
            pulse = int(180 + 60 * math.sin(self.tick * 0.06))
            draw_text(s, "[ CLICK OR PRESS SPACE TO SKIP ]",
                      self.font_tiny, (pulse, pulse-20, pulse-40),
                      WIDTH//2, HEIGHT-30, align="center", shadow=False)
        else:
            # Dim overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            s.blit(overlay, (0, 0))

            draw_text(s, "⚔  ECHOES  OF  THE  ARENA  ⚔",
                      self.font_title, C_GOLD, WIDTH//2, 28, align="center", outline=True)
            pygame.draw.line(s, C_GOLD_DIM, (80, 100), (WIDTH-80, 100), 1)
            pygame.draw.rect(s, C_GOLD, (WIDTH//2-8, 96, 16, 8))

            # Gesture guide panel
            px, py, pw, ph = 90, 118, WIDTH-180, 280
            draw_panel(s, px, py, pw, ph, border=C_GOLD_DIM, alpha=230)

            # Panel title with ornament
            pygame.draw.line(s, C_GOLD_DIM, (px+20, py+44), (px+pw-20, py+44), 1)
            draw_text(s, "GESTURE  CONTROLS", self.font_badge, C_GOLD,
                      px+pw//2, py+14, align="center")
            pygame.draw.rect(s, C_GOLD, (px+pw//2-30, py+44, 60, 2))

            for i, (gesture, desc, col) in enumerate(GESTURE_GUIDE):
                gy = py + 56 + i * 54
                # Row panel
                draw_panel(s, px+16, gy, pw-32, 44, border=col, alpha=180)
                # Gesture icon + name
                draw_text(s, gesture, self.font_body, col, px+36, gy+12, outline=True)
                # Separator
                pygame.draw.line(s, col, (px+220, gy+8), (px+220, gy+36), 1)
                # Description
                draw_text(s, desc, self.font_small, C_WHITE, px+236, gy+14, shadow=False)
                # Colour accent bar on left
                pygame.draw.rect(s, col, (px+16, gy, 4, 44))

            # Enter button — pulsing
            pulse2 = int(55 + 20 * math.sin(self.tick * 0.08))
            btn_col = (C_GOLD[0], C_GOLD[1], min(255, C_GOLD[2]+pulse2))
            self._btn_rect = draw_button(
                s, "⚔   ENTER  THE  ARENA   ⚔",
                self.font_badge, WIDTH//2-200, py+ph+20, 400, 56,
                border=C_GOLD, text_col=btn_col, glow_col=C_GOLD)

            # Bottom ornament
            pygame.draw.line(s, C_GOLD_DIM, (80, HEIGHT-30), (WIDTH-80, HEIGHT-30), 1)
            draw_text(s, "May honour guide your blade",
                      self.font_tiny, C_GOLD_DIM, WIDTH//2, HEIGHT-24,
                      align="center", shadow=False)
