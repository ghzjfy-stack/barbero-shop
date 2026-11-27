#!/usr/bin/env python3
"""MinoxShop — Women's Rogaine foam v2 (polish pass).

Fixes from v1 review (~7/10):
- Full-bleed product (no floating white card)
- Pure Hebrew chips (no EN tokens that scramble RTL)
- Stronger cover crop + bottom shadow
- Softer motion + longer CTA hold
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

W, H, FPS, DUR = 1080, 1920, 30, 21.5
N = int(round(FPS * DUR))
COVER_HOLD_SEC = 0.85
COVER_HOLD_N = int(round(COVER_HOLD_SEC * FPS))

OUT = Path(os.environ.get("RW_OUT", "/tmp/rogaine-women-v2"))
ART = Path("/opt/cursor/artifacts")
_REPO = Path(__file__).resolve().parent.parent / "reels/rogaine-women-foam-v2/assets"
LOGO_PATH = Path(os.environ.get("MINOX_LOGO", str(_REPO / "main-logo.png")))

FONT = "/usr/share/fonts/truetype/croscore/Arimo-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/croscore/Arimo-Regular.ttf"

HOOK_END = 3.30
STOP_END = 4.55
PRODUCT_IN = 4.65
ID_END = 7.70
MONTHS_END = 10.00
PRICE_END = 13.40
SHIP_END = 16.60


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


def soft_bg() -> Image.Image:
    """Full-bleed soft lilac gradient — atmosphere, not a flat card."""
    arr = np.zeros((H, W, 3), dtype=np.float32)
    for y in range(H):
        u = y / (H - 1)
        # soft vertical wash: lavender → cooler lilac
        r = 236 - 18 * u
        g = 230 - 22 * u
        b = 242 - 8 * u
        arr[y, :, 0] = r
        arr[y, :, 1] = g
        arr[y, :, 2] = b
    # subtle side vignette
    xs = np.linspace(-1, 1, W, dtype=np.float32)
    side = (xs * xs)[None, :, None]
    arr = arr * (1.0 - 0.08 * side)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def cover_window(im: Image.Image, *, zoom: float, focus_x: float, focus_y: float) -> Image.Image:
    zoom = max(1.0, zoom)
    scale = max(W / im.width, H / im.height) * zoom
    nw, nh = max(W + 2, int(im.width * scale)), max(H + 2, int(im.height * scale))
    r = im.resize((nw, nh), Image.Resampling.LANCZOS)
    max_x, max_y = nw - W, nh - H
    x = int(max(0, min(max_x, max_x * focus_x)))
    y = int(max(0, min(max_y, max_y * focus_y)))
    return r.crop((x, y, x + W, y + H))


def knock_white(im: Image.Image, *, thresh: int = 238) -> Image.Image:
    """Remove studio white so product sits on gradient, not a white card."""
    rgba = im.convert("RGBA")
    arr = np.asarray(rgba).astype(np.int16)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    white = (r > thresh) & (g > thresh) & (b > thresh)
    # soft edge: near-white gets partial alpha
    near = (r > thresh - 18) & (g > thresh - 18) & (b > thresh - 18)
    a = a.copy()
    a[white] = 0
    a[near & ~white] = np.minimum(a[near & ~white], 90)
    arr[:, :, 3] = a
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def fit_fullbleed(
    im: Image.Image,
    *,
    zoom: float = 1.0,
    margin_x: float = 0.03,
    margin_y: float = 0.14,
) -> Image.Image:
    """Product on soft gradient — edge-to-edge frame, no white card."""
    zoom = max(0.9, zoom)
    cut = knock_white(im)
    usable_w = int(W * (1 - 2 * margin_x) / zoom)
    usable_h = int(H * (1 - 2 * margin_y) / zoom)
    scale = min(usable_w / cut.width, usable_h / cut.height)
    nw, nh = max(1, int(cut.width * scale)), max(1, int(cut.height * scale))
    r = cut.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = soft_bg().convert("RGBA")
    px, py = (W - nw) // 2, (H - nh) // 2
    # soft drop shadow under product silhouette
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sh = r.split()[-1].point(lambda v: 70 if v > 20 else 0).filter(ImageFilter.GaussianBlur(22))
    dark = Image.new("RGBA", r.size, (30, 14, 50, 255))
    dark.putalpha(sh)
    shadow.alpha_composite(dark, (px, py + 14))
    out = Image.alpha_composite(canvas, shadow)
    out.alpha_composite(r, (px, py))
    return out.convert("RGB")


def grade(im: Image.Image, *, contrast=1.0, bright=1.0, color=1.0) -> Image.Image:
    im = ImageEnhance.Brightness(im).enhance(bright)
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Color(im).enhance(color)
    return im


def phone_photo(im: Image.Image, *, seed: int, strength: float = 1.0) -> Image.Image:
    rng = np.random.default_rng(seed % 10_000)
    arr = np.asarray(im).astype(np.float32)
    noise = rng.standard_normal(arr.shape).astype(np.float32) * (3.2 * strength)
    out = Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8))
    vig = Image.new("RGB", (W, H), (30, 16, 48))
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((-W * 0.1, -H * 0.04, W * 1.1, H * 1.04), fill=int(220 - 30 * strength))
    mask = mask.filter(ImageFilter.GaussianBlur(90))
    return Image.composite(out, Image.blend(out, vig, 0.16 * strength), mask)


def bottom_shadow(canvas: Image.Image, *, top: float = 0.62, strength: float = 0.72) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y0 = int(H * top)
    for i in range(H - y0):
        a = int(255 * strength * ((i / max(1, H - y0)) ** 1.35))
        d.line((0, y0 + i, W, y0 + i), fill=(12, 8, 22, a))
    return Image.alpha_composite(canvas.convert("RGBA"), layer)


def draw_text(d: ImageDraw.ImageDraw, xy, text: str, *, size: int, fill):
    f = font(size)
    bb = d.textbbox((0, 0), text, font=f)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x, y = xy
    d.text((x - tw / 2 - bb[0], y - th / 2 - bb[1]), text, font=f, fill=fill)


def chip_block(canvas: Image.Image, y: int, lines: list[str], *, size: int, opacity: float, style: str, pop: float):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    scale = 0.88 + 0.12 * pop
    cy = y
    for line in lines:
        f = font(int(size * scale))
        bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), line, font=f)
        ww, hh = bb[2] - bb[0], bb[3] - bb[1]
        bw, bh = int(ww + 48), int(hh + 24)
        bx = (W - bw) // 2
        if style == "hook":
            fill = (255, 236, 210, int(248 * opacity))
            text_c = (48, 22, 12, int(255 * opacity))
            radius = 16
        elif style == "stamp":
            fill = (36, 16, 58, int(245 * opacity))
            text_c = (255, 255, 255, int(255 * opacity))
            radius = 20
        else:
            fill = (22, 12, 38, int(236 * opacity))
            text_c = (255, 255, 255, int(255 * opacity))
            radius = 16
        d.rounded_rectangle((bx, cy, bx + bw, cy + bh), radius=radius, fill=fill)
        draw_text(d, (W // 2, cy + bh // 2), line, size=int(size * scale), fill=text_c)
        cy += bh + 14
    canvas.alpha_composite(layer)


def prepare_logo(path: Path, width: int = 170) -> Image.Image:
    logo = Image.open(path).convert("RGBA")
    h = max(1, int(logo.height * width / logo.width))
    return logo.resize((width, h), Image.Resampling.LANCZOS)


def paste_logo(canvas: Image.Image, logo: Image.Image, *, opacity: float):
    if opacity <= 0:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lg = logo.copy()
    a = lg.split()[-1].point(lambda v: int(v * opacity))
    lg.putalpha(a)
    layer.alpha_composite(lg, ((W - lg.width) // 2, H - lg.height - 88))
    canvas.alpha_composite(layer)


def apply_shake(im: Image.Image, shake: float, t: float) -> Image.Image:
    if shake <= 0.01:
        return im
    dx = int(shake * 2.2 * math.sin(t * 31))
    dy = int(shake * 1.8 * math.cos(t * 25))
    out = Image.new("RGB", (W, H), (0, 0, 0))
    out.paste(im, (dx, dy))
    return out


def flash_white(im: Image.Image, amount: float) -> Image.Image:
    if amount <= 0:
        return im
    return Image.blend(im, Image.new("RGB", (W, H), (255, 255, 255)), min(1.0, amount))


def draw_glints(canvas: Image.Image, t: float):
    """Subtle metal glints on cans — polish, not sparkle spam."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pts = [(0.38, 0.36), (0.62, 0.34), (0.45, 0.52), (0.58, 0.55), (0.50, 0.28)]
    for i, (fx, fy) in enumerate(pts):
        phase = (t * 2.4 + i * 0.6) % 1.0
        tw = max(0.0, math.sin(phase * math.pi)) ** 2
        a = int(150 * tw)
        if a < 18:
            continue
        cx, cy = int(W * fx), int(H * fy)
        r = 2 + int(4 * tw)
        d.line((cx - r * 2, cy, cx + r * 2, cy), fill=(255, 255, 255, a), width=2)
        d.line((cx, cy - r * 2, cx, cy + r * 2), fill=(255, 255, 255, a), width=2)
    canvas.alpha_composite(layer)


