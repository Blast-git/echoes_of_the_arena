# src/ui/base.py  — REDESIGNED v2
# Shared base class, drawing helpers, pixel-art visual system

import pygame
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ── Fullscreen resolution (falls back gracefully) ──────────────────────────
def _get_display_size():
    pygame.display.init()
    info = pygame.display.Info()
    w, h = info.current_w, info.current_h
    if w < 800 or h < 500:
        return 1280, 720
    return w, h

WIDTH, HEIGHT = 1280, 720   # logical canvas — scaled to fullscreen via display surface

# ── Colour Palette — "Ember & Ink" ────────────────────────────────────────
C_BG        = (  7,   5,   3)
C_BG2       = ( 14,  10,   7)
C_VOID      = (  3,   2,   1)

C_GOLD      = (212, 175,  55)
C_GOLD_DIM  = (120,  90,  25)
C_GOLD_PALE = (180, 150,  60)

C_RED       = (200,  30,  20)
C_RED_DARK  = ( 90,   8,   8)
C_RED_BRIGHT= (255,  70,  50)

C_GREEN     = ( 50, 160,  60)
C_GREEN_DIM = ( 25,  80,  30)

C_CYAN      = ( 30, 200, 200)
C_BLUE      = ( 33, 120, 210)

C_WHITE     = (230, 220, 200)
C_GREY      = ( 80,  68,  55)
C_DARK      = ( 20,  14,  10)
C_DARKER    = ( 10,   7,   5)
C_SAND      = (160, 120,  65)
C_SAND2     = ( 90,  65,  30)
C_BLOOD     = ( 70,   0,   0)
C_ORANGE    = (255, 130,   0)
C_AMBER     = (255, 170,  20)
C_PURPLE    = (120,  60, 180)

# ── Pixel font simulation — border-box style text ─────────────────────────
def draw_text(surf, text, font, colour, x, y, align="left", shadow=True, outline=False):
    rendered = font.render(text, True, colour)
    r = rendered.get_rect()
    if   align == "center": r.centerx = x
    elif align == "right":  r.right   = x
    else:                   r.left    = x
    r.top = y

    if outline:
        dark = tuple(max(0, c - 180) for c in colour)
        for dx, dy in [(-1,-1),(1,-1),(-1,1),(1,1),(0,-1),(0,1),(-1,0),(1,0)]:
            o = font.render(text, True, dark)
            or_ = o.get_rect()
            if   align == "center": or_.centerx = x + dx
            elif align == "right":  or_.right   = x + dx
            else:                   or_.left    = x + dx
            or_.top = y + dy
            surf.blit(o, or_)
    elif shadow:
        s = font.render(text, True, (0, 0, 0))
        sr = s.get_rect()
        if   align == "center": sr.centerx = x + 2
        elif align == "right":  sr.right   = x + 2
        else:                   sr.left    = x + 2
        sr.top = y + 2
        surf.blit(s, sr)

    surf.blit(rendered, r)
    return r


