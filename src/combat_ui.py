# src/combat_ui.py
# Echoes of the Arena — Visual Combat UI
# Handles sprite loading, base64 encoding, CSS animations,
# and the full arena HTML render for the Combat phase.

import os
import base64
from pathlib import Path

# ── Asset paths ───────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
ASSETS_DIR = BASE_DIR / ".." / "assets" / "images"

SPRITE_FILES = {
    "hero":        ASSETS_DIR / "hero.png",
    "hero_hurt":   ASSETS_DIR / "hero_hurt.png",
    "enemy":       ASSETS_DIR / "enemy.png",
    "enemy_hurt":  ASSETS_DIR / "enemy_hurt.png",
}


def _b64(path: Path) -> str | None:
    """Return base64-encoded image string or None if file missing."""
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except FileNotFoundError:
        return None


def load_sprites() -> dict[str, str | None]:
    """Load all sprite PNGs as base64 strings."""
    return {key: _b64(path) for key, path in SPRITE_FILES.items()}


# ════════════════════════════════════════════════════════════════════════════
# CSS ANIMATIONS
# ════════════════════════════════════════════════════════════════════════════

ARENA_CSS = """
<style>
/* ── Arena background ────────────────────────────────────────────────── */
.arena-bg {
    position: relative;
    width: 100%;
    height: 340px;
    background:
        linear-gradient(180deg,
            #0a0a0a   0%,
            #1a0a0a  30%,
            #2a1a0a  55%,
            #1a1008  75%,
            #0e0c06 100%);
    border: 2px solid #2a2a2a;
    border-radius: 6px;
    overflow: hidden;
    box-shadow: inset 0 0 80px rgba(0,0,0,0.8);
}

/* ── Torch flicker lights ────────────────────────────────────────────── */
.torch-left, .torch-right {
    position: absolute;
    top: 0; width: 50%; height: 100%;
    pointer-events: none;
    animation: torchFlicker 3s ease-in-out infinite alternate;
}
.torch-left  { left: 0;
    background: radial-gradient(ellipse at 10% 20%,
        rgba(255,140,0,0.18) 0%, transparent 60%); }
.torch-right { right: 0;
    background: radial-gradient(ellipse at 90% 20%,
        rgba(255,100,0,0.15) 0%, transparent 60%);
    animation-delay: 1.5s; }

@keyframes torchFlicker {
    0%   { opacity: 0.7; }
    25%  { opacity: 1.0; }
    50%  { opacity: 0.8; }
    75%  { opacity: 1.0; }
    100% { opacity: 0.6; }
}

/* ── Sand ground ─────────────────────────────────────────────────────── */
.arena-ground {
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 90px;
    background: linear-gradient(180deg,
        transparent 0%,
        rgba(80,50,20,0.4) 40%,
        rgba(60,40,15,0.7) 100%);
    border-top: 1px solid rgba(120,80,30,0.3);
}

/* ── Blood stain marks on sand ───────────────────────────────────────── */
.blood-mark {
    position: absolute;
    border-radius: 50%;
    background: radial-gradient(ellipse,
        rgba(120,0,0,0.45) 0%, transparent 70%);
}
.blood-1 { width:80px; height:30px; bottom:20px; left:38%; }
.blood-2 { width:50px; height:20px; bottom:35px; left:55%; }
.blood-3 { width:60px; height:25px; bottom:15px; left:20%; }

/* ── Crowd silhouettes ───────────────────────────────────────────────── */
.crowd {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 70px;
    background: repeating-linear-gradient(
        90deg,
        rgba(20,10,5,0.9)  0px,  8px,
        rgba(30,15,8,0.85) 8px, 14px,
        rgba(15, 8,3,0.9) 14px, 22px
    );
    border-bottom: 1px solid rgba(80,40,10,0.4);
}
.crowd::after {
    content: '';
    position: absolute;
    bottom: -1px; left: 0; right: 0;
    height: 20px;
    background: linear-gradient(180deg,
        transparent 0%, rgba(0,0,0,0.6) 100%);
}

/* ── Crowd cheer pulse ───────────────────────────────────────────────── */
.crowd-cheer {
    animation: crowdPulse 0.5s ease-in-out 4;
}
@keyframes crowdPulse {
    0%,100% { filter: brightness(1); }
    50%     { filter: brightness(1.8) saturate(1.4); }
}

/* ── Character sprites ───────────────────────────────────────────────── */
.sprite-wrapper {
    position: absolute;
    bottom: 75px;
    display: flex;
    flex-direction: column;
    align-items: center;
}
.sprite-hero  { left:  10%; }
.sprite-enemy { right: 10%; }

.sprite-img {
    width: 96px;
    height: 96px;
    image-rendering: pixelated;
    filter: drop-shadow(0 4px 12px rgba(0,0,0,0.8));
}

/* ── Idle float ──────────────────────────────────────────────────────── */
.anim-idle {
    animation: idleFloat 2.4s ease-in-out infinite;
}
@keyframes idleFloat {
    0%,100% { transform: translateY(0px);   }
    50%     { transform: translateY(-6px);  }
}

/* ── Attack lunge ────────────────────────────────────────────────────── */
.anim-attack-hero {
    animation: heroAttack 0.45s ease-in-out forwards;
}
@keyframes heroAttack {
    0%   { transform: translateX(0)   scaleX(1);    }
    40%  { transform: translateX(60px) scaleX(1.15); }
    70%  { transform: translateX(45px) scaleX(0.9);  }
    100% { transform: translateX(0)   scaleX(1);    }
}

.anim-attack-enemy {
    animation: enemyAttack 0.45s ease-in-out forwards;
}
@keyframes enemyAttack {
    0%   { transform: translateX(0)    scaleX(1);    }
    40%  { transform: translateX(-60px) scaleX(1.15); }
    70%  { transform: translateX(-45px) scaleX(0.9);  }
    100% { transform: translateX(0)    scaleX(1);    }
}

/* ── Hurt flash ──────────────────────────────────────────────────────── */
.anim-hurt {
    animation: hurtFlash 0.6s ease-in-out;
}
@keyframes hurtFlash {
    0%,100% { filter: drop-shadow(0 4px 12px rgba(0,0,0,0.8)); }
    20%     { filter: drop-shadow(0 0 20px rgba(255,50,50,1))
                      brightness(2) saturate(0.2); }
    40%     { filter: drop-shadow(0 4px 12px rgba(0,0,0,0.8)); }
    60%     { filter: drop-shadow(0 0 16px rgba(255,50,50,0.8))
                      brightness(1.8); }
}

/* ── Death shake ─────────────────────────────────────────────────────── */
.anim-death {
    animation: deathShake 0.8s ease-in-out forwards;
}
@keyframes deathShake {
    0%         { transform: translateX(0) rotate(0deg) scaleY(1); }
    15%        { transform: translateX(-8px) rotate(-5deg); }
    30%        { transform: translateX(8px)  rotate(5deg); }
    50%        { transform: translateX(-5px) rotate(-3deg); }
    70%        { transform: translateX(5px)  rotate(2deg); }
    100%       { transform: translateX(0) rotate(-90deg) scaleY(0.3);
                 opacity: 0.3; }
}

/* ── Potion heal glow ────────────────────────────────────────────────── */
.anim-heal {
    animation: healGlow 1.0s ease-in-out;
}
@keyframes healGlow {
    0%,100% { filter: drop-shadow(0 4px 12px rgba(0,0,0,0.8)); }
    40%     { filter: drop-shadow(0 0 24px rgba(50,255,120,1))
                      brightness(1.6) saturate(1.5); }
}

/* ── Poison dark pulse ───────────────────────────────────────────────── */
.anim-poison {
    animation: poisonPulse 0.8s ease-in-out;
}
@keyframes poisonPulse {
    0%,100% { filter: drop-shadow(0 4px 12px rgba(0,0,0,0.8)); }
    40%     { filter: drop-shadow(0 0 20px rgba(120,0,200,0.9))
                      brightness(0.6) saturate(2); }
}

/* ── Overseer flash (full arena) ─────────────────────────────────────── */
.overseer-buff-flash {
    animation: overseeBuff 1.2s ease-in-out;
}
@keyframes overseeBuff {
    0%,100% { box-shadow: inset 0 0 80px rgba(0,0,0,0.8); }
    40%     { box-shadow: inset 0 0 60px rgba(255,215,0,0.5),
                          0 0 40px rgba(255,215,0,0.4); }
}

.overseer-nerf-flash {
    animation: overseerNerf 1.2s ease-in-out;
}
@keyframes overseerNerf {
    0%,100% { box-shadow: inset 0 0 80px rgba(0,0,0,0.8); }
    40%     { box-shadow: inset 0 0 60px rgba(180,0,0,0.7),
                          0 0 40px rgba(180,0,0,0.5); }
}

/* ── Floating damage numbers ─────────────────────────────────────────── */
.dmg-float {
    position: absolute;
    font-family: 'MedievalSharp', serif;
    font-size: 1.6rem;
    font-weight: bold;
    pointer-events: none;
    animation: floatUp 1.2s ease-out forwards;
}
.dmg-float.dmg-player  { color: #ff4444; right: 18%; bottom: 160px; }
.dmg-float.dmg-enemy   { color: #ffcc00; left:  18%; bottom: 160px; }
.dmg-float.dmg-heal    { color: #44ff88; right: 18%; bottom: 160px; }
.dmg-float.dmg-overseer{ color: #d4af37; left:  45%; bottom: 200px; font-size:1.2rem; }

@keyframes floatUp {
    0%   { opacity: 1;   transform: translateY(0)    scale(1.2); }
    60%  { opacity: 1;   transform: translateY(-40px) scale(1); }
    100% { opacity: 0;   transform: translateY(-70px) scale(0.8); }
}

/* ── VS divider ──────────────────────────────────────────────────────── */
.vs-text {
    position: absolute;
    left: 50%; bottom: 120px;
    transform: translateX(-50%);
    font-family: 'MedievalSharp', serif;
    color: rgba(212,175,55,0.25);
    font-size: 2.5rem;
    letter-spacing: 4px;
    pointer-events: none;
    text-shadow: 0 0 20px rgba(212,175,55,0.3);
}

/* ── Name plates ─────────────────────────────────────────────────────── */
.name-plate {
    font-family: 'MedievalSharp', serif;
    font-size: 0.75rem;
    letter-spacing: 2px;
    color: #d4af37;
    margin-top: 6px;
    text-shadow: 0 0 8px rgba(212,175,55,0.5);
}

/* ── Gesture action banner ───────────────────────────────────────────── */
.action-banner {
    position: absolute;
    bottom: 100px; left: 50%;
    transform: translateX(-50%);
    background: rgba(0,0,0,0.75);
    border: 1px solid #d4af37;
    border-radius: 4px;
    padding: 4px 16px;
    font-family: 'MedievalSharp', serif;
    color: #d4af37;
    font-size: 0.9rem;
    white-space: nowrap;
    animation: bannerFade 2.5s ease-out forwards;
}
@keyframes bannerFade {
    0%,60% { opacity: 1; transform: translateX(-50%) translateY(0); }
    100%   { opacity: 0; transform: translateX(-50%) translateY(-20px); }
}
</style>
"""


