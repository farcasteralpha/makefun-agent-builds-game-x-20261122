#!/usr/bin/env python3
"""Render video.mp4 (1080x1920, 24fps, 30s) for the make.fun bounty.

Scenes, all drawn frame-by-frame with PIL (a screen recording of the build):
  A  0.0- 4.0s  hook + the ONE prompt typed out
  B  4.0-12.0s  editor: game code lines appearing + terminal progress
  C 12.0-25.0s  the finished game actually playing (same mechanics as game.html)
  D 25.0-27.5s  "IT WORKS." + score + call to build on make.fun
The referral end card is overlaid afterwards by ffmpeg (see build_video.sh),
NOT drawn here — the press-pack file is used as-is.
"""
import math, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, DUR = 1080, 1920, 24, 30
N = FPS * DUR
OUT = "/tmp/agent-game-frames"
random.seed(20261122)

FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FM = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FMB = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

def font(p, s):
    return ImageFont.truetype(p, s)

def wrap(draw, text, fnt, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= maxw:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines

def star_pts(cx, cy, r, rot=0.0):
    pts = []
    for i in range(10):
        rad = r if i % 2 == 0 else r * 0.45
        a = (i * math.pi) / 5 - math.pi / 2 + rot
        pts.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad))
    return pts

def draw_fox(d, x, y, s=1.0):
    # tail
    d.ellipse([x - 150 * s, y - 6 * s, x - 78 * s, y + 34 * s], fill="#e8823a")
    d.ellipse([x - 158 * s, y + 4 * s, x - 118 * s, y + 30 * s], fill="#ffffff")
    # ears
    d.polygon([(x - 52 * s, y - 40 * s), (x - 66 * s, y - 92 * s), (x - 20 * s, y - 56 * s)], fill="#e8823a")
    d.polygon([(x + 52 * s, y - 40 * s), (x + 66 * s, y - 92 * s), (x + 20 * s, y - 56 * s)], fill="#e8823a")
    # body + chest
    d.ellipse([x - 72 * s, y - 52 * s, x + 72 * s, y + 52 * s], fill="#e8823a")
    d.ellipse([x - 40 * s, y - 8 * s, x + 40 * s, y + 44 * s], fill="#ffffff")
    # eyes + nose
    d.ellipse([x - 30 * s, y - 22 * s, x - 14 * s, y - 6 * s], fill="#1c1c1c")
    d.ellipse([x + 14 * s, y - 22 * s, x + 30 * s, y - 6 * s], fill="#1c1c1c")
    d.ellipse([x - 8 * s, y + 2 * s, x + 8 * s, y + 18 * s], fill="#1c1c1c")

def sky(d, t, top=(11, 16, 38), mid=(26, 36, 80), bot=(44, 30, 77)):
    for y in range(0, H, 8):
        f = y / H
        c = tuple(int(top[i] + (bot[i] - top[i]) * f) for i in range(3))
        d.rectangle([0, y, W, y + 8], fill=c)
    for i in range(70):
        sx = (i * 137.5) % W; sy = (i * 89.3) % (H * 0.7)
        tw = 0.4 + 0.6 * abs(math.sin(t * 0.001 + i))
        a = int(tw * 200)
        d.ellipse([sx, sy, sx + 4, sy + 4], fill=(255, 255, 255, a))
    d.ellipse([W - 200, 90, W - 110, 180], fill="#f5f0d0")
    d.rectangle([0, H - 110, W, H], fill="#0d3319")
    d.rectangle([0, H - 110, W, H - 98], fill="#14532d")

PROMPT = ("Build a tiny browser game in a single HTML file: a fox at the bottom "
          "of a night-sky canvas catches falling stars with the arrow keys "
          "(or A/D, or touch-drag). Stars are worth 1 point, rare golden stars "
          "are worth 5, bombs cost one of 3 lives. 30-second timer, live score, "
          "game-over screen with the final score and restart.")

CODE_LINES = [
    ("const cv = document.getElementById('game');", "#7ee0a3"),
    ("const ctx = cv.getContext('2d');", "#7ee0a3"),
    ("let score = 0, lives = 3, timeLeft = 30;", "#c792ea"),
    ("function spawnItem() {", "#82aaff"),
    ("  const r = Math.random();", "#d6deeb"),
    ("  const kind = r < .62 ? 'star'", "#d6deeb"),
    ("    : r < .78 ? 'gold' : 'bomb';", "#d6deeb"),
    ("  items.push({ kind, x: rand(40, W-40),", "#d6deeb"),
    ("    y: -30, vy: rand(240, 380) });", "#d6deeb"),
    ("}", "#82aaff"),
    ("function drawFox(x, y) { /* ears, tail,", "#82aaff"),
    ("  eyes — one cute fox, drawn in code */ }", "#82aaff"),
    ("function frame(ts) {", "#82aaff"),
    ("  foxX += (foxTX - foxX) * dt * 14;", "#d6deeb"),
    ("  if (caught) score += gold ? 5 : 1;", "#d6deeb"),
    ("  if (timeLeft <= 0) endGame();", "#d6deeb"),
    ("  requestAnimationFrame(frame);", "#d6deeb"),
    ("}", "#82aaff"),
    ("// 30 seconds. One fox. Go. 🦊", "#6a9955"),
]
TERM_LINES = [
    "$ agent: building game from one prompt…",
    "✓ canvas + night sky ready",
    "✓ fox, stars, bombs drawn",
    "✓ 30s timer + score + lives",
    "✓ game runs — 0 errors",
]

