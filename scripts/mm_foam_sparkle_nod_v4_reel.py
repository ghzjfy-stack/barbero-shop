#!/usr/bin/env python3
"""MinoxShop Member's Mark — clipper fake-out v4 (foam sparkle nod).

Same as v3 polish, plus: during «יש גם קצף» soft-crossfade to the foam
pack with sparkle glints (not a hard PowerPoint cut), then ease back to liquid.
"""

from __future__ import annotations

import math
import os
import shutil
import struct
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H, FPS, DUR = 1080, 1920, 30, 16
N = FPS * DUR
COVER_HOLD_SEC = 0.8
COVER_HOLD_N = int(round(COVER_HOLD_SEC * FPS))

ASSETS = Path(os.environ.get("MM_ASSETS", "/tmp/mm-reel"))
OUT = Path(os.environ.get("MM_OUT", "/tmp/mm-foam-sparkle-v4"))
ART = Path("/opt/cursor/artifacts")
LOGO_PATH = Path(os.environ.get("MINOX_LOGO", "/tmp/minox-mp/main-logo.png"))

FONT = "/usr/share/fonts/truetype/croscore/Arimo-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/croscore/Arimo-Regular.ttf"

# Beat map — slower after hook so persuasion lands
HOOK_END = 2.15
STOP_END = 3.35
PRODUCT_IN = 3.45
ID_END = 6.10
MONTHS_END = 7.80
PRICE_END = 11.40
SHIP_END = 13.70
# Soft foam pop inside ship beat (crossfade in/out)
FOAM_IN = 11.55
FOAM_PEAK = 12.55
FOAM_OUT = 13.35


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT if bold else FONT_REG, size)


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 3 * t * t - 2 * t * t * t