# ════════════════════════════════════════════════════════════════════════════
# ARENA RENDERER
# ════════════════════════════════════════════════════════════════════════════

def render_arena(
    player_hp:      int,
    enemy_hp:       int,
    hero_state:     str = "idle",    # idle | attack | hurt | heal | poison | dead
    enemy_state:    str = "idle",    # idle | attack | hurt | dead
    overseer_event: str = "",        # "" | "buff" | "nerf"
    last_action:    str = "",        # shown as action banner
    last_player_dmg: int = 0,
    last_enemy_dmg:  int = 0,
    last_heal:       int = 0,
) -> str:
    """
    Build the full arena HTML string with layered backgrounds,
    animated sprites, and floating damage numbers.
    Returns raw HTML to pass to st.markdown(unsafe_allow_html=True).
    """
    sprites = load_sprites()

    # ── Select sprite image based on state ───────────────────────────────
    hero_key  = "hero_hurt"  if hero_state  in ("hurt", "dead") else "hero"
    enemy_key = "enemy_hurt" if enemy_state in ("hurt", "dead") else "enemy"

    hero_b64  = sprites.get(hero_key)  or sprites.get("hero")
    enemy_b64 = sprites.get(enemy_key) or sprites.get("enemy")

    # ── Build img tags or SVG fallbacks ──────────────────────────────────
    def sprite_tag(b64: str | None, css_class: str, state: str) -> str:
        anim_map = {
            "idle":   "anim-idle",
            "attack": f"anim-attack-{css_class.split('-')[1]}",
            "hurt":   "anim-hurt",
            "heal":   "anim-heal",
            "poison": "anim-poison",
            "dead":   "anim-death",
        }
        anim = anim_map.get(state, "anim-idle")

        if b64:
            return (f'<img src="data:image/png;base64,{b64}" '
                    f'class="sprite-img {anim}" alt="character">')
        else:
            # SVG fallback silhouette
            color = "#4a7a4a" if "hero" in css_class else "#7a4a4a"
            return (f'<svg class="sprite-img {anim}" viewBox="0 0 32 48" '
                    f'xmlns="http://www.w3.org/2000/svg">'
                    f'<ellipse cx="16" cy="8"  rx="7" ry="7" fill="{color}"/>'
                    f'<rect   x="8"  y="14" width="16" height="20" rx="3" fill="{color}"/>'
                    f'<rect   x="4"  y="14" width="6"  height="14" rx="2" fill="{color}"/>'
                    f'<rect   x="22" y="14" width="6"  height="14" rx="2" fill="{color}"/>'
                    f'<rect   x="9"  y="33" width="6"  height="14" rx="2" fill="{color}"/>'
                    f'<rect   x="17" y="33" width="6"  height="14" rx="2" fill="{color}"/>'
                    f'</svg>')

    hero_img  = sprite_tag(hero_b64,  "sprite-hero",  hero_state)
    enemy_img = sprite_tag(enemy_b64, "sprite-enemy", enemy_state)

    # ── Arena-level CSS class based on overseer event ─────────────────────
    arena_anim = ""
    if overseer_event == "buff":
        arena_anim = "overseer-buff-flash"
    elif overseer_event == "nerf":
        arena_anim = "overseer-nerf-flash"

    # ── Floating damage numbers ────────────────────────────────────────────
    floats = ""
    if last_player_dmg > 0:
        floats += f'<div class="dmg-float dmg-player">-{last_player_dmg}</div>'
    if last_enemy_dmg > 0:
        floats += f'<div class="dmg-float dmg-enemy">-{last_enemy_dmg}</div>'
    if last_heal > 0:
        floats += f'<div class="dmg-float dmg-heal">+{last_heal}</div>'
    if overseer_event == "buff":
        floats += '<div class="dmg-float dmg-overseer">⚡ Crowd Cheer! +10</div>'
    elif overseer_event == "nerf":
        floats += '<div class="dmg-float dmg-overseer">💀 Ambush! -10</div>'

    # ── Action banner ──────────────────────────────────────────────────────
    banner = ""
    if last_action:
        banner = f'<div class="action-banner">{last_action}</div>'

    # ── Crowd cheer animation class ────────────────────────────────────────
    crowd_class = "crowd-cheer" if overseer_event == "buff" else "crowd"

    html = f"""
<div class="arena-bg {arena_anim}">
    <!-- Crowd -->
    <div class="{crowd_class}"></div>

    <!-- Torch lights -->
    <div class="torch-left"></div>
    <div class="torch-right"></div>

    <!-- Ground -->
    <div class="arena-ground">
        <div class="blood-mark blood-1"></div>
        <div class="blood-mark blood-2"></div>
        <div class="blood-mark blood-3"></div>
    </div>

    <!-- VS text -->
    <div class="vs-text">VS</div>

    <!-- Hero sprite -->
    <div class="sprite-wrapper sprite-hero">
        {hero_img}
        <div class="name-plate">KAELEN</div>
    </div>

    <!-- Enemy sprite -->
    <div class="sprite-wrapper sprite-enemy">
        {enemy_img}
        <div class="name-plate">GARG</div>
    </div>

    <!-- Floating numbers -->
    {floats}

    <!-- Action banner -->
    {banner}
</div>
"""
    return html
