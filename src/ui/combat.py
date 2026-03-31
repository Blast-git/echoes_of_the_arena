# src/ui/combat.py  — REDESIGNED v2
import pygame
import threading, math, random, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ui.base import *


GESTURE_COLOURS = {
    "Honorable Strike":    C_GREEN,
    "Defend":              C_BLUE,
    "Use Potion":          C_CYAN,
    "Dishonorable Poison": C_RED,
}

SPRITE_SIZE = (140, 180)


def _load_sprite(name):
    base = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "images")
    path = os.path.join(base, f"{name}.png")
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(img, SPRITE_SIZE)
    except Exception:
        surf = pygame.Surface(SPRITE_SIZE, pygame.SRCALPHA)
        col  = C_GREEN if "hero" in name else C_RED
        pygame.draw.rect(surf, col, surf.get_rect(), border_radius=8)
        draw_text(surf, name[:4].upper(), pygame.font.SysFont(None, 24), C_WHITE, 20, 70)
        return surf


class FloatingText:
    def __init__(self, text, x, y, colour, font):
        self.text    = text
        self.x, self.y = float(x), float(y)
        self.colour  = colour
        self.font    = font
        self.alpha   = 255
        self.life    = 90
        self.scale   = 2.0

    def update(self):
        self.y      -= 1.4
        self.life   -= 1
        self.alpha   = max(0, int(255 * self.life / 90))
        self.scale   = max(1.0, self.scale - 0.04)

    def draw(self, surf):
        if self.alpha <= 0: return
        base = self.font.render(self.text, True, self.colour)
        if self.scale > 1.05:
            w = max(1, int(base.get_width() * self.scale))
            h = max(1, int(base.get_height() * self.scale))
            base = pygame.transform.scale(base, (w, h))
        # Outline
        dark = tuple(max(0,c-140) for c in self.colour)
        for dx, dy in [(-1,-1),(1,1),(1,-1),(-1,1)]:
            o = self.font.render(self.text, True, dark)
            if self.scale > 1.05:
                o = pygame.transform.scale(o, (max(1,int(o.get_width()*self.scale)),
                                               max(1,int(o.get_height()*self.scale))))
            o.set_alpha(self.alpha)
            surf.blit(o, (int(self.x)-base.get_width()//2+dx,
                          int(self.y)-base.get_height()//2+dy))
        base.set_alpha(self.alpha)
        surf.blit(base, (int(self.x)-base.get_width()//2, int(self.y)-base.get_height()//2))

    @property
    def dead(self): return self.life <= 0


class Particle:
    """Sparks / blood splatter for hit effects."""
    def __init__(self, x, y, colour):
        self.x, self.y = float(x), float(y)
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-6, -1)
        self.life = random.randint(20, 50)
        self.max_life = self.life
        self.colour = colour
        self.size = random.randint(2, 5)

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.3
        self.life -= 1

    def draw(self, surf):
        a = int(255 * self.life / self.max_life)
        ps = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(ps, (*self.colour, a), (self.size, self.size), self.size)
        surf.blit(ps, (int(self.x)-self.size, int(self.y)-self.size))

    @property
    def dead(self): return self.life <= 0


class InputBox:
    def __init__(self, x, y, w, h, placeholder=""):
        self.rect        = pygame.Rect(x, y, w, h)
        self.text        = ""
        self.placeholder = placeholder
        self.active      = False
        self.tick        = 0

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if   event.key == pygame.K_BACKSPACE: self.text = self.text[:-1]
            elif event.key not in (pygame.K_RETURN, pygame.K_ESCAPE):
                if len(self.text) < 80: self.text += event.unicode
        return self.active and event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN

    def draw(self, surf, font):
        self.tick += 1
        border = C_GOLD if self.active else C_GREY
        # Background
        pygame.draw.rect(surf, C_DARKER, self.rect, border_radius=3)
        pygame.draw.rect(surf, border,   self.rect, 1, border_radius=3)
        if self.active:
            glow = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
            glow.fill((*C_GOLD, 12))
            surf.blit(glow, (self.rect.x, self.rect.y))
        display = self.text if self.text else self.placeholder
        col = C_WHITE if self.text else C_GREY
        draw_text(surf, display, font, col,
                  self.rect.x+12,
                  self.rect.y + self.rect.h//2 - font.get_height()//2,
                  shadow=bool(self.text))
        if self.active and self.tick % 60 < 30:
            tw = font.render(self.text, True, C_WHITE).get_width() if self.text else 0
            pygame.draw.rect(surf, C_GOLD,
                             (self.rect.x+14+tw, self.rect.y+6, 2, self.rect.h-12))

    def clear(self): self.text = ""


class CombatScreen(BaseScreen):
    HERO_X   = 210
    ENEMY_X  = WIDTH - 360
    SPRITE_Y = HEIGHT - 340

    def __init__(self, screen, gs, cam, *fonts):
        super().__init__(screen, gs, *fonts)
        self.cam      = cam
        self.floats   = []
        self.particles= []
        self.input    = InputBox(450, HEIGHT-62, 370, 44,
                                 "No webcam? Type your attack here...")
        self.shake    = 0
        self.shake_dx = 0
        self.flash    = None
        self.flash_a  = 0
        self.arena_tick = 0

        # Sprite animation states
        self.hero_anim  = "idle"
        self.enemy_anim = "idle"
        self.anim_tick  = 0

        # Sprites
        self.spr = {
            "hero":       _load_sprite("hero"),
            "hero_hurt":  _load_sprite("hero_hurt"),
            "enemy":      _load_sprite("enemy"),
            "enemy_hurt": _load_sprite("enemy_hurt"),
        }

        self._pending_round = False
        self._round_thread  = None
        self._lock_rect     = pygame.Rect(0,0,1,1)
        self._potion_rect   = pygame.Rect(0,0,1,1)

        # Round announcement
        self._round_announce   = 0    # frames to show "ROUND X" banner
        self._last_round_shown = 0

    def _sprite_pos(self, who, anim):
        base_x = self.HERO_X  if who == "hero" else self.ENEMY_X
        base_y = self.SPRITE_Y
        t = pygame.time.get_ticks()
        if anim == "attack":
            dx  = 80 if who == "hero" else -80
            osc = int(dx * abs(t % 400 - 200) / 200)
            return base_x + osc, base_y - abs(osc)//3
        if anim == "hurt":
            osc = int(12 * (self.anim_tick / 25)) * (-1 if who == "hero" else 1)
            jitter = random.randint(-2,2) if self.anim_tick > 10 else 0
            return base_x + osc + jitter, base_y + abs(osc)//2
        if anim == "dead":
            return base_x, base_y + 30
        # idle bob
        bob = int(6 * math.sin(t * 0.002))
        return base_x, base_y + bob

    def _get_sprite(self, who, anim):
        if who == "hero":
            return self.spr["hero_hurt"] if anim in ("hurt","dead") else self.spr["hero"]
        else:
            return self.spr["enemy_hurt"] if anim in ("hurt","dead") else self.spr["enemy"]

    def _spawn_hit_particles(self, x, y, colour, count=20):
        for _ in range(count):
            self.particles.append(Particle(x, y, colour))

    # ── Combat round (threaded) ────────────────────────────────────────────
    def _run_round(self, gesture, text):
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
            from cv_combat    import get_gesture_effects
            from rl_gladiator import get_garg_action
            from rl_overseer  import get_overseer_action_safe

            gs = self.gs

            if gesture:
                try:
                    effects = get_gesture_effects(gesture)
                except Exception:
                    effects = {"honor_delta":0,"player_damage":10,"heals":False,"blocks":False}

                if effects["heals"]:
                    if gs.potions > 0:
                        heal = min(25, 100 - gs.player_hp)
                        gs.player_hp   = min(100, gs.player_hp + heal)
                        gs.potions    -= 1
                        gs.honor_score = max(0, gs.honor_score - 2)
                        self.floats.append(FloatingText(
                            f"+{heal} HP", self.HERO_X+70, self.SPRITE_Y-30, C_CYAN, self.font_heading))
                        log = f"Used Potion — healed {heal} HP"
                    else:
                        log = "No potions left!"
                        effects["blocks"] = False
                else:
                    dmg = effects["player_damage"]
                    gs.enemy_hp     = max(0, gs.enemy_hp - dmg)
                    gs.honor_score  = max(0, min(100, gs.honor_score + effects["honor_delta"]))
                    self.enemy_anim = "hurt"
                    self.anim_tick  = 25
                    self.shake      = 12
                    self._spawn_hit_particles(self.ENEMY_X+70, self.SPRITE_Y+60,
                                              C_RED if dmg > 12 else C_GOLD)
                    self.floats.append(FloatingText(
                        f"-{dmg}", self.ENEMY_X+70, self.SPRITE_Y-30, C_GOLD, self.font_heading))
                    log = f"{gesture} — {dmg} dmg to Garg"
                blocked = effects.get("blocks", False)
            else:
                dmg = 12
                gs.enemy_hp     = max(0, gs.enemy_hp - dmg)
                self.enemy_anim = "hurt"
                self.anim_tick  = 25
                self.shake      = 8
                self._spawn_hit_particles(self.ENEMY_X+70, self.SPRITE_Y+60, C_GOLD)
                self.floats.append(FloatingText(
                    f"-{dmg}", self.ENEMY_X+70, self.SPRITE_Y-30, C_GOLD, self.font_heading))
                log     = f"{text} — {dmg} dmg"
                blocked = False

            gs.action_history.append(f"R{gs.round_count} [Kaelen]: {log}")

            if gs.enemy_hp <= 0:
                gs.enemy_hp     = 0
                gs.round_count += 1
                gs.game_phase   = "Aftermath"   # ← critical: trigger scene transition
                self._pending_round = False
                return

            # Enemy turn (RL)
            try:
                garg_action = get_garg_action(gs.player_hp, gs.enemy_hp, gs.round_count)
            except Exception:
                garg_action = {"action":"strike","damage":8,"taunt":""}

            if not blocked:
                enemy_dmg = garg_action.get("damage", 8)
                gs.player_hp   = max(0, gs.player_hp - enemy_dmg)
                self.hero_anim = "hurt"
                self.shake     = max(self.shake, 10)
                self._spawn_hit_particles(self.HERO_X+70, self.SPRITE_Y+60, C_RED_BRIGHT)
                self.floats.append(FloatingText(
                    f"-{enemy_dmg}", self.HERO_X+70, self.SPRITE_Y-30, C_RED, self.font_heading))
                gs.action_history.append(f"R{gs.round_count} [Garg]: {enemy_dmg} dmg")

            if garg_action.get("taunt"):
                gs.last_taunt = garg_action["taunt"]

            # Overseer
            try:
                overseer = get_overseer_action_safe(gs.honor_score, gs.round_count)
                if overseer and overseer.get("event"):
                    gs.overseer_event = overseer["event"]
                    if overseer.get("ambush"):
                        extra = random.randint(8,14)
                        gs.player_hp = max(0, gs.player_hp - extra)
                        self.floats.append(FloatingText(
                            "💀 AMBUSH!", WIDTH//2, HEIGHT//2-80, C_RED_BRIGHT, self.font_badge))
                        self._spawn_hit_particles(self.HERO_X+70, self.SPRITE_Y+40, C_RED_BRIGHT, 30)
            except Exception:
                pass

            gs.round_count += 1
            gs.last_gesture = None
            if gs.player_hp <= 0:
                gs.player_hp  = 0
                gs.game_phase = "Defeated"
            if gs.enemy_hp <= 0:
                gs.enemy_hp   = 0
                gs.game_phase = "Aftermath"

        finally:
            self._pending_round = False

    # ── Update ────────────────────────────────────────────────────────────
    def update(self, dt, events):
        super().update(dt, events)
        self.arena_tick += 1

        self.anim_tick = max(0, self.anim_tick - 1)
        if self.anim_tick == 0:
            self.hero_anim  = "idle"
            self.enemy_anim = "idle"

        if self.shake > 0:
            self.shake   -= 1
            self.shake_dx = (10 if self.shake % 4 < 2 else -10) if self.shake > 0 else 0
        else:
            self.shake_dx = 0

        if self.flash_a > 0:
            self.flash_a = max(0, self.flash_a - 4)

        for f in self.floats:   f.update()
        for p in self.particles: p.update()
        self.floats    = [f for f in self.floats    if not f.dead]
        self.particles = [p for p in self.particles if not p.dead]

        # Round announce
        if self._round_announce > 0:
            self._round_announce -= 1

        live_g = self.cam.get_gesture() if self.cam else None
        if live_g:
            self.gs.last_gesture = live_g

        if self._pending_round:
            return

        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if self.gs.last_gesture and self._lock_rect.collidepoint(e.pos):
                    self._fire_round(self.gs.last_gesture, None)
                if self._potion_rect.collidepoint(e.pos) and self.gs.potions > 0:
                    self._fire_round("Use Potion", None)
            if self.input.handle(e) and self.input.text.strip():
                self._fire_round(None, self.input.text.strip())
                self.input.clear()

    def _fire_round(self, gesture, text):
        if self._pending_round: return
        self._pending_round = True
        self.hero_anim      = "attack"
        self.anim_tick      = 25
        if self.gs.round_count != self._last_round_shown:
            self._round_announce   = 90
            self._last_round_shown = self.gs.round_count
        threading.Thread(target=self._run_round, args=(gesture, text), daemon=True).start()

    # ── Draw ──────────────────────────────────────────────────────────────
    def draw(self):
        s   = self.screen
        gs  = self.gs
        sdx = self.shake_dx

        # Full pixel-art arena background
        draw_arena_bg(s, self.arena_tick)

        # Flash overlay
        if self.flash and self.flash_a > 0:
            fl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fl.fill((*self.flash, self.flash_a))
            s.blit(fl, (sdx, 0))

        # Particles (behind sprites)
        for p in self.particles:
            p.draw(s)

        # ── SPRITES ──────────────────────────────────────────────────────
        hx, hy = self._sprite_pos("hero",  self.hero_anim)
        ex, ey = self._sprite_pos("enemy", self.enemy_anim)
        h_spr  = self._get_sprite("hero",  self.hero_anim)
        e_spr  = self._get_sprite("enemy", self.enemy_anim)

        # Sprite glow (health-based)
        hp_pct = gs.player_hp / 100
        glow_col = C_RED if hp_pct < 0.3 else (C_AMBER if hp_pct < 0.6 else C_GREEN_DIM)
        for r, a in [(50,6),(30,12)]:
            gls = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
            pygame.draw.circle(gls, (*glow_col, a), (r,r), r)
            s.blit(gls, (hx+sdx+SPRITE_SIZE[0]//2-r, hy+SPRITE_SIZE[1]//2-r))

        # Enemy glow
        e_hp_pct = gs.enemy_hp / 100
        e_glow = C_RED if e_hp_pct < 0.3 else C_RED_DARK
        for r, a in [(50,5),(28,10)]:
            gls = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
            pygame.draw.circle(gls, (*e_glow, a), (r,r), r)
            s.blit(gls, (ex+sdx+SPRITE_SIZE[0]//2-r, ey+SPRITE_SIZE[1]//2-r))

        # Shadow ellipses on ground
        pygame.draw.ellipse(s, (0,0,0), (hx+sdx+10, self.SPRITE_Y+SPRITE_SIZE[1]-5, 120, 16))
        pygame.draw.ellipse(s, (0,0,0), (ex+sdx+10, self.SPRITE_Y+SPRITE_SIZE[1]-5, 120, 16))

        s.blit(h_spr, (hx+sdx, hy))
        # Mirror enemy sprite
        e_flipped = pygame.transform.flip(e_spr, True, False)
        s.blit(e_flipped, (ex+sdx, ey))

        # Name plates
        for nx, ny, name, col in [
            (hx+sdx, hy+SPRITE_SIZE[1]+6, "KAELEN", C_GREEN),
            (ex+sdx, ey+SPRITE_SIZE[1]+6, "GARG",   C_RED)
        ]:
            draw_panel(s, nx-5, ny, SPRITE_SIZE[0]+10, 28, border=col, alpha=200)
            draw_text(s, name, self.font_tiny, col,
                      nx + SPRITE_SIZE[0]//2, ny+7, align="center")

        # VS text (faded)
        vs_a = max(0, 80 - self.arena_tick * 2) if self.arena_tick < 40 else 30
        vs_s = pygame.Surface((140, 60), pygame.SRCALPHA)
        vt = self.font_title.render("VS", True, C_GOLD_DIM)
        vt.set_alpha(vs_a)
        vs_s.blit(vt, (0, 0))
        s.blit(vs_s, (WIDTH//2+sdx-70, HEIGHT//2-80))

        # Floats
        for f in self.floats:
            f.draw(s)

        # ── TAUNT BUBBLE ─────────────────────────────────────────────────
        if gs.last_taunt:
            tw = min(460, self.font_small.render(gs.last_taunt, True, C_WHITE).get_width()+28)
            tx = ex + sdx - tw + SPRITE_SIZE[0]//2
            ty = ey - 58
            draw_panel(s, tx, ty, tw, 44, border=C_RED, alpha=210)
            # Speech bubble tail
            pygame.draw.polygon(s, C_DARKER, [
                (tx+tw-40, ty+44), (tx+tw-24, ty+56), (tx+tw-20, ty+44)])
            pygame.draw.polygon(s, C_RED, [
                (tx+tw-40, ty+44), (tx+tw-24, ty+56), (tx+tw-20, ty+44)], 1)
            draw_text(s, f'"{gs.last_taunt[:54]}"', self.font_small,
                      (230,100,100), tx+14, ty+10, shadow=False)

        # ── OVERSEER EVENT ────────────────────────────────────────────────
        if gs.overseer_event:
            ew = 540
            oy = HEIGHT - 200
            draw_panel(s, WIDTH//2+sdx-ew//2, oy, ew, 40, border=C_AMBER, alpha=220)
            pygame.draw.rect(s, C_AMBER, (WIDTH//2+sdx-ew//2, oy, 4, 40))
            draw_text(s, f"⚡  {gs.overseer_event[:62]}",
                      self.font_small, C_AMBER, WIDTH//2+sdx, oy+10, align="center")

        # ── ROUND ANNOUNCE BANNER ─────────────────────────────────────────
        if self._round_announce > 0:
            a = min(255, self._round_announce * 5)
            ban = pygame.Surface((500, 80), pygame.SRCALPHA)
            ban.fill((0,0,0,min(200,a)))
            s.blit(ban, (WIDTH//2-250, HEIGHT//2-100))
            rt = self.font_title.render(f"ROUND  {gs.round_count}", True, C_GOLD)
            rt.set_alpha(a)
            s.blit(rt, (WIDTH//2-rt.get_width()//2, HEIGHT//2-90))

        # ── TOP HUD ──────────────────────────────────────────────────────
        hud_h = 76
        hud_bg = pygame.Surface((WIDTH, hud_h), pygame.SRCALPHA)
        hud_bg.fill((*C_VOID, 220))
        s.blit(hud_bg, (0, 0))
        # HUD border
        pygame.draw.rect(s, C_GOLD_DIM, (0, 0, WIDTH, hud_h), 1)
        pygame.draw.line(s, C_GOLD, (0, hud_h-1), (WIDTH, hud_h-1))
        # Corner ornaments
        for cx, cy2 in [(0,0),(WIDTH-8,0),(0,hud_h-8),(WIDTH-8,hud_h-8)]:
            pygame.draw.rect(s, C_GOLD_DIM, (cx,cy2,8,8))

        ox = sdx
        # KAELEN side
        draw_text(s, "KAELEN", self.font_hud, C_GREEN, 18+ox, 6, outline=True)
        draw_bar(s, 18+ox, 34, 300, 18, gs.player_hp, 100, C_GREEN)
        draw_text(s, f"{gs.player_hp}/100", self.font_tiny, C_WHITE, 325+ox, 37, shadow=False)
        draw_text(s, "HONOUR", self.font_tiny, C_GREY, 18+ox, 56, shadow=False)
        draw_bar(s, 80+ox, 57, 160, 10, gs.honor_score, 100,
                 C_GREEN if gs.honor_score > 50 else C_RED)
        # Potion dots
        for i in range(3):
            col = C_CYAN if i < gs.potions else (30,30,30)
            pygame.draw.circle(s, col, (260+ox + i*24, 62), 8)
            pygame.draw.circle(s, tuple(min(255,c+60) for c in col) if i < gs.potions else C_GREY,
                               (260+ox + i*24, 62), 8, 1)

        # ROUND badge
        draw_panel(s, WIDTH//2+ox-80, 4, 160, 38, border=C_GOLD_DIM, alpha=200)
        draw_text(s, f"ROUND  {gs.round_count}", self.font_badge, C_GOLD,
                  WIDTH//2+ox, 12, align="center")

        # GARG side
        draw_text(s, "GARG", self.font_hud, C_RED, WIDTH-18+ox, 6, align="right", outline=True)
        draw_bar(s, WIDTH-322+ox, 34, 300, 18, gs.enemy_hp, 100, C_RED)
        draw_text(s, f"{gs.enemy_hp}/100", self.font_tiny, C_WHITE,
                  WIDTH-326+ox, 37, align="right", shadow=False)

        # ── BOTTOM CONTROL STRIP ─────────────────────────────────────────
        strip_y = HEIGHT - 148
        strip_bg = pygame.Surface((WIDTH, 148), pygame.SRCALPHA)
        strip_bg.fill((*C_VOID, 230))
        s.blit(strip_bg, (0, strip_y))
        pygame.draw.line(s, C_GOLD, (0, strip_y), (WIDTH, strip_y), 2)
        pygame.draw.rect(s, C_GOLD_DIM, (0, strip_y, WIDTH, 148), 1)

        # Camera feed
        cam_surf = self.cam.get_pygame_surface((200, 126)) if self.cam else None
        if cam_surf:
            s.blit(cam_surf, (12, strip_y + 10))
            pygame.draw.rect(s, C_GOLD_DIM, (12, strip_y+10, 200, 126), 1)
            pygame.draw.line(s, C_GOLD, (12, strip_y+10), (212, strip_y+10), 1)
        else:
            pygame.draw.rect(s, (8,6,4), (12, strip_y+10, 200, 126))
            pygame.draw.rect(s, C_GREY,  (12, strip_y+10, 200, 126), 1)
            draw_text(s, "◉  CAM", self.font_tiny, C_GREY, 112, strip_y+65, align="center", shadow=False)

        # Live gesture
        live_g = self.cam.get_gesture() if self.cam else None
        if live_g:
            gc = GESTURE_COLOURS.get(live_g, C_GOLD)
            draw_panel(s, 220, strip_y+8, 210, 28, border=gc, alpha=180)
            pygame.draw.rect(s, gc, (220, strip_y+8, 3, 28))
            draw_text(s, f"◉  {live_g}", self.font_tiny, gc, 232, strip_y+14, shadow=False)

        # Execute button
        locked_g = gs.last_gesture
        gc2 = GESTURE_COLOURS.get(locked_g, C_GOLD_DIM) if locked_g else C_GREY
        self._lock_rect = draw_button(
            s, f"⚔  EXECUTE: {locked_g or '— show gesture —'}",
            self.font_badge, 220, strip_y+44, 330, 44,
            active=bool(locked_g), border=gc2, text_col=gc2, glow_col=gc2)

        # Potion button
        self._potion_rect = draw_button(
            s, f"🧪  POTION  ({gs.potions})",
            self.font_badge, 562, strip_y+44, 190, 44,
            active=gs.potions > 0, border=C_CYAN, text_col=C_CYAN)

        # Text input
        self.input.draw(s, self.font_body)
        draw_button(s, "STRIKE", self.font_badge,
                    self.input.rect.right + 8, strip_y+44, 100, 44,
                    active=bool(self.input.text), border=C_RED, text_col=C_RED)

        # Gesture legend mini-strip
        legends = [("✊ Strike",C_GREEN),("✌ Defend",C_BLUE),("🖐 Potion",C_CYAN),("🤘 Poison",C_RED)]
        for i,(lt,lc) in enumerate(legends):
            lx = 220 + i*170
            draw_text(s, lt, self.font_tiny, lc, lx, strip_y+96, shadow=False)

        # Pending spinner
        if self._pending_round:
            dots = "●" * (1 + (self.tick // 8) % 3)
            draw_text(s, f"⏳  Processing{dots}", self.font_small,
                      C_GOLD_DIM, WIDTH-240, strip_y+8, shadow=False)