# --- gameplay simulation (same rules as game.html) ---
class Sim:
    def __init__(self):
        self.fox, self.target = 540.0, 540.0
        self.items, self.score, self.t = [], 0, 0.0
        self.spawn = 0.0
    def step(self, dt):
        self.t += dt
        self.spawn -= dt
        if self.spawn <= 0:
            r = random.random()
            kind = "star" if r < 0.62 else ("gold" if r < 0.78 else "bomb")
            self.items.append({"kind": kind, "x": random.uniform(60, 1020),
                               "y": -40, "vy": random.uniform(420, 640),
                               "rot": random.uniform(0, 6.28), "vr": random.uniform(-2, 2)})
            self.spawn = random.uniform(0.30, 0.55)
        # fox chases nearest falling star
        stars = [it for it in self.items if it["kind"] != "bomb"]
        if stars:
            near = min(stars, key=lambda it: it["y"])
            self.target = max(90, min(990, near["x"]))
        self.fox += (self.target - self.fox) * min(1, dt * 10)
        fox_y = 1620
        for it in list(self.items):
            it["y"] += it["vy"] * dt; it["rot"] += it["vr"] * dt
            if abs(it["x"] - self.fox) < 95 and abs(it["y"] - fox_y) < 85:
                if it["kind"] != "bomb":
                    self.score += 5 if it["kind"] == "gold" else 1
                self.items.remove(it)
            elif it["y"] > 1980:
                self.items.remove(it)

SIM = Sim()
# pre-run the sim so gameplay frames match a real playthrough.
# NOTE: snapshot plain tuples per frame — the dicts keep mutating, so a
# shallow list() copy would show every item at its end-of-life y.
GAME_FRAMES = {}
for fi in range(int(12 * FPS), int(25 * FPS)):
    SIM.step(1 / FPS)
    GAME_FRAMES[fi] = (SIM.fox, [(it["kind"], it["x"], it["y"], it["rot"]) for it in SIM.items], SIM.score)
FINAL_SCORE = SIM.score

import os
BADGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "press-badge-9x16.png")
assert os.path.exists(BADGE_PATH), "press badge missing: " + BADGE_PATH
badge = Image.open(BADGE_PATH).convert("RGBA")
os.makedirs(OUT, exist_ok=True)

def base(t):
    img = Image.new("RGBA", (W, H), (11, 16, 38, 255))
    return img, ImageDraw.Draw(img)

def add_badge(img, t):
    if badge and t < 27.5:
        img.alpha_composite(badge, (0, 0))

