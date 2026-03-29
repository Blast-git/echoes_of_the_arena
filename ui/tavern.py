# src/ui/tavern.py  — REDESIGNED v2
import pygame, math, threading
from ui.base import *


class TavernScreen(BaseScreen):
    def __init__(self, screen, gs, *fonts):
        super().__init__(screen, gs, *fonts)
        self.input     = None
        self._thinking = False
        self._anim_in  = 0
        self._init_input()
        self._chat_scroll  = 0
        self._msg_anims    = []   # per-message type-in

    def _init_input(self):
        self.input = _InputBox(80, HEIGHT-68, WIDTH-210, 48, "Speak to Aldric...")

    def update(self, dt, events):
        super().update(dt, events)
        self._anim_in = min(80, self._anim_in + 1)

        for e in events:
            if self.input.handle(e) and self.input.text.strip() and not self._thinking:
                self._send(self.input.text.strip())
                self.input.clear()
            if e.type == pygame.MOUSEBUTTONDOWN:
                if hasattr(self,"_leave_rect") and self._leave_rect.collidepoint(e.pos):
                    self.gs.game_phase = "Epilogue"

    def _send(self, msg):
        self._thinking = True
        self.gs.chat_history.append({"role":"user","content":msg})
        def worker():
            try:
                from rag_merchant import chat_with_merchant
                res = chat_with_merchant(msg, self.gs.honor_score, self.gs.story_path)
                dialogue    = res.get("dialogue","Aldric says nothing.")
                deal_status = res.get("deal_status","ongoing")
            except Exception:
                dialogue    = "Aldric mutters something inaudible. His eyes do not leave yours."
                deal_status = "ongoing"
            self.gs.chat_history.append({"role":"assistant","content":dialogue,
                                          "deal_status":deal_status})
            if deal_status in ("success","failed"):
                self.gs.merchant_deal_status = deal_status
            self._thinking = False
        threading.Thread(target=worker, daemon=True).start()

    def draw(self):
        s  = self.screen
        gs = self.gs
        t  = self.tick

        # Draw full tavern pixel-art background
        draw_tavern_bg(s, t)

        # Slide-in animation
        slide = max(0, (80 - self._anim_in) * 12)

        # ── TITLE BAR ─────────────────────────────────────────────────────
        title_bg = pygame.Surface((WIDTH, 80), pygame.SRCALPHA)
        title_bg.fill((*C_VOID, 210))
        s.blit(title_bg, (0, -slide))
        pygame.draw.line(s, C_GOLD, (0, 80-slide), (WIDTH, 80-slide), 2)

        draw_text(s, "🍻   THE  BROKEN  SHIELD  TAVERN",
                  self.font_title, C_GOLD, WIDTH//2, 10-slide, align="center", outline=True)
        draw_text(s, "— WHERE  SECRETS  ARE  CURRENCY —",
                  self.font_small, C_GOLD_DIM, WIDTH//2, 64-slide, align="center")
        pygame.draw.line(s, C_GOLD_DIM, (80, 86-slide), (WIDTH-80, 86-slide), 1)

        # ── PATH BANNER ───────────────────────────────────────────────────
        is_rebel = gs.story_path == "Rebel Path"
        path_col = C_GREEN if is_rebel else C_RED
        path_txt = ("⚔  You walk in as someone who showed mercy.  Word travels fast."
                    if is_rebel else
                    "🗡  You enter with fresh blood on your hands.  Everyone notices.")
        banner_y = 94
        draw_panel(s, 70, banner_y, WIDTH-140, 34, border=path_col, alpha=200)
        pygame.draw.rect(s, path_col, (70, banner_y, 4, 34))
        draw_text(s, path_txt, self.font_small, path_col,
                  WIDTH//2, banner_y+8, align="center")

        # ── RUMOR BAR ─────────────────────────────────────────────────────
        rumor_y = 136
        if gs.rumor:
            draw_panel(s, 70, rumor_y, WIDTH-140, 40, border=C_RED, alpha=190)
            pygame.draw.rect(s, C_RED, (70, rumor_y, 4, 40))
            draw_text(s, f'🗣  "{gs.rumor[:90]}"',
                      self.font_small, (230,100,100), WIDTH//2, rumor_y+10, align="center")
            chat_top = 184
        else:
            chat_top = 140

        # ── MERCHANT CHARACTER (right side) ───────────────────────────────
        merch_x = WIDTH - 200
        merch_y = chat_top + 30
        # Draw merchant at right side of screen
        draw_merchant(s, merch_x, merch_y, t)

        # Merchant name plate
        draw_panel(s, merch_x-20, merch_y+200, 130, 32, border=C_GOLD_DIM, alpha=200)
        draw_text(s, "ALDRIC", self.font_badge, C_GOLD_PALE, merch_x+45, merch_y+207, align="center")
        draw_text(s, "Merchant", self.font_tiny, C_GREY, merch_x+45, merch_y+220, align="center", shadow=False)

        # ── CHAT AREA ─────────────────────────────────────────────────────
        chat_w = WIDTH - 340   # leave room for merchant
        chat_h = HEIGHT - chat_top - 90
        draw_panel(s, 70, chat_top, chat_w, chat_h, border=C_GOLD_DIM, alpha=190)

        if not gs.chat_history:
            # Intro scene
            intro_y = chat_top + 30
            draw_text(s, "Behind the bar, Aldric polishes a goblet without looking up.",
                      self.font_body, C_WHITE, 70+chat_w//2, intro_y, align="center")
            draw_text(s, '"I know who you are.  Choose your words carefully."',
                      self.font_body, C_GOLD_PALE, 70+chat_w//2, intro_y+40, align="center")
            pygame.draw.line(s, C_GOLD_DIM, (120, intro_y+80), (70+chat_w-50, intro_y+80), 1)
            draw_text(s, "🎯  Goal: negotiate to purchase Aldric's legendary blade for 500 gold.",
                      self.font_small, C_GREY, 70+chat_w//2, intro_y+94, align="center", shadow=False)
        else:
            cy3 = chat_top + 12
            visible = gs.chat_history[-9:]
            for msg in visible:
                is_user = msg["role"] == "user"
                if is_user:
                    # Player message — right-aligned bubble
                    col  = C_WHITE
                    prefix = "You"
                    bg_col = C_DARK
                    border_col = C_GOLD_DIM
                    ax = 70 + chat_w - 20
                    align_val = "right"
                else:
                    col  = (210, 175, 100)
                    prefix = "Aldric"
                    bg_col = (14, 8, 5)
                    border_col = C_GOLD_DIM
                    ax = 86
                    align_val = "left"

                if cy3 + 30 > chat_top + chat_h - 10:
                    break

                # Name label
                label_col = C_GOLD if not is_user else C_GREEN_DIM
                draw_text(s, prefix, self.font_tiny, label_col, ax, cy3,
                          align=align_val, shadow=False)
                cy3 += 16

                # Message text
                content = msg["content"][:96]
                draw_text(s, content, self.font_small, col, ax, cy3,
                          align=align_val, shadow=False)
                cy3 += 26

                # Deal status badge
                if not is_user and "deal_status" in msg:
                    ds = msg["deal_status"]
                    if ds == "success":
                        draw_text(s, "✅ DEAL STRUCK", self.font_tiny, C_GREEN, ax, cy3,
                                  align=align_val, shadow=False)
                        cy3 += 18
                    elif ds == "failed":
                        draw_text(s, "❌ DEAL FAILED", self.font_tiny, C_RED, ax, cy3,
                                  align=align_val, shadow=False)
                        cy3 += 18

                # Separator
                pygame.draw.line(s, (30,20,10), (86, cy3+2), (70+chat_w-20, cy3+2), 1)
                cy3 += 10

        # ── DEAL CONCLUDED ────────────────────────────────────────────────
        deal_done = gs.merchant_deal_status in ("success","failed")
        if deal_done:
            dc = C_GREEN if gs.merchant_deal_status=="success" else C_RED
            label = ("✅  DEAL STRUCK — Aldric produces the legendary blade."
                     if gs.merchant_deal_status=="success"
                     else "❌  Aldric calls for the guards.  Leave.  Now.")
            deal_y = HEIGHT - 120
            draw_panel(s, 70, deal_y, WIDTH-140, 44, border=dc, alpha=230)
            pygame.draw.rect(s, dc, (70, deal_y, 5, 44))
            # Pulsing glow
            glow_a = int(30 + 20*math.sin(t*0.1))
            gls = pygame.Surface((WIDTH-140, 44), pygame.SRCALPHA)
            gls.fill((*dc, glow_a))
            s.blit(gls, (70, deal_y))
            draw_text(s, label, self.font_badge, dc, WIDTH//2, deal_y+12, align="center")
            self._leave_rect = draw_button(
                s, "LEAVE THE TAVERN  ➡", self.font_badge,
                WIDTH//2-190, HEIGHT-68, 380, 48,
                border=dc, text_col=dc, glow_col=dc)
        elif self._thinking:
            # Typing dots animation
            dots_n = 1 + (t//12)%3
            dots = "●"*dots_n + "○"*(3-dots_n)
            draw_text(s, f"Aldric considers his words  {dots}",
                      self.font_small, C_GOLD_DIM, WIDTH-280, HEIGHT-56, shadow=False)
        else:
            self.input.draw(s, self.font_body)
            send_active = bool(self.input.text)
            draw_button(s, "SEND ➤", self.font_badge,
                        WIDTH-122, HEIGHT-68, 100, 48,
                        active=True, border=C_GOLD if send_active else C_GREY,
                        text_col=C_GOLD if send_active else C_GREY)

        # Bottom ornamental line
        pygame.draw.line(s, C_GOLD_DIM, (0, HEIGHT-3), (WIDTH, HEIGHT-3), 3)


class _InputBox:
    def __init__(self, x, y, w, h, placeholder=""):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = ""
        self.placeholder = placeholder
        self.active = False
        self.tick = 0

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
            elif event.key not in (pygame.K_RETURN, pygame.K_ESCAPE):
                if len(self.text) < 120: self.text += event.unicode
        return self.active and event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN

    def draw(self, surf, font):
        self.tick += 1
        active = self.active
        border = C_GOLD if active else C_GREY

        # Background
        pygame.draw.rect(surf, C_DARKER, self.rect, border_radius=3)
        pygame.draw.rect(surf, border,   self.rect, 1, border_radius=3)

        if active:
            glow = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
            glow.fill((*C_GOLD, 14))
            surf.blit(glow, (self.rect.x, self.rect.y))
            # Corner accents
            for cx, cy in [(self.rect.x, self.rect.y),
                            (self.rect.right-4, self.rect.y),
                            (self.rect.x, self.rect.bottom-4),
                            (self.rect.right-4, self.rect.bottom-4)]:
                pygame.draw.rect(surf, C_GOLD, (cx, cy, 4, 4))

        display = self.text if self.text else self.placeholder
        col = C_WHITE if self.text else C_GREY
        draw_text(surf, display, font, col,
                  self.rect.x+12,
                  self.rect.y + self.rect.h//2 - font.get_height()//2,
                  shadow=bool(self.text))
        if active and self.tick % 60 < 30:
            tw = font.render(self.text, True, C_WHITE).get_width() if self.text else 0
            pygame.draw.rect(surf, C_GOLD,
                             (self.rect.x+14+tw, self.rect.y+8, 2, self.rect.h-16))

    def clear(self): self.text = ""
