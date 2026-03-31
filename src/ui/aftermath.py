# src/ui/aftermath.py  — REDESIGNED v2
import pygame, math, random, threading
from ui.base import *


class AftermathScreen(BaseScreen):
    def __init__(self, screen, gs, *fonts):
        super().__init__(screen, gs, *fonts)
        self._generating = False
        self._rumor_done = False
        self._particles  = []
        self._anim_in    = 0   # entrance animation counter

    def _spawn_embers(self):
        for tx in [60, WIDTH-60]:
            if random.random() < 0.25:
                self._particles.append({
                    'x': float(tx + random.randint(-10,10)),
                    'y': float(85),
                    'vx': random.uniform(-0.5,0.5),
                    'vy': random.uniform(-1.8,-0.6),
                    'life': random.randint(25,55),
                    'ml': 55,
                    'col': random.choice([C_ORANGE,C_AMBER,C_RED_BRIGHT])
                })

    def update(self, dt, events):
        super().update(dt, events)
        self._anim_in = min(60, self._anim_in + 1)
        self._spawn_embers()
        for p in self._particles:
            p['x'] += p['vx']; p['y'] += p['vy']; p['life'] -= 1
        self._particles = [p for p in self._particles if p['life'] > 0]

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if hasattr(self,"_spare_rect") and self._spare_rect.collidepoint(e.pos):
                    if self.gs.honor_score > 50:
                        self.gs.story_path = "Rebel Path"
                        self.gs.game_phase = "Tavern"
                elif hasattr(self,"_kill_rect") and self._kill_rect.collidepoint(e.pos):
                    self.gs.story_path  = "Mercenary Path"
                    self.gs.honor_score = max(0, self.gs.honor_score - 20)
                    self.gs.game_phase  = "Tavern"
                elif hasattr(self,"_rumor_rect") and self._rumor_rect.collidepoint(e.pos):
                    if not self._generating and not self.gs.rumor:
                        self._gen_rumor()

    def _gen_rumor(self):
        self._generating = True
        def worker():
            try:
                from llm_engine import get_garg_rumor
                self.gs.rumor = get_garg_rumor(self.gs.action_history)
            except Exception:
                self.gs.rumor = "They say Kaelen cheated using forbidden techniques. Garg never stood a chance."
            finally:
                self._generating = False
                self._rumor_done = True
        threading.Thread(target=worker, daemon=True).start()

    def draw(self):
        s  = self.screen
        gs = self.gs
        t  = self.tick

        # Background — blood-drenched arena aftermath
        draw_arena_bg(s, t)

        # Dark red dramatic overlay
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((40, 0, 0, 80))
        s.blit(ov, (0, 0))

        # Embers
        for p in self._particles:
            a = int(220 * p['life'] / p['ml'])
            ps2 = pygame.Surface((4,4), pygame.SRCALPHA)
            pygame.draw.circle(ps2, (*p['col'], a), (2,2), 2)
            s.blit(ps2, (int(p['x'])-2, int(p['y'])-2))

        # Entrance slide-in animation
        slide = max(0, (60 - self._anim_in) * 18)

        # ── TITLE ─────────────────────────────────────────────────────────
        title_bg = pygame.Surface((WIDTH, 72), pygame.SRCALPHA)
        title_bg.fill((*C_VOID, 220))
        s.blit(title_bg, (0, -slide))
        pygame.draw.line(s, C_GOLD, (0, 72-slide), (WIDTH, 72-slide), 2)

        # Animated title flicker
        flicker_col = tuple(int(c * (0.85 + 0.15*math.sin(t*0.07))) for c in C_GOLD)
        draw_text(s, "⚔   AFTERMATH   ⚔", self.font_title, flicker_col,
                  WIDTH//2, 14-slide, align="center", outline=True)

        # Decorative sword dividers
        pygame.draw.line(s, C_GOLD_DIM, (80, 78-slide), (WIDTH-80, 78-slide), 1)
        pygame.draw.polygon(s, C_GOLD, [(WIDTH//2-8,74-slide),(WIDTH//2+8,74-slide),(WIDTH//2,82-slide)])

        # ── STORY PANEL ───────────────────────────────────────────────────
        panel_y = 90 - slide
        draw_panel(s, 70, panel_y, WIDTH-140, 118, border=C_GOLD_DIM, alpha=210)
        pygame.draw.rect(s, C_GOLD, (70, panel_y, 3, 118))
        lines = [
            "Garg collapses to one knee, his weapon skidding across the sand.",
            "High Senator Vane rises from his gilded box, thumb turning downward.",
            "He demands you finish it.  But you are not the man they think you are.",
        ]
        for i, line in enumerate(lines):
            col = C_GOLD if i == 2 else C_WHITE
            draw_text(s, line, self.font_body, col, WIDTH//2, panel_y+16+i*34, align="center")

        # ── HONOUR GAUGE ─────────────────────────────────────────────────
        hc = C_GREEN if gs.honor_score > 50 else C_RED
        gy = 222
        # Gauge label
        draw_text(s, "HONOUR", self.font_tiny, C_GREY, WIDTH//2, gy-2, align="center", shadow=False)
        # Full-width honour bar
        draw_bar(s, WIDTH//2-200, gy+16, 400, 22, gs.honor_score, 100, hc)
        draw_panel(s, WIDTH//2-60, gy+6, 120, 40, border=hc, alpha=200)
        draw_text(s, f"{gs.honor_score} / 100", self.font_badge, hc,
                  WIDTH//2, gy+14, align="center")

        # ── CHOICE SECTION ────────────────────────────────────────────────
        cy2 = 290
        draw_text(s, "WHAT  DOES  KAELEN  DO?", self.font_heading, C_GOLD,
                  WIDTH//2, cy2, align="center", outline=True)
        pygame.draw.line(s, C_GOLD_DIM, (200, cy2+30), (WIDTH-200, cy2+30), 1)

        # SPARE button
        can_spare = gs.honor_score > 50
        self._spare_rect = draw_button(
            s, "🕊   SPARE GARG — REBEL PATH",
            self.font_badge, 70, cy2+44, (WIDTH-160)//2 - 10, 58,
            active=can_spare, border=C_GREEN, text_col=C_GREEN, glow_col=C_GREEN)

        if not can_spare:
            draw_text(s, f"⚠ Requires honour > 50  (yours: {gs.honor_score})",
                      self.font_tiny, C_RED, 70 + ((WIDTH-160)//2 - 10)//2, cy2+108,
                      align="center", shadow=False)

        # Center divider sword
        mid_x = WIDTH//2
        pygame.draw.line(s, C_GOLD_DIM, (mid_x, cy2+44), (mid_x, cy2+102), 2)
        pygame.draw.polygon(s, C_GOLD_DIM, [(mid_x-5,cy2+70),(mid_x+5,cy2+70),(mid_x,cy2+80)])

        # KILL button
        self._kill_rect = draw_button(
            s, "💀   KILL GARG — MERCENARY PATH",
            self.font_badge, WIDTH//2+10, cy2+44, (WIDTH-160)//2 - 10, 58,
            border=C_RED, text_col=C_RED, glow_col=C_RED)

        # ── RUMOR SECTION ─────────────────────────────────────────────────
        pygame.draw.line(s, C_GOLD_DIM, (70, cy2+120), (WIDTH-70, cy2+120), 1)
        pygame.draw.rect(s, C_GOLD, (WIDTH//2-30, cy2+117, 60, 4))

        rumor_y = cy2 + 132
        if not gs.rumor and not self._generating:
            # Pulsing button
            pulse = 1.0 + 0.08*math.sin(t*0.08)
            self._rumor_rect = draw_button(
                s, "🗣   GENERATE GARG'S RUMOR",
                self.font_badge, WIDTH//2-190, rumor_y, 380, 50,
                border=C_GOLD_DIM, text_col=C_GOLD_PALE)
        elif self._generating:
            # Animated dots
            dots = "◉" * (1 + (t//10)%3) + "○" * (3-(t//10)%3)
            draw_panel(s, 70, rumor_y, WIDTH-140, 52, border=C_GOLD_DIM, alpha=180)
            draw_text(s, f"⏳  Garg spins his lies...  {dots}",
                      self.font_body, C_GOLD_DIM, WIDTH//2, rumor_y+14, align="center")
        else:
            draw_panel(s, 70, rumor_y, WIDTH-140, 80, border=C_RED, alpha=210)
            pygame.draw.rect(s, C_RED, (70, rumor_y, 4, 80))
            draw_text(s, f'🗣  "{gs.rumor[:88]}"',
                      self.font_small, (230,100,100), WIDTH//2, rumor_y+10, align="center")
            draw_text(s, "— Garg's version of events",
                      self.font_tiny, C_GREY, WIDTH//2, rumor_y+54, align="center", shadow=False)

        # Bottom border
        pygame.draw.line(s, C_GOLD_DIM, (0, HEIGHT-3), (WIDTH, HEIGHT-3), 3)
