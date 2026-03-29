# src/ui/epilogue.py  — REDESIGNED v2
import pygame, math, random
from ui.base import *


REBEL_TEXT = [
    ("The blade feels right in your hand.", C_GOLD),
    ("Word has spread through the lower districts overnight.", C_WHITE),
    ("A Commander returned from the dead.", C_WHITE),
    ("A man who showed mercy when the entire Dominion demanded blood.", C_GOLD_PALE),
    ("", None),
    ("By morning, three former soldiers are waiting outside.", C_WHITE),
    ("", None),
    ("The rebellion has its symbol.", C_GREEN),
]

MERC_TEXT = [
    ("You tuck the blade into your belt and walk out.", C_WHITE),
    ("Senator Vane's messenger is waiting in the alley.", C_GOLD_DIM),
    ("A new contract.  A bigger arena.  More gold.", C_GOLD),
    ("", None),
    ("You used to fight for justice.", C_WHITE),
    ("Now you fight for whoever pays most.", C_RED),
    ("", None),
    ("At least you're honest about it.", C_GREY),
]


class EpilogueScreen(BaseScreen):
    def __init__(self, screen, gs, *fonts):
        super().__init__(screen, gs, *fonts)
        self._particles = []
        self._anim_in   = 0

    def _spawn_embers(self):
        is_rebel = self.gs.story_path == "Rebel Path"
        col = C_GREEN if is_rebel else C_RED
        for tx in [80, WIDTH-80]:
            if random.random() < 0.2:
                self._particles.append({
                    'x': float(tx + random.randint(-10,10)),
                    'y': float(80),
                    'vx': random.uniform(-0.4,0.4),
                    'vy': random.uniform(-1.5,-0.4),
                    'life': random.randint(30,60),
                    'ml': 60,
                    'col': col
                })

    def update(self, dt, events):
        super().update(dt, events)
        self._anim_in = min(80, self._anim_in + 1)
        self._spawn_embers()
        for p in self._particles:
            p['x'] += p['vx']; p['y'] += p['vy']; p['life'] -= 1
        self._particles = [p for p in self._particles if p['life'] > 0]

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if hasattr(self,"_play_rect") and self._play_rect.collidepoint(e.pos):
                    self.gs.__init__()
                    self.gs.game_phase = "Prologue"

    def draw(self):
        s  = self.screen
        gs = self.gs
        t  = self.tick

        is_rebel = gs.story_path == "Rebel Path"
        path_col = C_GREEN if is_rebel else C_RED

        # Background
        s.fill(C_VOID)
        for i in range(HEIGHT):
            bt = i/HEIGHT
            col = tuple(int(C_VOID[j] + (C_BG[j]-C_VOID[j])*bt) for j in range(3))
            pygame.draw.line(s, col, (0,i),(WIDTH,i))

        # Ember particles
        for p in self._particles:
            a = int(220 * p['life'] / p['ml'])
            ps2 = pygame.Surface((4,4), pygame.SRCALPHA)
            pygame.draw.circle(ps2, (*p['col'], a), (2,2), 2)
            s.blit(ps2, (int(p['x'])-2, int(p['y'])-2))

        # Torch glows
        for tx, ty in [(80, 80), (WIDTH-80, 80)]:
            flicker = 1.0+0.15*math.sin(t*0.08+tx)
            for r, a in [(int(120*flicker),7),(int(75*flicker),14),(int(38*flicker),28)]:
                gl = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
                pygame.draw.circle(gl, (*path_col, a), (r,r), r)
                s.blit(gl, (tx-r, ty-r))

        # Slide
        slide = max(0, (80-self._anim_in)*10)

        # ── TITLE ─────────────────────────────────────────────────────────
        title_bg = pygame.Surface((WIDTH, 72), pygame.SRCALPHA)
        title_bg.fill((*C_VOID, 210))
        s.blit(title_bg, (0, -slide))
        pygame.draw.line(s, C_GOLD, (0, 72-slide), (WIDTH, 72-slide), 2)

        draw_text(s, "📜   EPILOGUE", self.font_title, C_GOLD,
                  WIDTH//2, 12-slide, align="center", outline=True)
        pygame.draw.line(s, C_GOLD_DIM, (80, 80-slide), (WIDTH-80, 80-slide), 1)
        pygame.draw.polygon(s, C_GOLD, [(WIDTH//2-8,76-slide),(WIDTH//2+8,76-slide),(WIDTH//2,84-slide)])

        # ── PATH BANNER ───────────────────────────────────────────────────
        path_lbl = ("⚔   REBEL PATH — THE PEOPLE'S CHAMPION"
                    if is_rebel else
                    "🗡   MERCENARY PATH — SWORD FOR HIRE")
        py2 = 96
        draw_panel(s, 70, py2, WIDTH-140, 52, border=path_col, alpha=220)
        pygame.draw.rect(s, path_col, (70, py2, 5, 52))
        pygame.draw.rect(s, path_col, (WIDTH-75, py2, 5, 52))

        # Pulsing glow on banner
        glow_a = int(25+18*math.sin(t*0.07))
        gl2 = pygame.Surface((WIDTH-140, 52), pygame.SRCALPHA)
        gl2.fill((*path_col, glow_a))
        s.blit(gl2, (70, py2))

        draw_text(s, path_lbl, self.font_heading, path_col,
                  WIDTH//2, py2+13, align="center", outline=True)

        # ── STORY TEXT PANEL ──────────────────────────────────────────────
        story_y = 160
        lines = REBEL_TEXT if is_rebel else MERC_TEXT
        draw_panel(s, 70, story_y, WIDTH-140, 240, border=C_GOLD_DIM, alpha=200)
        pygame.draw.rect(s, C_GOLD_DIM, (70, story_y, 3, 240))

        oy = story_y + 18
        for text, col in lines:
            if text and col:
                # Fade in each line based on tick
                draw_text(s, text, self.font_body, col, WIDTH//2, oy, align="center")
            oy += 28

        # ── FINAL STATS ───────────────────────────────────────────────────
        stats_y = 414
        pygame.draw.line(s, C_GOLD_DIM, (70, stats_y), (WIDTH-70, stats_y), 1)
        draw_text(s, "⚔   FINAL  RECORD   ⚔", self.font_heading, C_GOLD,
                  WIDTH//2, stats_y+10, align="center")
        pygame.draw.line(s, C_GOLD_DIM, (70, stats_y+42), (WIDTH-70, stats_y+42), 1)

        stats = [
            ("Rounds Fought", str(gs.round_count),   C_GOLD),
            ("Final Honour",  str(gs.honor_score),    C_GREEN if gs.honor_score > 50 else C_RED),
            ("Story Path",    gs.story_path or "—",   path_col),
            ("Potions Left",  str(gs.potions),         C_CYAN),
        ]
        card_w = (WIDTH - 200) // 4
        for i, (label, val, vc) in enumerate(stats):
            sx = 100 + i*(card_w+16)
            sy2 = stats_y + 52
            draw_panel(s, sx, sy2, card_w, 70, border=vc, alpha=210)
            pygame.draw.rect(s, vc, (sx, sy2, card_w, 3))
            draw_text(s, label, self.font_tiny, C_GREY, sx+card_w//2, sy2+8,
                      align="center", shadow=False)
            draw_text(s, val,   self.font_heading, vc, sx+card_w//2, sy2+28, align="center")

            # Glow on card
            ga = int(20+12*math.sin(t*0.06+i*0.8))
            gc2 = pygame.Surface((card_w, 70), pygame.SRCALPHA)
            gc2.fill((*vc, ga))
            s.blit(gc2, (sx, sy2))

        # ── PLAY AGAIN ────────────────────────────────────────────────────
        btn_y = HEIGHT - 72
        pulse = 1.0+0.08*math.sin(t*0.09)
        bc = tuple(int(c*pulse) for c in C_GOLD)
        bc = tuple(min(255,c) for c in bc)
        self._play_rect = draw_button(
            s, "🔄   PLAY AGAIN — A NEW STORY",
            self.font_badge, WIDTH//2-220, btn_y, 440, 52,
            border=C_GOLD, text_col=bc, glow_col=C_GOLD)

        # Bottom bar
        pygame.draw.line(s, C_GOLD_DIM, (0, HEIGHT-3), (WIDTH, HEIGHT-3), 3)