def draw_bf_stack(canvas: Image.Image, y: int, lines: list[str], *, opacity: float, pop: float):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    scale = 0.86 + 0.14 * pop
    cy = y
    bf = lines[0]
    bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), bf, font=font(42))
    ww, hh = bb[2] - bb[0], bb[3] - bb[1]
    bw, bh = int((ww + 52) * scale), int((hh + 26) * scale)
    bx = (W - bw) // 2
    d.rounded_rectangle((bx, cy, bx + bw, cy + bh), radius=12, fill=(150, 40, 120, int(245 * opacity)))
    draw_text(d, (W // 2, cy + bh // 2), bf, size=int(42 * scale), fill=(255, 255, 255, int(255 * opacity)))
    cy += bh + 16
    price = lines[1]
    bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), price, font=font(int(128 * scale)))
    ww, hh = bb[2] - bb[0], bb[3] - bb[1]
    pw, ph = ww + 70, hh + 42
    px = (W - pw) // 2
    d.rounded_rectangle((px, cy, px + pw, cy + ph), radius=26, fill=(14, 8, 28, int(248 * opacity)))
    for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        draw_text(
            d,
            (W // 2 + ox, cy + ph // 2 + oy),
            price,
            size=int(128 * scale),
            fill=(255, 210, 120, int(255 * opacity)),
        )
    draw_text(d, (W // 2, cy + ph // 2), price, size=int(128 * scale), fill=(255, 255, 255, int(255 * opacity)))
    cy += ph + 16
    sub = lines[2]
    bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), sub, font=font(44))
    ww, hh = bb[2] - bb[0], bb[3] - bb[1]
    sw, sh = ww + 46, hh + 26
    sx = (W - sw) // 2
    d.rounded_rectangle((sx, cy, sx + sw, cy + sh), radius=14, fill=(255, 236, 210, int(242 * opacity)))
    draw_text(d, (W // 2, cy + sh // 2), sub, size=44, fill=(48, 22, 12, int(255 * opacity)))
    canvas.alpha_composite(layer)


def chip_at(t: float):
    def pop_since(start: float, win: float = 0.28) -> float:
        return ease_out(min(1.0, max(0.0, (t - start) / win)))

    if 0.05 <= t < HOOK_END:
        return ["פעם אחת ביום"], 1.0, "hook", 66, pop_since(0.05)
    if HOOK_END + 0.04 <= t < STOP_END:
        return ["זהו."], 1.0, "stamp", 128, pop_since(HOOK_END + 0.04, 0.22)
    if PRODUCT_IN <= t < ID_END:
        return ["קצף לנשים", "חמישה אחוז · פעם ביום"], 1.0, "dark", 50, pop_since(PRODUCT_IN)
    if ID_END <= t < MONTHS_END:
        return ["ארבעה חודשים", "שני מכלים מלאים"], 1.0, "stamp", 52, pop_since(ID_END)
    if MONTHS_END <= t < PRICE_END:
        return ["בלאק פריידי", "₪400", "משלוח חינם עד הבית"], 1.0, "bf", 50, pop_since(MONTHS_END, 0.35)
    if PRICE_END <= t < SHIP_END:
        return ["מקורי מארה״ב", "עד הבית עם שליח"], 1.0, "dark", 46, pop_since(PRICE_END, 0.35)
    if SHIP_END <= t < DUR - 0.08:
        return ["לינק בתגובה", "הזמנה · ₪400"], 1.0, "stamp", 52, pop_since(SHIP_END)
    return None


def beat_camera(t: float):
    if t < HOOK_END:
        z = 1.62 + 0.28 * ease_out(t / HOOK_END) + 0.01 * math.sin(t * 4)
        return z, 0.50, 0.38 + 0.03 * ease_out(t / HOOK_END), 0.0, 0.10
    if t < STOP_END:
        return 1.0, 0.5, 0.5, 0.0, 0.0
    u = t - PRODUCT_IN
    z = 1.0 + 0.045 * min(1.0, u / 8.0) + 0.008 * math.sin(u * 1.2)
    flash = 0.16 if MONTHS_END <= t < MONTHS_END + 0.26 else 0.0
    return z, 0.5, 0.46, flash, 0.03


def frame_at(i: int, cans: Image.Image, box: Image.Image, logo: Image.Image) -> Image.Image:
    t = i / FPS
    zoom, fx, fy, flash, shake = beat_camera(t)

    if t < HOOK_END:
        plate = cover_window(cans, zoom=zoom, focus_x=fx, focus_y=fy)
        plate = grade(plate, contrast=1.16, bright=1.01, color=1.05)
        plate = phone_photo(plate, seed=i, strength=0.7)
        canvas = plate.convert("RGBA")
        draw_glints(canvas, t)
    elif t < STOP_END:
        canvas = Image.new("RGBA", (W, H), (24, 12, 42, 255))
    else:
        # True full-bleed crop into product (no studio-white card / shelf)
        u = min(1.0, max(0.0, (t - PRODUCT_IN) / 7.0))
        if t < MONTHS_END:
            plate = cover_window(box, zoom=1.18 + 0.10 * u, focus_x=0.46, focus_y=0.48)
        else:
            plate = cover_window(cans, zoom=1.42 + 0.12 * u, focus_x=0.50, focus_y=0.40)
        plate = grade(plate, contrast=1.12, bright=1.0, color=1.04)
        plate = phone_photo(plate, seed=i + 17, strength=0.45)
        canvas = plate.convert("RGBA")
        if t >= MONTHS_END:
            draw_glints(canvas, t)
        canvas = bottom_shadow(canvas, top=0.80, strength=0.30)

    canvas_rgb = apply_shake(canvas.convert("RGB"), shake, t)
    canvas_rgb = flash_white(canvas_rgb, flash)
    canvas = canvas_rgb.convert("RGBA")

    info = chip_at(t)
    if info:
        lines, op, style, size, pop = info
        if style == "stamp" and lines == ["זהו."]:
            chip_block(canvas, int(H * 0.42), lines, size=size, opacity=op, style=style, pop=pop)
        elif style == "bf":
            draw_bf_stack(canvas, int(H * 0.05), lines, opacity=op, pop=pop)
        else:
            chip_block(canvas, int(H * 0.065), lines, size=size, opacity=op, style=style, pop=pop)

    if t >= SHIP_END:
        paste_logo(canvas, logo, opacity=min(1.0, (t - SHIP_END) / 0.35))
    return canvas.convert("RGB")


def make_audio(path: Path):
    sr = 44100
    n = int(DUR * sr)
    t = np.arange(n) / sr
    rng = np.random.default_rng(47)
    beat = 60 / 118

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

    shimmer = np.zeros(n)
    hook_n = int(HOOK_END * sr)
    tt = np.arange(hook_n) / sr
    shimmer[:hook_n] = (
        0.18 * np.sin(2 * np.pi * 523 * tt)
        + 0.11 * np.sin(2 * np.pi * 784 * tt)
        + 0.07 * np.sin(2 * np.pi * 1046 * tt)
        + 0.05 * rng.standard_normal(hook_n)
    ) * (0.35 + 0.65 * (tt / max(tt[-1], 1e-6)))

    mute = np.ones(n)
    mute[int(HOOK_END * sr) : int(STOP_END * sr)] = 0.05

    kick = np.zeros(n)
    snare = np.zeros(n)
    for i, bt in enumerate(np.arange(STOP_END, DUR, beat)):
        i0 = int(bt * sr)
        length = int(0.20 * sr)
        if i0 + length > n:
            break
        tt = np.arange(length) / sr
        freq = 98 * np.exp(-15 * tt) + 40
        amp = 0.54 if i % 2 == 0 else 0.32
        kick[i0 : i0 + length] += amp * np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-9 * tt)
        if i % 2 == 1:
            sl = int(0.08 * sr)
            if i0 + sl <= n:
                snare[i0 : i0 + sl] += 0.26 * rng.standard_normal(sl) * np.exp(-40 * np.arange(sl) / sr)

    bass = np.zeros(n)
    notes = [82.41, 82.41, 98.0, 73.42]
    bar = 4 * beat
    for bi, start in enumerate(np.arange(STOP_END, DUR, bar)):
        note = notes[bi % len(notes)]
        i0 = int(start * sr)
        length = min(int(bar * sr * 0.85), n - i0)
        if length <= 0:
            break
        tt = np.arange(length) / sr
        wave_b = 0.55 * np.sin(2 * np.pi * note * tt) + 0.22 * np.sin(2 * np.pi * note * 2 * tt)
        bass[i0 : i0 + length] += 0.25 * wave_b * adsr(length)

    impact = np.zeros(n)
    for wt, amp in ((HOOK_END, 0.88), (PRODUCT_IN, 0.62), (MONTHS_END, 1.08), (SHIP_END, 0.44)):
        i0 = int(wt * sr)
        length = min(int(0.32 * sr), n - i0)
        if length <= 0:
            continue
        tt = np.arange(length) / sr
        impact[i0 : i0 + length] += amp * np.sin(2 * np.pi * (55 * np.exp(-14 * tt)) * tt) * np.exp(-9 * tt)

    riser = np.zeros(n)
    r0 = int((MONTHS_END - 0.45) * sr)
    rl = int(0.45 * sr)
    if r0 > 0 and r0 + rl < n:
        tt = np.arange(rl) / sr
        riser[r0 : r0 + rl] = 0.24 * np.sin(2 * np.pi * (260 + 720 * (tt / 0.45)) * tt) * (tt / 0.45)

    pad = np.zeros(n)
    for f in (164.81, 196.0, 246.94):
        pad += np.sin(2 * np.pi * f * t)
    pad = pad / 5.0 * 0.075
    pad[: int(STOP_END * sr)] *= 0.12

    bed = (shimmer + kick + snare + bass + pad + impact + riser) * mute
    gate = np.ones(n)
    gate[int(PRODUCT_IN * sr) :] = 1.18
    gate[int(MONTHS_END * sr) :] = 1.32
    bed = bed * gate
    peak = np.max(np.abs(bed)) + 1e-9
    bed = np.tanh(bed / peak * 1.18) * 0.98
    fi, fo = int(0.03 * sr), int(0.24 * sr)
    bed[:fi] *= np.linspace(0, 1, fi)
    bed[-fo:] *= np.linspace(1, 0, fo)
    audio = np.clip(bed, -1, 1)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(x * 32750)) for x in audio))