def load_rgb(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def cover_window(im: Image.Image, *, zoom: float, focus_x: float, focus_y: float) -> Image.Image:
    zoom = max(1.0, zoom)
    scale = max(W / im.width, H / im.height) * zoom
    nw, nh = max(W + 2, int(im.width * scale)), max(H + 2, int(im.height * scale))
    r = im.resize((nw, nh), Image.Resampling.LANCZOS)
    max_x, max_y = nw - W, nh - H
    x = int(max(0, min(max_x, max_x * focus_x)))
    y = int(max(0, min(max_y, max_y * focus_y)))
    return r.crop((x, y, x + W, y + H))


def grade(im: Image.Image, *, contrast: float = 1.1, bright: float = 0.94, color: float = 1.05) -> Image.Image:
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Color(im).enhance(color)
    return ImageEnhance.Brightness(im).enhance(bright)


def prepare_logo(path: Path, width: int = 200) -> Image.Image:
    logo = Image.open(path).convert("RGBA")
    arr = np.array(logo)
    rgb = arr[..., :3].astype(np.int16)
    white = (rgb[:, :, 0] > 232) & (rgb[:, :, 1] > 232) & (rgb[:, :, 2] > 225)
    arr[..., 3] = np.where(white, 0, 255).astype(np.uint8)
    logo = Image.fromarray(arr, "RGBA")
    if logo.getbbox():
        logo = logo.crop(logo.getbbox())
    h = int(logo.height * width / logo.width)
    return logo.resize((width, h), Image.Resampling.LANCZOS)


def draw_text(d: ImageDraw.ImageDraw, xy, text: str, *, size: int, fill, bold: bool = True, anchor="mm"):
    f = font(size, bold)
    kw = dict(font=f, fill=fill, anchor=anchor)
    if any("\u0590" <= c <= "\u05FF" for c in text):
        kw["direction"] = "rtl"
        kw["language"] = "he"
    d.text(xy, text, **kw)


def chip_block(
    canvas: Image.Image,
    y: int,
    lines: list[str],
    *,
    size: int,
    opacity: float,
    style: str = "dark",
    pop: float = 1.0,
):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(size)
    widths, heights = [], []
    for line in lines:
        bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), line, font=f)
        widths.append(bb[2] - bb[0])
        heights.append(bb[3] - bb[1])
    pad_x, pad_y, gap = 40, 24, 12
    # pop = entrance scale (starts slightly small, lands at 1.0)
    scale = 0.88 + 0.12 * max(0.0, min(1.0, pop))
    box_w = int((max(widths) + pad_x * 2) * scale)
    box_h = int((sum(heights) + gap * (len(lines) - 1) + pad_y * 2) * scale)
    x0 = (W - box_w) // 2
    y0 = y
    if style == "stamp":
        fill = (8, 12, 20, int(235 * opacity))
        radius = 18
    elif style == "alert":
        fill = (200, 18, 28, int(245 * opacity))
        radius = 14
    elif style == "hook":
        fill = (255, 214, 40, int(245 * opacity))
        radius = 12
    else:
        fill = (0, 0, 0, int(205 * opacity))
        radius = 22
    d.rounded_rectangle((x0, y0, x0 + box_w, y0 + box_h), radius=radius, fill=fill)
    if style == "hook":
        d.rounded_rectangle(
            (x0, y0, x0 + box_w, y0 + box_h),
            radius=radius,
            outline=(20, 20, 20, int(180 * opacity)),
            width=4,
        )
    cy = y0 + pad_y
    text_fill = (12, 12, 14, int(255 * opacity)) if style == "hook" else (255, 255, 255, int(255 * opacity))
    tsize = max(18, int(size * scale))
    for i, line in enumerate(lines):
        draw_text(d, (W // 2, cy + int(heights[i] * scale) // 2), line, size=tsize, fill=text_fill)
        cy += int(heights[i] * scale) + gap
    canvas.alpha_composite(layer)


def paste_logo(canvas: Image.Image, logo: Image.Image, *, opacity: float = 1.0):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lw, lh = logo.size
    x = (W - lw) // 2
    y = int(H * 0.88)
    pillow = Image.new("RGBA", (lw + 48, lh + 36), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pillow)
    pd.rounded_rectangle((0, 0, lw + 48, lh + 36), radius=22, fill=(255, 255, 255, int(210 * opacity)))
    layer.alpha_composite(pillow, (x - 24, y - 18))
    mark = logo.copy()
    if opacity < 0.99:
        a = mark.split()[-1].point(lambda v: int(v * opacity))
        mark.putalpha(a)
    layer.alpha_composite(mark, (x, y))
    canvas.alpha_composite(layer)


def apply_shake(im: Image.Image, amount: float, t: float) -> Image.Image:
    if amount < 0.01:
        return im
    dx = int(amount * 14 * math.sin(t * 62))
    dy = int(amount * 11 * math.cos(t * 51))
    base = Image.new("RGB", (W, H), (18, 16, 16))
    base.paste(im, (dx, dy))
    return base


def flash_white(im: Image.Image, amount: float) -> Image.Image:
    if amount <= 0:
        return im
    white = Image.new("RGB", (W, H), (255, 255, 255))
    return Image.blend(im, white, min(1.0, amount))


def draw_red_clipper(canvas: Image.Image, cx: float, cy: float, *, scale: float = 1.0, buzz: float = 0.0):
    """Red cordless clipper silhouette — viral fake-shave cue."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    s = scale
    # buzz jitter
    jx = int(4 * buzz * math.sin(cy * 0.4))
    jy = int(2 * buzz * math.cos(cx * 0.3))
    cx, cy = int(cx) + jx, int(cy) + jy

    # shadow under machine
    d.ellipse((cx - int(90 * s), cy + int(70 * s), cx + int(90 * s), cy + int(110 * s)), fill=(0, 0, 0, 70))

    # body
    bw, bh = int(150 * s), int(220 * s)
    x0, y0 = cx - bw // 2, cy - bh // 2
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=int(28 * s), fill=(210, 28, 36, 255))
    # darker side panel
    d.rounded_rectangle(
        (x0 + int(12 * s), y0 + int(18 * s), x0 + int(48 * s), y0 + bh - int(70 * s)),
        radius=int(14 * s),
        fill=(150, 16, 22, 255),
    )
    # gloss stripe
    d.rounded_rectangle(
        (x0 + int(70 * s), y0 + int(22 * s), x0 + bw - int(22 * s), y0 + int(50 * s)),
        radius=int(10 * s),
        fill=(255, 120, 120, 90),
    )
    # power switch
    d.rounded_rectangle(
        (cx - int(18 * s), y0 + int(70 * s), cx + int(18 * s), y0 + int(110 * s)),
        radius=int(8 * s),
        fill=(40, 40, 44, 255),
    )
    d.ellipse((cx - int(10 * s), y0 + int(78 * s), cx + int(10 * s), y0 + int(98 * s)), fill=(240, 240, 245, 255))

    # taper / neck
    neck_w, neck_h = int(88 * s), int(36 * s)
    nx0 = cx - neck_w // 2
    ny0 = y0 + bh - int(18 * s)
    d.rounded_rectangle((nx0, ny0, nx0 + neck_w, ny0 + neck_h), radius=int(10 * s), fill=(180, 20, 28, 255))

    # blade / guard (silver teeth) — the “about to shave” tip
    blade_w, blade_h = int(120 * s), int(42 * s)
    bx0 = cx - blade_w // 2
    by0 = ny0 + neck_h - int(6 * s)
    d.rounded_rectangle((bx0, by0, bx0 + blade_w, by0 + blade_h), radius=int(6 * s), fill=(210, 214, 220, 255))
    d.rounded_rectangle(
        (bx0 + 2, by0 + 2, bx0 + blade_w - 2, by0 + blade_h - 2),
        radius=int(5 * s),
        fill=(160, 166, 175, 255),
    )
    # teeth
    teeth = 9
    for i in range(teeth):
        tx = bx0 + int((i + 0.5) * blade_w / teeth)
        tw = max(3, int(7 * s))
        d.rectangle((tx - tw // 2, by0 + blade_h - 2, tx + tw // 2, by0 + blade_h + int(16 * s)), fill=(230, 233, 238, 255))

    # red LED
    d.ellipse((cx + int(40 * s), y0 + int(36 * s), cx + int(56 * s), y0 + int(52 * s)), fill=(255, 70, 70, 255))

    canvas.alpha_composite(layer)


def red_cut_path(canvas: Image.Image, t: float, tip_y: float):
    """Thin red guide line the clipper is “about to” carve."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x = int(W * 0.50 + 5 * math.sin(t * 22))
    y0 = int(H * 0.18)
    y1 = int(min(tip_y, H * 0.62))
    if y1 <= y0:
        return
    for w, a in ((34, 40), (16, 110), (5, 240)):
        d.line((x, y0, x, y1), fill=(230, 24, 34, a), width=w)
    # hot tip
    r = 16
    d.ellipse((x - r, y1 - r, x + r, y1 + r), fill=(255, 70, 70, 170))
    canvas.alpha_composite(layer)


def chip_at(t: float):
    """Returns lines, opacity, style, size, pop (0→1 entrance)."""
    def pop_since(start: float, win: float = 0.28) -> float:
        return ease_out(min(1.0, max(0.0, (t - start) / win)))

    if 0.05 <= t < HOOK_END:
        return ["לגלח את זה", "ולגמור עם זה?"], 1.0, "hook", 62, pop_since(0.05)
    if HOOK_END + 0.04 <= t < STOP_END:
        return ["רגע."], 1.0, "stamp", 132, pop_since(HOOK_END + 0.04, 0.22)
    if PRODUCT_IN <= t < ID_END:
        return ["מינוקסידיל 5%", "טיפות · Member's Mark"], 1.0, "dark", 50, pop_since(PRODUCT_IN)
    if ID_END <= t < MONTHS_END:
        return ["6 חודשים מלאים", "יבוא ארה״ב"], 1.0, "stamp", 56, pop_since(ID_END)
    if MONTHS_END <= t < PRICE_END:
        # Black Friday persuasion — hold long
        return ["BLACK FRIDAY", "375₪", "מחיר שובר שוק"], 1.0, "bf", 52, pop_since(MONTHS_END, 0.35)
    if PRICE_END <= t < FOAM_IN:
        return ["משלוח חינם", "עד הבית עם שליח"], 1.0, "dark", 46, pop_since(PRICE_END)
    if FOAM_IN <= t < FOAM_OUT:
        return ["יש גם קצף במלאי", "אותו 5% · Member's Mark"], 1.0, "hook", 48, pop_since(FOAM_IN, 0.32)
    if FOAM_OUT <= t < SHIP_END:
        return ["משלוח חינם עד הבית"], 1.0, "dark", 46, pop_since(FOAM_OUT, 0.22)
    if SHIP_END <= t < DUR - 0.08:
        return ["הקישור בפרופיל", "עכשיו"], 1.0, "stamp", 52, pop_since(SHIP_END)
    return None


def foam_mix(t: float) -> float:
    """0→1→0 soft envelope for foam plate blend."""
    if t < FOAM_IN or t > FOAM_OUT:
        return 0.0
    if t < FOAM_IN + 0.35:
        return ease_out((t - FOAM_IN) / 0.35)
    if t > FOAM_OUT - 0.35:
        return ease_in_out(1.0 - (t - (FOAM_OUT - 0.35)) / 0.35)
    return 1.0


def draw_sparkles(canvas: Image.Image, t: float, amount: float):
    """Soft glints over foam cans — pretty, not flare-spam."""
    if amount < 0.05:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # fixed pretty positions over 4-can pack (mid frame)
    seeds = [
        (0.28, 0.38), (0.42, 0.34), (0.55, 0.40), (0.68, 0.36),
        (0.35, 0.52), (0.50, 0.48), (0.62, 0.55), (0.45, 0.62),
        (0.58, 0.30), (0.33, 0.44),
    ]
    for i, (fx, fy) in enumerate(seeds):
        phase = (t * 3.2 + i * 0.73) % 1.0
        twinkle = max(0.0, math.sin(phase * math.pi)) ** 2
        a = int(200 * amount * twinkle)
        if a < 12:
            continue
        cx, cy = int(W * fx), int(H * fy)
        r = 3 + int(5 * twinkle)
        # 4-point sparkle
        d.line((cx - r * 2, cy, cx + r * 2, cy), fill=(255, 255, 255, a), width=2)
        d.line((cx, cy - r * 2, cx, cy + r * 2), fill=(255, 255, 255, a), width=2)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 250, 230, int(a * 0.7)))
    # soft foam bloom near center cans
    bloom = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bloom)
    br = int(40 + 30 * amount)
    bd.ellipse((W // 2 - br, int(H * 0.48) - br, W // 2 + br, int(H * 0.48) + br), fill=(255, 255, 255, int(55 * amount)))
    bloom = bloom.filter(ImageFilter.GaussianBlur(18))
    canvas.alpha_composite(bloom)
    canvas.alpha_composite(layer)


def beat_camera(t: float):
    if t < HOOK_END:
        z = 1.20 + 0.12 * ease_out(t / HOOK_END) + 0.025 * math.sin(t * 10)
        return z, 0.50, 0.36, 0.0, 0.70 + 0.30 * math.sin(t * 26)
    if t < STOP_END:
        return 1.0, 0.5, 0.45, 0.0, 0.0
    u = t - PRODUCT_IN
    z = 1.02 + 0.06 * min(1.0, u / 10.0) + 0.012 * math.sin(u * 1.4)
    # tiny punch when foam pops in
    if FOAM_IN <= t < FOAM_IN + 0.35:
        z += 0.04 * ease_out((t - FOAM_IN) / 0.35)
    flash = 0.0
    if MONTHS_END <= t < MONTHS_END + 0.28:
        flash = 0.22
    elif FOAM_IN <= t < FOAM_IN + 0.22:
        flash = 0.16 * (1.0 - (t - FOAM_IN) / 0.22)
    return z, 0.5, 0.48, flash, 0.04


def draw_bf_stack(canvas: Image.Image, y: int, lines: list[str], *, opacity: float, pop: float):
    """Dedicated Black Friday price stack — badge + huge price + subline."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    scale = 0.86 + 0.14 * pop
    cy = y

    # BF badge
    bf = lines[0]
    fbf = font(44)
    bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), bf, font=fbf)
    ww, hh = bb[2] - bb[0], bb[3] - bb[1]
    bw, bh = int((ww + 52) * scale), int((hh + 26) * scale)
    bx = (W - bw) // 2
    d.rounded_rectangle((bx, cy, bx + bw, cy + bh), radius=12, fill=(196, 22, 32, int(245 * opacity)))
    draw_text(d, (W // 2, cy + bh // 2), bf, size=int(44 * scale), fill=(255, 255, 255, int(255 * opacity)))
    cy += bh + 18

    # price
    price = lines[1]
    fp = font(int(130 * scale))
    bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), price, font=fp)
    ww, hh = bb[2] - bb[0], bb[3] - bb[1]
    pw, ph = ww + 72, hh + 44
    px = (W - pw) // 2
    d.rounded_rectangle((px, cy, px + pw, cy + ph), radius=28, fill=(0, 0, 0, int(245 * opacity)))
    draw_text(d, (W // 2, cy + ph // 2), price, size=int(130 * scale), fill=(255, 255, 255, int(255 * opacity)))
    cy += ph + 18

    # sub
    sub = lines[2]
    fsub = font(46)
    bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), sub, font=fsub)
    ww, hh = bb[2] - bb[0], bb[3] - bb[1]
    sw, sh = ww + 48, hh + 28
    sx = (W - sw) // 2
    d.rounded_rectangle((sx, cy, sx + sw, cy + sh), radius=16, fill=(255, 205, 55, int(240 * opacity)))
    draw_text(d, (W // 2, cy + sh // 2), sub, size=46, fill=(20, 18, 12, int(255 * opacity)))
    canvas.alpha_composite(layer)


def frame_at(i: int, scalp: Image.Image, bottles: Image.Image, foam: Image.Image, logo: Image.Image) -> Image.Image:
    t = i / FPS
    zoom, fx, fy, flash, shake = beat_camera(t)

    if t < HOOK_END:
        plate = cover_window(scalp, zoom=zoom, focus_x=fx, focus_y=fy)
        plate = grade(plate, contrast=1.22, bright=0.88, color=1.08)
        canvas = plate.convert("RGBA")
        progress = ease_in_out(min(1.0, t / 1.45))
        tip_y = H * (0.26 + 0.36 * progress)
        red_cut_path(canvas, t, tip_y)
        enter = ease_out(min(1.0, t / 0.22))
        clip_y = tip_y - 20 + (1 - enter) * (-160)
        clip_x = W * 0.50 + 10 * math.sin(t * 22)
        draw_red_clipper(
            canvas,
            clip_x,
            clip_y,
            scale=1.55 + 0.10 * math.sin(t * 18),
            buzz=1.0 + 0.55 * math.sin(t * 44),
        )
    elif t < STOP_END:
        canvas = Image.new("RGBA", (W, H), (6, 8, 12, 255))
    else:
        mix = foam_mix(t)
        # slight extra zoom on foam so the pop feels intentional
        fz = zoom + (0.05 if mix > 0.05 else 0.0)
        liquid = cover_window(bottles, zoom=zoom, focus_x=fx, focus_y=fy)
        liquid = grade(liquid, contrast=1.12, bright=0.96, color=1.04)
        if mix > 0.01:
            foam_plate = cover_window(foam, zoom=fz, focus_x=0.5, focus_y=0.48)
            foam_plate = grade(foam_plate, contrast=1.14, bright=1.0, color=1.06)
            plate = Image.blend(liquid, foam_plate, mix)
        else:
            plate = liquid
        canvas = plate.convert("RGBA")
        vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        vd = ImageDraw.Draw(vig)
        for k, a in ((0, 0), (1, 18), (2, 36)):
            m = 40 + k * 70
            vd.rectangle((0, 0, W, m), fill=(8, 14, 28, a))
            vd.rectangle((0, H - m, W, H), fill=(8, 14, 28, a))
        canvas = Image.alpha_composite(canvas, vig)
        if mix > 0.08:
            draw_sparkles(canvas, t, mix)

    canvas_rgb = apply_shake(canvas.convert("RGB"), shake, t)
    canvas_rgb = flash_white(canvas_rgb, flash)
    canvas = canvas_rgb.convert("RGBA")

    info = chip_at(t)
    if info:
        lines, op, style, size, pop = info
        if t < HOOK_END:
            y = int(H * 0.08)
            chip_block(canvas, y, lines, size=size, opacity=op, style=style, pop=pop)
        elif style == "stamp" and lines == ["רגע."]:
            y = int(H * 0.40)
            chip_block(canvas, y, lines, size=size, opacity=op, style=style, pop=pop)
        elif style == "bf":
            y = int(H * 0.28)
            draw_bf_stack(canvas, y, lines, opacity=op, pop=pop)
        else:
            y = int(H * 0.12)
            chip_block(canvas, y, lines, size=size, opacity=op, style=style, pop=pop)

    if t >= PRODUCT_IN + 0.12:
        paste_logo(canvas, logo, opacity=min(1.0, (t - PRODUCT_IN - 0.12) / 0.4))

    return canvas.convert("RGB")

def make_audio(path: Path):
    sr = 44100
    n = int(DUR * sr)
    t = np.arange(n) / sr
    rng = np.random.default_rng(19)
    beat = 60 / 128

    def adsr(length, a=0.01, d=0.08, s=0.7, r=0.12):
        env = np.ones(length)
        ia, idc, ir = int(a * sr), int(d * sr), int(r * sr)
        if ia:
            env[:ia] = np.linspace(0, 1, ia)
        if idc:
            env[ia : ia + idc] = np.linspace(1, s, idc)
        if ir:
            env[-ir:] = np.linspace(env[-ir] if len(env) else s, 0, ir)
        return env

    # clipper buzz during hook
    buzz = np.zeros(n)
    hook_n = int(HOOK_END * sr)
    tt = np.arange(hook_n) / sr
    buzz[:hook_n] = (
        0.12 * np.sin(2 * np.pi * 85 * tt)
        + 0.08 * np.sin(2 * np.pi * 170 * tt)
        + 0.05 * rng.standard_normal(hook_n)
    ) * (0.55 + 0.45 * np.sin(2 * np.pi * 28 * tt))
    # fade buzz out into stop
    fade = int(0.12 * sr)
    if hook_n > fade:
        buzz[hook_n - fade : hook_n] *= np.linspace(1, 0, fade)

    kick = np.zeros(n)
    snare = np.zeros(n)
    for i, bt in enumerate(np.arange(STOP_END, DUR, beat)):
        i0 = int(bt * sr)
        length = int(0.2 * sr)
        if i0 + length > n:
            break
        tt = np.arange(length) / sr
        freq = 100 * np.exp(-17 * tt) + 40
        amp = 0.40 if i % 2 == 0 else 0.22
        kick[i0 : i0 + length] += amp * np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-10 * tt)
        if i % 2 == 1:
            sl = int(0.08 * sr)
            if i0 + sl <= n:
                noise = rng.standard_normal(sl)
                snare[i0 : i0 + sl] += 0.18 * noise * np.exp(-42 * np.arange(sl) / sr)

    bass = np.zeros(n)
    notes = [73.42, 73.42, 87.31, 65.41]
    bar = 4 * beat
    for bi, start in enumerate(np.arange(STOP_END, DUR, bar)):
        note = notes[bi % len(notes)]
        i0 = int(start * sr)
        length = min(int(bar * sr * 0.88), n - i0)
        if length <= 0:
            break
        tt = np.arange(length) / sr
        wave_b = 0.55 * np.sin(2 * np.pi * note * tt) + 0.22 * np.sin(2 * np.pi * note * 2 * tt)
        bass[i0 : i0 + length] += 0.15 * wave_b * adsr(length)

    impact = np.zeros(n)
    for wt, amp in ((0.04, 0.18), (HOOK_END, 0.62), (PRODUCT_IN, 0.42), (MONTHS_END, 0.52), (SHIP_END, 0.25)):
        i0 = int(wt * sr)
        length = min(int(0.28 * sr), n - i0)
        if length <= 0:
            continue
        tt = np.arange(length) / sr
        impact[i0 : i0 + length] += amp * np.sin(2 * np.pi * (50 * np.exp(-18 * tt)) * tt) * np.exp(-11 * tt)
        noise = np.convolve(rng.standard_normal(length), np.ones(60) / 60, mode="same")
        impact[i0 : i0 + length] += 0.09 * amp * noise * np.sin(np.linspace(0, np.pi, length))

    pad = np.zeros(n)
    for f in (146.83, 174.61, 220.0):
        pad += np.sin(2 * np.pi * f * t)
    pad = pad / 4.5 * 0.045
    pad = np.convolve(pad, np.ones(41) / 41, mode="same")
    pad[: int(STOP_END * sr)] *= 0.15

    bed = buzz + kick + snare + bass + pad + impact
    peak = np.max(np.abs(bed)) + 1e-9
    bed = np.tanh(bed / peak * 0.78) * 0.92
    fi, fo = int(0.04 * sr), int(0.35 * sr)
    bed[:fi] *= np.linspace(0, 1, fi)
    bed[-fo:] *= np.linspace(1, 0, fo)
    audio = np.clip(bed, -1, 1)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(x * 30000)) for x in audio))


def build_grid_cover(bottles: Image.Image) -> Image.Image:
    safe_top = 420
    canvas = Image.new("RGBA", (W, H), (8, 18, 42, 255))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i in range(12, 0, -1):
        r = 120 + i * 45
        gd.ellipse((W // 2 - r, 780 - r, W // 2 + r, 780 + r), fill=(28, 60, 120, max(0, 10 - i)))
    canvas = Image.alpha_composite(canvas, glow)

    im = bottles.convert("RGBA")
    bw = 560
    bh = int(im.height * bw / im.width)
    im = im.resize((bw, bh), Image.Resampling.LANCZOS)
    plate = Image.new("RGBA", (bw + 40, bh + 32), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    pd.rounded_rectangle((0, 0, bw + 40, bh + 32), radius=18, fill=(248, 249, 251, 255))
    bx = (W - (bw + 40)) // 2
    by = safe_top + 20
    canvas.alpha_composite(plate, (bx, by))
    canvas.alpha_composite(im, (bx + 20, by + 16))

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = by + bh + 28

    def measure(text: str, size: int):
        bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), text, font=font(size))
        return bb[2] - bb[0], bb[3] - bb[1]

    def centered(yy, text, size, fill, rtl=True):
        kw = dict(font=font(size), fill=fill, anchor="mm")
        if rtl and any("\u0590" <= c <= "\u05FF" for c in text):
            kw["direction"] = "rtl"
            kw["language"] = "he"
        d.text((W // 2, yy), text, **kw)

    bf = "BLACK FRIDAY"
    ww, hh = measure(bf, 44)
    bfw, bfh = ww + 48, hh + 24
    bfx = (W - bfw) // 2
    d.rounded_rectangle((bfx, y, bfx + bfw, y + bfh), radius=12, fill=(196, 22, 32, 255))
    centered(y + bfh // 2, bf, 44, (255, 255, 255, 255), rtl=False)
    y += bfh + 16

    price = "375₪"
    ww, hh = measure(price, 150)
    pw, ph = ww + 70, hh + 40
    px = (W - pw) // 2
    d.rounded_rectangle((px, y, px + pw, y + ph), radius=26, fill=(0, 0, 0, 250))
    centered(y + ph // 2, price, 150, (255, 255, 255, 255), rtl=False)
    y += ph + 16
    centered(y, "מחיר שובר שוק", 50, (255, 205, 55, 255))
    y += 56
    centered(y, "מינוקסידיל 5% · טיפות · 6 חודשים", 34, (225, 232, 245, 255))
    y += 48
    centered(y, "לגלח… או לחזק?", 34, (165, 180, 210, 255))
    return Image.alpha_composite(canvas, layer).convert("RGB")


def encode_mp4(frames_dir: Path, audio: Path, mp4: Path, start_idx: int = 0, count: int | None = None):
    # ffmpeg image2 from numbered sequence — write a contiguous temp pattern if needed
    pattern = frames_dir / "f_%05d.png"
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-start_number", str(start_idx),
        "-i", str(pattern),
        "-i", str(audio),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest", "-movflags", "+faststart",
        str(mp4),
    ]
    if count is not None:
        cmd.insert(-1, "-frames:v")
        cmd.insert(-1, str(count))
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def render() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    frames = OUT / "frames"
    if frames.exists():
        shutil.rmtree(frames)
    frames.mkdir()

    scalp = load_rgb(ASSETS / "scalp.jpg")
    bottles = load_rgb(ASSETS / "liquid_gall.jpg")
    foam = load_rgb(ASSETS / "foam_gall.jpg")
    logo = prepare_logo(LOGO_PATH, width=260)

    def pad_pack(im: Image.Image, top=0.08, side=0.06, bottom=0.08) -> Image.Image:
        pad_t = int(im.height * top)
        pad_s = int(im.width * side)
        pad_b = int(im.height * bottom)
        out = Image.new("RGB", (im.width + 2 * pad_s, im.height + pad_t + pad_b), (236, 238, 242))
        out.paste(im, (pad_s, pad_t))
        return out

    bottles_p = pad_pack(bottles)
    foam_p = pad_pack(foam)

    cover = build_grid_cover(bottles)
    cover_path = OUT / "MinoxShop_MM_clipper_v4_COVER.jpg"
    cover.save(cover_path, quality=95)

    print(f"Rendering {N} frames (v4 — foam sparkle nod)…")
    for i in range(N):
        im = frame_at(i, scalp, bottles_p, foam_p, logo)
        im.save(frames / f"f_{i:05d}.png")
        if i % 60 == 0:
            print(f"  body {i}/{N}")

    audio = OUT / "audio.wav"
    make_audio(audio)

    mp4 = OUT / "MinoxShop_MM_clipper_v4_16s.mp4"
    encode_mp4(frames, audio, mp4)

    yt_frames = OUT / "frames_yt"
    if yt_frames.exists():
        shutil.rmtree(yt_frames)
    yt_frames.mkdir()
    for i in range(COVER_HOLD_N):
        cover.save(yt_frames / f"f_{i:05d}.png")
    for i in range(N):
        shutil.copy2(frames / f"f_{i:05d}.png", yt_frames / f"f_{COVER_HOLD_N + i:05d}.png")
    with wave.open(str(audio), "rb") as r:
        sr, sw, ch = r.getframerate(), r.getsampwidth(), r.getnchannels()
        body = r.readframes(r.getnframes())
    lead = b"\x00" * (int(COVER_HOLD_SEC * sr) * sw * ch)
    yt_audio = OUT / "audio_yt.wav"
    with wave.open(str(yt_audio), "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(sw)
        w.setframerate(sr)
        w.writeframes(lead + body)
    yt_mp4 = OUT / "MinoxShop_MM_clipper_v4_YT.mp4"
    encode_mp4(yt_frames, yt_audio, yt_mp4)

    ART.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mp4, ART / "DOWNLOAD_MinoxShop_MM_clipper_v4_16s.mp4")
    shutil.copy2(yt_mp4, ART / "DOWNLOAD_MinoxShop_MM_clipper_v4_YT.mp4")
    shutil.copy2(cover_path, ART / "DOWNLOAD_MinoxShop_MM_clipper_v4_COVER.jpg")
    shutil.copy2(mp4, ART / "mm_clipper_v4_demo.mp4")
    for label, sec in (
        ("hook", 0.4),
        ("clipper", 1.4),
        ("stop", 2.7),
        ("product", 4.5),
        ("price", 9.2),
        ("foam", 12.2),
        ("cta", 14.5),
    ):
        frame_at(int(sec * FPS), scalp, bottles_p, foam_p, logo).save(ART / f"mm_v4_preview_{label}.jpg", quality=92)
    cover.save(ART / "mm_v4_preview_cover.jpg", quality=92)
    print("Wrote", mp4)
    print("Wrote", yt_mp4)
    return mp4


if __name__ == "__main__":
    render()