def draw_bar(surf, x, y, w, h, value, max_val, colour, bg=C_DARK, border=True):
    pygame.draw.rect(surf, bg, (x, y, w, h))
    pct = max(0.0, min(1.0, value / max(1, max_val)))
    if pct > 0:
        fw = max(1, int((w - 2) * pct))
        # Main fill
        pygame.draw.rect(surf, colour, (x+1, y+1, fw, h-2))
        # Highlight strip
        hi = tuple(min(255, c + 70) for c in colour)
        pygame.draw.rect(surf, hi, (x+1, y+1, fw, max(1, h//3)))
        # Shimmer pixel dots
        for i in range(0, fw, 8):
            pygame.draw.rect(surf, hi, (x+1+i, y+1, 2, 2))
    # Border — two-tone pixel style
    pygame.draw.rect(surf, C_GREY, (x, y, w, h), 1)
    pygame.draw.line(surf, C_DARK, (x, y+h-1), (x+w, y+h-1))
    pygame.draw.line(surf, C_DARK, (x+w-1, y), (x+w-1, y+h))


def draw_panel(surf, x, y, w, h, border=C_GOLD_DIM, alpha=210, inner=True):
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    panel.fill((*C_DARKER, alpha))
    surf.blit(panel, (x, y))
    # Outer border
    pygame.draw.rect(surf, border, (x, y, w, h), 1)
    # Top highlight
    pygame.draw.line(surf, tuple(min(255,c+50) for c in border), (x+1, y+1), (x+w-2, y+1))
    if inner:
        # Inner shadow bottom/right
        pygame.draw.line(surf, C_VOID, (x+1, y+h-2), (x+w-2, y+h-2))
        pygame.draw.line(surf, C_VOID, (x+w-2, y+1), (x+w-2, y+h-2))


def draw_button(surf, text, font, x, y, w, h, active=True,
                border=C_GOLD_DIM, text_col=C_GOLD, glow_col=None):
    rect = pygame.Rect(x, y, w, h)
    mx, my = pygame.mouse.get_pos()
    hovered = rect.collidepoint(mx, my) and active

    if active:
        # Background gradient simulation
        for i in range(h):
            t = i / h
            r_ = int(C_DARK[0] + (C_BG2[0]-C_DARK[0])*t)
            g_ = int(C_DARK[1] + (C_BG2[1]-C_DARK[1])*t)
            b_ = int(C_DARK[2] + (C_BG2[2]-C_DARK[2])*t)
            pygame.draw.line(surf, (r_,g_,b_), (x, y+i), (x+w, y+i))

        pygame.draw.rect(surf, border, rect, 1)
        # Corner pixel accents
        pygame.draw.rect(surf, border, (x, y, 4, 4))
        pygame.draw.rect(surf, border, (x+w-4, y, 4, 4))
        pygame.draw.rect(surf, border, (x, y+h-4, 4, 4))
        pygame.draw.rect(surf, border, (x+w-4, y+h-4, 4, 4))

        if hovered:
            gc = glow_col or border
            glow = pygame.Surface((w, h), pygame.SRCALPHA)
            glow.fill((*gc, 35))
            surf.blit(glow, (x, y))
            pygame.draw.rect(surf, tuple(min(255,c+60) for c in border), rect, 1)
            # Scanline shimmer on hover
            for i in range(0, h, 4):
                pygame.draw.line(surf, (*gc, 15), (x, y+i), (x+w, y+i))
    else:
        pygame.draw.rect(surf, C_DARKER, rect)
        pygame.draw.rect(surf, C_GREY,   rect, 1)
        text_col = C_GREY

    tw = font.render(text, True, text_col).get_width()
    draw_text(surf, text, font, text_col,
              x + w//2 - tw//2,
              y + h//2 - font.get_height()//2,
              shadow=active, outline=hovered)
    return rect


# ── Pixel-art arena background ────────────────────────────────────────────
def draw_arena_bg(surf, tick=0):
    """Full pixel-art arena: tiered crowd, sand floor, pillars, torches."""
    surf.fill(C_VOID)

    # Sky / ceiling gradient
    for i in range(160):
        t = i / 160
        col = tuple(int(C_VOID[j] + (C_BG[j] - C_VOID[j]) * t) for j in range(3))
        pygame.draw.line(surf, col, (0, i), (WIDTH, i))

    # --- ARENA WALL (back) ---
    wall_y = 55
    wall_h = 130
    for i in range(wall_h):
        t = i / wall_h
        base = (38, 25, 14)
        lo   = (22, 14,  8)
        col = tuple(int(base[j] + (lo[j] - base[j]) * t) for j in range(3))
        pygame.draw.line(surf, col, (0, wall_y + i), (WIDTH, wall_y + i))

    # Stone blocks on wall
    for bx in range(0, WIDTH, 64):
        for by in range(wall_y, wall_y+wall_h, 24):
            ox = (by // 24 % 2) * 32
            pygame.draw.rect(surf, (28, 18, 10), (bx + ox, by, 62, 22), 1)
            pygame.draw.line(surf, (45, 30, 15), (bx+ox, by), (bx+ox+62, by))

    # Crowd silhouettes (tiered)
    for tier in range(3):
        cy = wall_y + 15 + tier * 28
        crowd_col = (15 + tier*4, 10 + tier*3, 6 + tier*2)
        head_col  = (20 + tier*5, 12 + tier*4, 7 + tier*2)
        for cx in range(-12 + tier*8, WIDTH + 20, 14 + tier*3):
            jitter = (cx * 37 + tier * 131) % 10
            hh = 18 + jitter + tier * 4
            pygame.draw.ellipse(surf, crowd_col,   (cx - 5, cy - hh, 12, hh))
            pygame.draw.ellipse(surf, head_col,    (cx - 4, cy - hh - 7, 10, 10))

    # Crowd color accents (banners/torch glow)
    for bx in range(100, WIDTH - 100, 180):
        banner_col = [(180,20,20),(20,100,180),(200,160,20),(60,140,60)][bx//180 % 4]
        pygame.draw.rect(surf, banner_col, (bx, wall_y+10, 6, 40))
        pygame.draw.polygon(surf, banner_col, [
            (bx, wall_y+50), (bx+6, wall_y+50), (bx+3, wall_y+62)])

    # Crowd rail
    pygame.draw.rect(surf, (50, 35, 20), (0, wall_y + wall_h - 6, WIDTH, 10))
    pygame.draw.line(surf, (70, 50, 28), (0, wall_y+wall_h-6), (WIDTH, wall_y+wall_h-6))

    # --- SAND FLOOR ---
    floor_y = HEIGHT - 200
    for i in range(200):
        t = i / 200
        base = (C_BG2[0]+12, C_BG2[1]+8, C_BG2[2])
        top  = (C_SAND2[0]+20, C_SAND2[1]+12, C_SAND2[2]+4)
        col  = tuple(int(base[j] + (top[j]-base[j]) * t) for j in range(3))
        pygame.draw.line(surf, col, (0, floor_y + i), (WIDTH, floor_y + i))

    # Sand texture — pixel grain
    rng = random.Random(42)
    for _ in range(400):
        gx = rng.randint(0, WIDTH-1)
        gy = rng.randint(floor_y, HEIGHT-1)
        gc = rng.choice([(80,55,22),(100,72,30),(60,42,16)])
        surf.set_at((gx, gy), gc)

    # Sand highlight line
    pygame.draw.line(surf, (110, 80, 38), (0, floor_y), (WIDTH, floor_y), 2)

    # Blood stains
    for bx, by, bw, bh in [(500,HEIGHT-148,90,26),(730,HEIGHT-162,60,18),(290,HEIGHT-138,70,20)]:
        bs = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.ellipse(bs, (*C_BLOOD, 100), (0, 0, bw, bh))
        surf.blit(bs, (bx, by))

    # --- STONE PILLARS ---
    for px in [90, WIDTH - 130]:
        # Shadow
        ps = pygame.Surface((60, HEIGHT - floor_y + 20), pygame.SRCALPHA)
        ps.fill((0, 0, 0, 60))
        surf.blit(ps, (px + 14, floor_y - 20))
        # Pillar body gradient
        for i in range(50):
            t = i / 50
            lc = tuple(int((45+t*20, 30+t*12, 15+t*6)[j]) for j in range(3))
        pygame.draw.rect(surf, (42, 28, 14), (px, wall_y+wall_h-40, 50, HEIGHT))
        # Pillar highlight
        pygame.draw.line(surf, (65, 45, 22), (px+4, wall_y+wall_h-40), (px+4, HEIGHT))
        # Pillar shadow
        pygame.draw.line(surf, (28, 18, 8),  (px+44, wall_y+wall_h-40), (px+44, HEIGHT))
        # Capital
        pygame.draw.rect(surf, (55, 38, 18), (px-6, wall_y+wall_h-50, 62, 16))
        pygame.draw.line(surf, (80, 58, 28), (px-6, wall_y+wall_h-50), (px+56, wall_y+wall_h-50))

    # --- TORCH GLOWS (animated) ---
    for tx, ty in [(60, 110), (WIDTH-60, 110)]:
        flicker = 1.0 + 0.15 * math.sin(tick * 0.08)
        for r, a in [(int(140*flicker),8),(int(90*flicker),16),(int(50*flicker),28),(int(22*flicker),50)]:
            gs_ = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
            pygame.draw.circle(gs_, (*C_ORANGE, a), (r, r), r)
            surf.blit(gs_, (tx-r, ty-r))
        # Flame sprite
        flame_w, flame_h = 14, 22
        for fi in range(3):
            foff = int(3 * math.sin(tick*0.12 + fi*1.2))
            fc = [(255,180,20),(255,100,10),(200,50,5)][fi]
            pygame.draw.ellipse(surf, fc,
                (tx - flame_w//2 + foff, ty - flame_h - fi*4, flame_w - fi*3, flame_h - fi*3))
        # Torch stick
        pygame.draw.rect(surf, (60,35,15), (tx-3, ty-6, 6, 20))


# ── Pixel-art tavern background ───────────────────────────────────────────
def draw_tavern_bg(surf, tick=0):
    """Warm tavern interior — wooden walls, bar, shelves, fireplace."""
    surf.fill((8, 5, 3))

    # Back wall wood planks
    for i in range(HEIGHT):
        t = i / HEIGHT
        col = tuple(int((22+t*8, 14+t*5, 6+t*2)[j]) for j in range(3))
        pygame.draw.line(surf, col, (0, i), (WIDTH, i))

    # Vertical wood planks
    for px in range(0, WIDTH, 48):
        pygame.draw.line(surf, (18, 11, 5), (px, 0), (px, HEIGHT), 2)
        pygame.draw.line(surf, (32, 20, 9), (px+2, 0), (px+2, HEIGHT))

    # Horizontal dado rail
    pygame.draw.rect(surf, (45, 28, 12), (0, HEIGHT//2 - 20, WIDTH, 14))
    pygame.draw.line(surf, (65, 42, 18), (0, HEIGHT//2-20), (WIDTH, HEIGHT//2-20))
    pygame.draw.line(surf, (20, 12, 5),  (0, HEIGHT//2-7),  (WIDTH, HEIGHT//2-7))

    # Floor boards
    for i in range(HEIGHT//2, HEIGHT, 18):
        pygame.draw.line(surf, (28, 18, 8), (0, i), (WIDTH, i))
    for px in range(0, WIDTH, 80):
        pygame.draw.line(surf, (22, 14, 6), (px, HEIGHT//2), (px, HEIGHT))

    # --- FIREPLACE (left side) ---
    fp_x, fp_y, fp_w, fp_h = 40, HEIGHT//2 - 220, 160, 240
    # Mantle
    pygame.draw.rect(surf, (50, 32, 14), (fp_x-10, fp_y + fp_h - 40, fp_w+20, 44))
    pygame.draw.line(surf, (75, 50, 20), (fp_x-10, fp_y+fp_h-40), (fp_x+fp_w+10, fp_y+fp_h-40))
    # Surround
    pygame.draw.rect(surf, (40, 25, 12), (fp_x, fp_y, fp_w, fp_h-40), 4)
    # Fire glow on surrounding wall
    for r, a in [(180,6),(120,12),(80,20),(50,32)]:
        flicker = 1.0 + 0.2*math.sin(tick*0.09)
        r2 = int(r*flicker)
        gs2 = pygame.Surface((r2*2, r2*2), pygame.SRCALPHA)
        pygame.draw.circle(gs2, (*C_ORANGE, a), (r2,r2), r2)
        surf.blit(gs2, (fp_x+fp_w//2-r2, fp_y+fp_h-r2-20))
    # Flames
    for fi in range(5):
        fh = 40 + 15*math.sin(tick*0.1+fi*0.8)
        fc = [(255,200,20),(255,130,10),(220,60,5),(180,30,5),(255,240,60)][fi]
        pygame.draw.ellipse(surf, fc,
            (fp_x+15+fi*22, fp_y+fp_h-50-int(fh), 18, int(fh)))

    # --- SHELVES (right side) ---
    shelf_x = WIDTH - 220
    for sy in [HEIGHT//2 - 150, HEIGHT//2 - 60, HEIGHT//2 + 30]:
        pygame.draw.rect(surf, (55, 35, 15), (shelf_x, sy, 180, 12))
        pygame.draw.line(surf, (80, 52, 22), (shelf_x, sy), (shelf_x+180, sy))
        # Bottles on shelf
        for bi in range(5):
            bx2 = shelf_x + 10 + bi*35
            bc = [(180,30,30),(30,80,160),(80,160,80),(160,120,30),(100,30,140)][bi]
            # Bottle body
            pygame.draw.rect(surf, bc, (bx2, sy-28, 12, 26))
            pygame.draw.rect(surf, tuple(min(255,c+50) for c in bc), (bx2+2, sy-28, 3, 10))
            # Bottle neck
            pygame.draw.rect(surf, bc, (bx2+4, sy-36, 4, 10))
            # Cork
            pygame.draw.rect(surf, (140,100,60), (bx2+4, sy-38, 4, 4))

    # --- BAR COUNTER ---
    bar_y = HEIGHT - 120
    pygame.draw.rect(surf, (55, 35, 14), (0, bar_y, WIDTH, 10))
    pygame.draw.line(surf, (80, 54, 20), (0, bar_y), (WIDTH, bar_y))
    pygame.draw.rect(surf, (42, 26, 10), (0, bar_y+10, WIDTH, HEIGHT-bar_y-10))

    # Merchant silhouette area (right side behind counter)
    # Atmospheric candle glow spots
    for cx, cy2 in [(300, HEIGHT//2-50), (700, HEIGHT//2-80), (1000, HEIGHT//2-40)]:
        for r, a in [(50,5),(30,10),(15,22)]:
            cs = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
            pygame.draw.circle(cs, (*C_AMBER, a), (r,r), r)
            surf.blit(cs, (cx-r, cy2-r))

    # Hanging lanterns
    for lx in [WIDTH//4, WIDTH//2, 3*WIDTH//4]:
        rope_h = 40
        pygame.draw.line(surf, (60, 40, 18), (lx, 0), (lx, rope_h), 2)
        # Lantern body
        pygame.draw.rect(surf, (60, 40, 18), (lx-10, rope_h, 20, 28))
        pygame.draw.rect(surf, (*C_AMBER, 180), (lx-7, rope_h+3, 14, 22))
        # Glow
        flicker2 = 1.0 + 0.12*math.sin(tick*0.07 + lx)
        for r, a in [(int(60*flicker2),6),(int(35*flicker2),12),(int(18*flicker2),25)]:
            ls = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
            pygame.draw.circle(ls, (*C_AMBER, a), (r,r), r)
            surf.blit(ls, (lx-r, rope_h+14-r))

    # Corner torch glow
    for tx, ty in [(60,80),(WIDTH-60,80),(60,HEIGHT-60),(WIDTH-60,HEIGHT-60)]:
        flicker3 = 1.0+0.15*math.sin(tick*0.08+tx)
        for r, a in [(int(100*flicker3),5),(int(60*flicker3),12),(int(30*flicker3),25)]:
            ts = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
            pygame.draw.circle(ts, (*C_ORANGE, a), (r,r), r)
            surf.blit(ts, (tx-r, ty-r))


# ── Pixel-art merchant sprite ─────────────────────────────────────────────
def draw_merchant(surf, x, y, tick=0):
    """Draw Aldric the merchant as pixel art character."""
    # Shadow
    pygame.draw.ellipse(surf, (0,0,0,60) if False else (12,8,4),
                        (x-30, y+170, 80, 16))

    # Robe (layered rectangles for pixel look)
    robe_col = (60, 30, 80)
    robe_hi  = (90, 50, 120)
    robe_sh  = (35, 15, 50)

    # Main robe
    pygame.draw.rect(surf, robe_col, (x-22, y+60, 50, 120))
    # Robe highlight
    pygame.draw.rect(surf, robe_hi,  (x-18, y+65, 6, 100))
    # Robe shadow
    pygame.draw.rect(surf, robe_sh,  (x+16, y+65, 6, 100))

    # Belt
    pygame.draw.rect(surf, (100,70,30), (x-22, y+110, 50, 10))
    pygame.draw.rect(surf, (140,100,45),(x-5,  y+110, 16, 10))  # buckle

    # Sleeves
    bob = int(3*math.sin(tick*0.05))
    pygame.draw.rect(surf, robe_col, (x-40, y+70+bob, 22, 55))
    pygame.draw.rect(surf, robe_col, (x+24, y+70-bob, 22, 55))
    pygame.draw.rect(surf, robe_hi,  (x-38, y+72+bob, 4, 40))
    pygame.draw.rect(surf, robe_hi,  (x+26, y+72-bob, 4, 40))

    # Hands
    hand_col = (190, 150, 110)
    pygame.draw.rect(surf, hand_col, (x-38, y+122+bob, 14, 14))
    pygame.draw.rect(surf, hand_col, (x+30, y+122-bob, 14, 14))

    # Torso collar
    pygame.draw.rect(surf, (180,140,80), (x-8, y+60, 22, 20))
    pygame.draw.polygon(surf, (180,140,80), [(x+3,y+60),(x-8,y+68),(x+14,y+68)])

    # Neck
    neck_col = (190, 155, 115)
    pygame.draw.rect(surf, neck_col, (x-5, y+44, 16, 18))

    # Head (breathing bob)
    head_bob = int(2*math.sin(tick*0.04))
    head_col = (200, 162, 118)
    pygame.draw.rect(surf, head_col, (x-14, y+14+head_bob, 34, 32))
    # Ear
    pygame.draw.rect(surf, head_col, (x-17, y+18+head_bob, 5, 10))
    pygame.draw.rect(surf, head_col, (x+20, y+18+head_bob, 5, 10))

    # Eyes
    blink = 1 if (tick % 90) > 4 else 3
    pygame.draw.rect(surf, (40,25,12), (x-8,  y+20+head_bob, 8, blink))
    pygame.draw.rect(surf, (40,25,12), (x+6,  y+20+head_bob, 8, blink))
    # Eye whites
    if blink > 1:
        pygame.draw.rect(surf, (220,200,180),(x-7, y+21+head_bob, 6, blink-1))
        pygame.draw.rect(surf, (220,200,180),(x+7, y+21+head_bob, 6, blink-1))

    # Eyebrows (furrowed)
    pygame.draw.rect(surf, (80,50,20), (x-9,  y+17+head_bob, 9, 3))
    pygame.draw.rect(surf, (80,50,20), (x+6,  y+17+head_bob, 9, 3))

    # Nose
    pygame.draw.rect(surf, (175,135,95),(x+1, y+26+head_bob, 4, 6))

    # Mouth (slight smirk)
    pygame.draw.rect(surf, (130,90,65), (x-4, y+33+head_bob, 12, 3))
    pygame.draw.rect(surf, (160,110,80),(x+4, y+34+head_bob, 5, 2))

    # Hair / hood
    hair_col = (50, 30, 10)
    pygame.draw.rect(surf, hair_col, (x-14, y+14+head_bob, 34, 8))
    pygame.draw.rect(surf, hair_col, (x-14, y+14+head_bob, 6, 20))
    pygame.draw.rect(surf, hair_col, (x+22, y+14+head_bob, 6, 16))
    # Hood
    pygame.draw.polygon(surf, robe_sh, [
        (x-20, y+14+head_bob), (x+26, y+14+head_bob),
        (x+30, y+6+head_bob),  (x+3, y-6+head_bob), (x-24, y+4+head_bob)
    ])
    pygame.draw.polygon(surf, robe_col, [
        (x-14, y+16+head_bob), (x+20, y+16+head_bob),
        (x+24, y+8+head_bob),  (x+3,  y-2+head_bob), (x-18, y+6+head_bob)
    ])

    # Staff / ledger in right hand
    pygame.draw.rect(surf, (70,45,18), (x+32, y-20-head_bob, 6, 200))
    pygame.draw.rect(surf, (100,70,28),(x+32, y-26-head_bob, 6, 8))
    # Gem on staff
    pygame.draw.rect(surf, C_PURPLE,   (x+33, y-30-head_bob, 4, 6))
    pygame.draw.rect(surf, (180,140,220),(x+34,y-29-head_bob, 2, 3))

    # Feet / base of robe
    pygame.draw.rect(surf, robe_sh, (x-22, y+165, 25, 20))
    pygame.draw.rect(surf, robe_sh, (x+2,  y+165, 25, 20))
    # Boot tips
    pygame.draw.rect(surf, (30,18,8), (x-26, y+176, 28, 10))
    pygame.draw.rect(surf, (30,18,8), (x+2,  y+176, 28, 10))


class BaseScreen:
    def __init__(self, screen, gs, *fonts):
        self.screen = screen
        self.gs     = gs
        self.tick   = 0
        (self.font_title, self.font_heading, self.font_body,
         self.font_small, self.font_badge, self.font_hud, self.font_tiny) = fonts

    def update(self, dt, events):
        self.tick += 1

    def draw(self):
        pass

    def btn_clicked(self, rect, events):
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if rect.collidepoint(e.pos):
                    return True
        return False