def build_hook_cover(cans: Image.Image) -> Image.Image:
    plate = cover_window(cans, zoom=1.88, focus_x=0.50, focus_y=0.36)
    plate = grade(plate, contrast=1.18, bright=0.98, color=1.04)
    plate = phone_photo(plate, seed=11, strength=0.85)
    canvas = plate.convert("RGBA")
    draw_glints(canvas, 0.55)
    canvas = bottom_shadow(canvas, top=0.58, strength=0.78)
    chip_block(canvas, int(H * 0.07), ["פעם אחת ביום"], size=68, opacity=1.0, style="hook", pop=1.0)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = int(H * 0.76)
    price = "₪400"
    bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), price, font=font(112))
    ww, hh = bb[2] - bb[0], bb[3] - bb[1]
    pw, ph = ww + 60, hh + 30
    px = (W - pw) // 2
    d.rounded_rectangle((px, y, px + pw, y + ph), radius=24, fill=(14, 8, 28, 240))
    for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        draw_text(d, (W // 2 + ox, y + ph // 2 + oy), price, size=112, fill=(255, 210, 120, 255))
    draw_text(d, (W // 2, y + ph // 2), price, size=112, fill=(255, 255, 255, 255))
    y += ph + 16
    draw_text(d, (W // 2, y), "ארבעה חודשים · משלוח חינם", size=34, fill=(255, 236, 210, 255))
    return Image.alpha_composite(canvas, layer).convert("RGB")


def loudness_boost(src: Path, dst: Path):
    af = (
        "acompressor=threshold=-17dB:ratio=4.5:attack=5:release=55:makeup=8.5,"
        "alimiter=limit=0.90:attack=1:release=40:level=disabled,"
        "loudnorm=I=-9:TP=-1.2:LRA=7"
    )
    subprocess.check_call(
        ["ffmpeg", "-y", "-i", str(src), "-af", af, "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le", str(dst)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def encode_mp4(frames_dir: Path, audio: Path, mp4: Path, start_idx: int = 0):
    subprocess.check_call(
        [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-start_number", str(start_idx),
            "-i", str(frames_dir / "f_%05d.png"),
            "-i", str(audio),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart",
            str(mp4),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def render() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    frames = OUT / "frames"
    if frames.exists():
        shutil.rmtree(frames)
    frames.mkdir()

    cans = load_rgb(_REPO / "cans.jpg")
    box = load_rgb(_REPO / "box.png")
    logo = prepare_logo(LOGO_PATH if LOGO_PATH.exists() else _REPO / "main-logo.png")

    def pad(im: Image.Image, top=0.04, side=0.03, bottom=0.04) -> Image.Image:
        # Keep transparent-ish pad on soft bg color (no white card)
        pt, ps, pb = int(im.height * top), int(im.width * side), int(im.height * bottom)
        bg = (236, 230, 242)
        out = Image.new("RGB", (im.width + 2 * ps, im.height + pt + pb), bg)
        out.paste(im, (ps, pt))
        return out

    cans_p, box_p = pad(cans), pad(box, top=0.02, side=0.02, bottom=0.02)

    cover = build_hook_cover(cans)
    cover_path = OUT / "MinoxShop_Rogaine_women_v2_COVER.jpg"
    cover.save(cover_path, quality=95)

    print(f"Rendering {N} frames (Rogaine women foam v2 polish)…")
    for i in range(N):
        frame_at(i, cans_p, box_p, logo).save(frames / f"f_{i:05d}.png")
        if i % 60 == 0:
            print(f"  body {i}/{N}")

    audio_raw, audio = OUT / "audio_raw.wav", OUT / "audio.wav"
    make_audio(audio_raw)
    loudness_boost(audio_raw, audio)

    mp4 = OUT / "MinoxShop_Rogaine_women_v2_22s.mp4"
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
    yt_mp4 = OUT / "MinoxShop_Rogaine_women_v2_YT.mp4"
    encode_mp4(yt_frames, yt_audio, yt_mp4)

    ART.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mp4, ART / "DOWNLOAD_MinoxShop_Rogaine_women_v2_22s.mp4")
    shutil.copy2(yt_mp4, ART / "DOWNLOAD_MinoxShop_Rogaine_women_v2_YT.mp4")
    shutil.copy2(cover_path, ART / "DOWNLOAD_MinoxShop_Rogaine_women_v2_COVER.jpg")
    shutil.copy2(mp4, ART / "rogaine_women_v2_demo.mp4")
    for label, sec in (("hook", 0.5), ("stop", 3.9), ("box", 5.8), ("months", 8.8), ("price", 11.5), ("cta", 18.0)):
        frame_at(int(sec * FPS), cans_p, box_p, logo).save(ART / f"rw_v2_preview_{label}.jpg", quality=92)
    cover.save(ART / "rw_v2_preview_cover.jpg", quality=92)
    print("Wrote", mp4)
    print("Wrote", yt_mp4)
    return mp4


if __name__ == "__main__":
    render()