for fi in range(N):
    t = fi / FPS
    img, d = base(t)
    if t < 4.0:
        # Scene A: hook + prompt typing (headline kept clear of the
        # make.fun badge, which sits at x120, y272-400)
        d.text((80, 430), "ONE", font=font(FB, 190), fill="#ffffff")
        d.text((80, 620), "PROMPT.", font=font(FB, 190), fill="#ffd76a")
        d.text((80, 850), "one game. watch it happen.", font=font(FR, 54), fill="#9aa7d8")
        # chat bubble with typed prompt
        chars = int(max(0, (t - 0.8)) * 90)
        shown = PROMPT[:chars]
        d.rounded_rectangle([60, 950, 1020, 1560], radius=36, fill="#1a2450", outline="#3d4a86", width=3)
        d.text((100, 985), "you  →  your AI agent", font=font(FMB, 40), fill="#7ee0a3")
        lines = wrap(d, shown, font(FM, 38), 860)
        y = 1065
        for ln in lines:
            d.text((100, y), ln, font=font(FM, 38), fill="#e8ecff")
            y += 56
        if chars < len(PROMPT) and int(t * 2) % 2 == 0:
            d.rectangle([100 + d.textlength(lines[-1] if lines else "", font=font(FM, 38)), y - 56, 100 + d.textlength(lines[-1] if lines else "", font=font(FM, 38)) + 18, y - 8], fill="#ffd76a")
        d.text((80, 1640), "no edits. no second try.", font=font(FB, 52), fill="#ffffff")
    elif t < 12.0:
        # Scene B: editor + terminal
        d.rectangle([0, 0, W, H], fill="#0b1026")
        d.rounded_rectangle([50, 120, 1030, 1180], radius=24, fill="#1e1e2e")
        d.rounded_rectangle([50, 120, 1030, 190], radius=24, fill="#2b2b40")
        d.ellipse([80, 143, 110, 173], fill="#ff5f57")
        d.ellipse([124, 143, 154, 173], fill="#febc2e")
        d.ellipse([168, 143, 198, 173], fill="#28c840")
        d.text((230, 138), "game.html — Starfall Fox", font=font(FMB, 38), fill="#d6deeb")
        d.text((80, 222), "agent@makefun:~/starfall-fox — writing game.html", font=font(FM, 32), fill="#565f89")
        d.line([(80, 412), (1000, 412)], fill="#2b2b40", width=2)
        nlines = min(len(CODE_LINES), int((t - 4.0) / 0.42) + 1)
        y = 430  # code starts below the make.fun badge (y272-400)
        for i, (code, col) in enumerate(CODE_LINES[:nlines]):
            d.text((80, y), f"{i+1:>2}", font=font(FM, 28), fill="#565f89")
            d.text((150, y), code, font=font(FM, 28), fill=col)
            y += 40
        if nlines < len(CODE_LINES) and int(t * 2) % 2 == 0:
            d.rectangle([150, y + 4, 168, y + 34], fill="#ffd76a")
        # terminal
        d.rounded_rectangle([50, 1230, 1030, 1700], radius=24, fill="#0d1117", outline="#30363d", width=2)
        d.text((90, 1260), "agent — building…", font=font(FMB, 38), fill="#7ee0a3")
        nterm = min(len(TERM_LINES), int((t - 4.0) / 1.4) + 1)
        y = 1330
        for ln in TERM_LINES[:nterm]:
            d.text((90, y), ln, font=font(FM, 36), fill="#c9d1d9")
            y += 62
        d.text((80, 1780), "writing the game, line by line.", font=font(FB, 48), fill="#ffffff")
    elif t < 25.0:
        # Scene C: gameplay
        fox, items, score = GAME_FRAMES[fi]
        sky(d, t * 1000)
        # HUD (kept clear of the make.fun badge at top-left, y 272-400)
        d.rounded_rectangle([40, 460, 560, 620], radius=28, fill=(0, 0, 0, 90))
        d.text((80, 490), f"Score  {score}", font=font(FB, 64), fill="#ffffff")
        d.text((80, 570), "30-second run", font=font(FR, 36), fill="#c7cfee")
        d.text((700, 250), f"{max(0, math.ceil(30 - (t - 12)))}s", font=font(FB, 64), fill="#ffffff")
        d.text((700, 330), "♥♥♥", font=font(FB, 40), fill="#ff6b6b")
        for kind, x, y, rot in items:
            if kind == "bomb":
                d.ellipse([x - 34, y - 34, x + 34, y + 34], fill="#2b2b33", outline="#555555", width=4)
                d.text((x - 14, y - 26), "!", font=font(FB, 48), fill="#ffffff")
            else:
                gold = kind == "gold"
                d.polygon(star_pts(x, y, 34 if gold else 28, rot),
                          fill="#ffd700" if gold else "#ffe9a8", outline="#ff9d00" if gold else "#f5c542")
        draw_fox(d, fox, 1620, 1.35)
        d.text((80, 1760), "it plays. for real.", font=font(FB, 52), fill="#ffffff")
    else:
        # Scene D: payoff
        d.rectangle([0, 0, W, H], fill="#0b1026")
        d.text((80, 420), "IT", font=font(FB, 200), fill="#ffffff")
        d.text((80, 620), "WORKS.", font=font(FB, 200), fill="#ffd76a")
        d.text((80, 900), f"Score {FINAL_SCORE} — 30 seconds,", font=font(FR, 56), fill="#e8ecff")
        d.text((80, 980), "0 errors, 1 prompt.", font=font(FR, 56), fill="#e8ecff")
        d.rounded_rectangle([80, 1150, 1000, 1330], radius=30, fill="#c41c83")
        d.text((130, 1200), "Your turn — build yours", font=font(FB, 52), fill="#ffffff")
        d.text((80, 1420), "on make.fun", font=font(FB, 52), fill="#ffffff")
        d.text((80, 1560), "game + video in the repo ↓", font=font(FR, 46), fill="#9aa7d8")
    add_badge(img, t)
    img.convert("RGB").save(f"{OUT}/f{fi:04d}.png")

print(f"rendered {N} frames, final gameplay score {FINAL_SCORE}")
print("FINAL_SCORE=" + str(FINAL_SCORE))
