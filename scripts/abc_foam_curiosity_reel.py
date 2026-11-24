#!/usr/bin/env python3
"""MinoxShop Amazon Basic Care — curiosity reel v8 VIEW-OPS.

Copies patterns from top commerce Shorts/Reels/TikTok (no UGC needed):
- Frame-0 hook text · jump-cuts every ~2s · BF stamp · price-smash reveal
- Handheld micro-shake · impact SFX on cuts · soft end-loop to box

15s · Hebrew chips · CTA הקישור בפרופיל · MinoxShop logo
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

W, H, FPS, DUR = 1080, 1920, 30, 15
N = FPS * DUR
# YouTube Shorts can't set a custom thumb — hold the grid cover on frame 0
# so uploaders can pick it (IG/TikTok still use the separate COVER.jpg).
COVER_HOLD_SEC = 0.8
COVER_HOLD_N = int(round(COVER_HOLD_SEC * FPS))

ASSETS = Path(os.environ.get("ABC_ASSETS", "/tmp/minox-amazon"))
OUT = Path(os.environ.get("ABC_OUT", "/tmp/abc-foam-curiosity"))
ART = Path("/opt/cursor/artifacts")

FONT = "/usr/share/fonts/truetype/croscore/Arimo-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/croscore/Arimo-Regular.ttf"
INK = (16, 18, 22)


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT if bold else FONT_REG, size)


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * t


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 3 * t * t - 2 * t * t * t


def load_rgb(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def cover_window(
    im: Image.Image,
    *,
    zoom: float,
    focus_x: float,
    focus_y: float,
) -> Image.Image:
    """Full-bleed cover. zoom≥1. focus 0..1 = crop anchor."""
    zoom = max(1.0, zoom)
    scale = max(W / im.width, H / im.height) * zoom
    nw, nh = max(W + 2, int(im.width * scale)), max(H + 2, int(im.height * scale))
    r = im.resize((nw, nh), Image.Resampling.LANCZOS)
    max_x, max_y = nw - W, nh - H
    x = int(max(0, min(max_x, max_x * focus_x)))
    y = int(max(0, min(max_y, max_y * focus_y)))
    return r.crop((x, y, x + W, y + H))


def grade(im: Image.Image, *, contrast: float = 1.08, bright: float = 0.96) -> Image.Image:
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Color(im).enhance(1.06)
    im = ImageEnhance.Brightness(im).enhance(bright)
    base = im.convert("RGBA")
    # Soft top veil for chip readability only
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(veil)
    for y in range(0, int(H * 0.22)):
        a = int(95 * (1 - y / (H * 0.22)) ** 1.2)
        vd.line((0, y, W, y), fill=(8, 12, 20, a))
    # Light vignette
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vgd = ImageDraw.Draw(vig)
    for i in range(6):
        pad = 28 + i * 50
        vgd.rectangle((0, 0, W, H), outline=(0, 0, 0, 5 + i * 5), width=pad)
    vig = vig.filter(ImageFilter.GaussianBlur(28))
    out = Image.alpha_composite(base, veil)
    return Image.alpha_composite(out, vig)


def add_grain(im: Image.Image, amount: float = 0.01, seed: int = 0) -> Image.Image:
    rng = np.random.default_rng(seed)
    arr = np.array(im.convert("RGBA")).astype(np.float32)
    noise = rng.standard_normal(arr.shape[:2]) * (255 * amount)
    arr[..., :3] = np.clip(arr[..., :3] + noise[..., None], 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def flash_white(im: Image.Image, amount: float) -> Image.Image:
    if amount <= 0.01:
        return im
    white = Image.new("RGBA", im.size, (255, 255, 255, int(220 * amount)))
    return Image.alpha_composite(im.convert("RGBA"), white)


def draw_text(draw, xy, text, *, size=64, fill=(255, 255, 255), anchor="mm", bold=True):
    f = font(size, bold=bold)
    kwargs = dict(font=f, fill=fill, anchor=anchor)
    if any("\u0590" <= ch <= "\u05FF" for ch in text):
        kwargs["direction"] = "rtl"
        kwargs["language"] = "he"
    draw.text(xy, text, **kwargs)


def chip_block(
    canvas,
    cy,
    lines,
    *,
    size=48,
    opacity=1.0,
    slide_x=0.0,
    pop=1.0,
    style: str = "clean",
    rotate: float = 0.0,
):
    """clean = white pill · stamp = BF tilted badge · smash = giant price."""
    if opacity <= 0.02:
        return
    size = max(28, int(size * pop))
    f = font(size)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    widths, heights = [], []
    for line in lines:
        bbox = probe.textbbox((0, 0), line, font=f, direction="rtl", language="he")
        widths.append(bbox[2] - bbox[0])
        heights.append(bbox[3] - bbox[1])
    pad_x, pad_y, gap = (52, 24, 10) if style != "smash" else (40, 28, 6)
    pw = max(widths) + pad_x * 2
    ph = sum(heights) + gap * (len(lines) - 1) + pad_y * 2
    chip = Image.new("RGBA", (pw + 12, ph + 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(chip)
    if style == "stamp":
        d.rounded_rectangle((4, 6, pw + 4, ph + 6), radius=18, fill=(0, 0, 0, int(120 * opacity)))
        d.rounded_rectangle((0, 0, pw, ph), radius=18, fill=(16, 18, 22, int(240 * opacity)))
        d.rounded_rectangle((0, 0, pw, ph), radius=18, outline=(255, 205, 60, int(230 * opacity)), width=5)
        ink = (255, 255, 255)
    elif style == "smash":
        d.rounded_rectangle((3, 5, pw + 3, ph + 5), radius=28, fill=(0, 0, 0, int(110 * opacity)))
        d.rounded_rectangle((0, 0, pw, ph), radius=28, fill=(255, 255, 255, int(245 * opacity)))
        ink = INK
    else:
        d.rounded_rectangle((3, 4, pw + 3, ph + 4), radius=24, fill=(0, 0, 0, int(100 * opacity)))
        d.rounded_rectangle((0, 0, pw, ph), radius=24, fill=(255, 255, 255, int(240 * opacity)))
        ink = INK
    y = pad_y
    for i, (line, th) in enumerate(zip(lines, heights)):
        fill = (255, 255, 255) if style == "stamp" else ink
        draw_text(d, (pw // 2, y + th // 2), line, size=size, fill=(*fill, int(255 * opacity)))
        y += th + gap
    if abs(rotate) > 0.2:
        chip = chip.rotate(rotate, resample=Image.Resampling.BICUBIC, expand=True)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x0 = (W - chip.width) // 2 + int(slide_x)
    y0 = cy - chip.height // 2
    layer.alpha_composite(chip, (x0, y0))
    canvas.alpha_composite(layer)


def chip_at(t: float):
    """Readable pacing: ~2s for 2-line chips, ~1.2s+ for short lines, punchy 395."""
    # returns lines, opacity, slide_x, pop, style, rotate
    if 0.0 <= t < 2.4:
        if t < 0.14:
            return (["מה יש בקופסה הכחולה", "מארה״ב?"], ease_out(t / 0.14), 48 * (1 - ease_out(t / 0.14)), 1.0 + 0.12 * ease_out(t / 0.14), "clean", 0.0)
        if t > 2.2:
            return (["מה יש בקופסה הכחולה", "מארה״ב?"], 1 - ease_in((t - 2.2) / 0.2), 0.0, 1.0, "clean", 0.0)
        return (["מה יש בקופסה הכחולה", "מארה״ב?"], 1.0, 0.0, 1.0, "clean", 0.0)
    if 2.45 <= t < 3.7:
        local = t - 2.45
        op = ease_out(min(1, local / 0.12))
        if t > 3.5:
            op = 1 - ease_in((t - 3.5) / 0.2)
        rot = -7 + 3 * ease_out(min(1, local / 0.25))
        return (["BLACK FRIDAY"], op, 0.0, 1.22 if local < 0.22 else 1.06, "stamp", rot)
    if 3.8 <= t < 5.95:
        local = t - 3.8
        op = ease_out(min(1, local / 0.14))
        if t > 5.75:
            op = 1 - ease_in((t - 5.75) / 0.2)
        return (["מינוקסידיל 5%", "לחיזוק וצמיחת השיער"], op, -24 * (1 - ease_out(min(1, local / 0.22))), 1.1 if local < 0.22 else 1.0, "clean", 0.0)
    if 6.0 <= t < 7.25:
        local = t - 6.0
        op = ease_out(min(1, local / 0.12))
        if t > 7.05:
            op = 1 - ease_in((t - 7.05) / 0.2)
        return (["חשבתם שזה יקר?"], op, 32 * (1 - ease_out(min(1, local / 0.2))), 1.12 if local < 0.2 else 1.0, "clean", 0.0)
    if 7.3 <= t < 8.4:
        local = t - 7.3
        op = ease_out(min(1, local / 0.1))
        if t > 8.2:
            op = 1 - ease_in((t - 8.2) / 0.2)
        return (["395₪"], op, 0.0, 1.32 if local < 0.2 else 1.16, "smash", 0.0)
    if 8.45 <= t < 9.85:
        local = t - 8.45
        op = ease_out(min(1, local / 0.12))
        if t > 9.65:
            op = 1 - ease_in((t - 9.65) / 0.2)
        return (["מחיר שובר שוק", "3 חודשים"], op, 0.0, 1.1 if local < 0.22 else 1.0, "smash", 0.0)
    if 9.9 <= t < 11.25:
        local = t - 9.9
        op = ease_out(min(1, local / 0.12))
        if t > 11.05:
            op = 1 - ease_in((t - 11.05) / 0.2)
        return (["קצף לגברים · יבוא מארה״ב"], op, 0.0, 1.06 if local < 0.2 else 1.0, "clean", 0.0)
    if 11.3 <= t < 12.9:
        local = t - 11.3
        op = ease_out(min(1, local / 0.12))
        if t > 12.7:
            op = 1 - ease_in((t - 12.7) / 0.2)
        return (["משלוח חינם עד הבית", "עם שליח"], op, 0.0, 1.06 if local < 0.2 else 1.0, "clean", 0.0)
    if 12.95 <= t < 13.75:
        local = t - 12.95
        op = ease_out(min(1, local / 0.12))
        if t > 13.55:
            op = 1 - ease_in((t - 13.55) / 0.2)
        return (["אנחנו פה בשבילכם"], op, 0.0, 1.08 if local < 0.2 else 1.0, "clean", 0.0)
    if 13.8 <= t <= 15.01:
        local = t - 13.8
        return (["הקישור בפרופיל"], ease_out(min(1, local / 0.18)), 0.0, 1.1 if local < 0.22 else 1.0, "clean", 0.0)
    return None


def beat_camera(t: float) -> tuple[float, float, float, float, float]:
    """zoom, focus_x, focus_y, flash, shake — synced to readable chip beats."""
    cuts = [0.0, 2.0, 2.45, 3.8, 6.0, 7.3, 8.45, 9.9, 11.3, 12.95, 13.8]
    fx_cycle = [0.42, 0.58, 0.48, 0.55, 0.45, 0.50, 0.52, 0.46, 0.54, 0.50, 0.50]

    def seg(i0, i1):
        a, b = cuts[i0], cuts[i1] if i1 < len(cuts) else DUR
        local = (t - a) / max(0.01, b - a)
        flash = 0.45 * (1 - local / 0.1) if local < 0.1 else 0.0
        shake = 8.0 * (1 - local / 0.12) if local < 0.12 else 2.0
        fx = fx_cycle[i0] + (fx_cycle[min(i0 + 1, len(fx_cycle) - 1)] - fx_cycle[i0]) * ease_out(min(1, local))
        return local, flash, shake, fx

    if t < 2.45:
        local = t / 2.45
        flash = 0.28 * (1 - t / 0.18) if t < 0.18 else 0.0
        return 1.0, 0.42 + 0.12 * ease_out(local), 0.5, flash, 2.5 + 1.5 * math.sin(t * 11)
    if t < 3.8:
        _, flash, shake, fx = seg(2, 3)
        return 1.0, fx, 0.5, max(flash, 0.6 * (1 - (t - 2.45) / 0.12) if t < 2.57 else 0), shake
    if t < 6.0:
        _, flash, shake, fx = seg(3, 4)
        return 1.0, fx, 0.5, flash, shake
    if t < 7.3:
        _, flash, shake, fx = seg(4, 5)
        return 1.0, fx, 0.5, flash, shake
    if t < 8.45:
        local = (t - 7.3) / 1.15
        flash = 0.65 * (1 - local / 0.1) if local < 0.1 else 0.0
        return 1.0, 0.50, 0.5, flash, 12 * (1 - min(1, local / 0.15)) + 2
    if t < 9.9:
        _, flash, shake, fx = seg(6, 7)
        return 1.0, fx, 0.5, flash, shake
    if t < 11.3:
        _, flash, shake, fx = seg(7, 8)
        return 1.0, fx, 0.5, flash, shake
    if t < 12.95:
        _, flash, shake, fx = seg(8, 9)
        return 1.0, fx, 0.5, flash, shake
    if t < 13.8:
        return 1.0, 0.50, 0.5, 0.0, 1.8
    local = (t - 13.8) / 1.2
    flash = 0.28 * (1 - local / 0.1) if local < 0.1 else 0.0
    return 1.0, 0.50, 0.5, flash, 2.0


def foam_sparkles(canvas: Image.Image, t: float, seed: int = 7) -> None:
    """Rising foam dots — denser after reveal for motion without looking like falling hair."""
    if t < 2.2:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    life = min(1.0, (t - 2.2) / 0.45)
    for i in range(28):
        x = int((0.08 + 0.84 * ((i * 37 % 100) / 100)) * W)
        speed = 32 + (i * 17 % 48)
        y = int(H * 0.94 - ((t * speed * 9 + i * 80) % (H * 0.8)))
        r = 3 + (i % 5)
        a = int((70 + (i % 5) * 10) * life * (0.5 + 0.5 * abs(math.sin(t * 2.1 + i))))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, a))
    canvas.alpha_composite(layer)


def apply_shake(im: Image.Image, amount: float, t: float) -> Image.Image:
    if amount < 0.5:
        return im
    dx = int(amount * math.sin(t * 53.0))
    dy = int(amount * 0.7 * math.cos(t * 41.0))
    out = Image.new("RGB", (W, H), (18, 20, 24))
    out.paste(im.convert("RGB"), (dx, dy))
    return out


def whip_smear(im: Image.Image, t: float) -> Image.Image:
    """Brief horizontal smear on jump-cut frames — native Shorts feel."""
    cuts = (2.45, 3.8, 6.0, 7.3, 8.45, 9.9, 11.3, 13.8)
    strength = 0.0
    for c in cuts:
        if abs(t - c) < 0.07:
            strength = max(strength, 1.0 - abs(t - c) / 0.07)
    if strength < 0.15:
        return im
    blurred = im.filter(ImageFilter.GaussianBlur(radius=1.2 + 3.5 * strength))
    return Image.blend(im.convert("RGB"), blurred.convert("RGB"), 0.55 * strength)


def prepare_logo(path: Path, width: int = 210) -> Image.Image:
    """Knock out near-white plate so logo sits clean on the reel."""
    im = Image.open(path).convert("RGBA")
    arr = np.array(im)
    rgb = arr[..., :3].astype(np.int16)
    white = (rgb[:, :, 0] > 232) & (rgb[:, :, 1] > 232) & (rgb[:, :, 2] > 225)
    arr[..., 3] = np.where(white, 0, 255).astype(np.uint8)
    im = Image.fromarray(arr, "RGBA")
    bbox = im.getbbox()
    if bbox:
        im = im.crop(bbox)
    h = max(1, int(im.height * width / im.width))
    return im.resize((width, h), Image.Resampling.LANCZOS)


def paste_logo(canvas: Image.Image, logo: Image.Image, *, opacity: float = 0.92) -> None:
    if opacity <= 0.02:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lw, lh = logo.size
    x = (W - lw) // 2
    y = H - lh - 110
    # soft white pillow so it matches other MinoxShop reels
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


def frame_at(i: int, box: Image.Image, trio: Image.Image, logo: Image.Image) -> Image.Image:
    t = i / FPS
    zoom, fx, fy, flash, shake = beat_camera(t)
    src = box if t < 2.45 else trio
    plate = cover_window(src, zoom=zoom, focus_x=fx, focus_y=fy)
    if t >= 14.4:
        box_plate = cover_window(box, zoom=1.0, focus_x=0.50, focus_y=0.5)
        plate = Image.blend(plate.convert("RGB"), box_plate.convert("RGB"), ease_in((t - 14.4) / 0.6))
    plate = apply_shake(plate, shake, t)
    plate = whip_smear(plate, t)
    canvas = grade(plate)
    canvas = flash_white(canvas, flash)
    foam_sparkles(canvas, t, seed=7)
    info = chip_at(t)
    if info:
        lines, op, slide, pop, style, rot = info
        size = 50 if len(lines) > 1 else 56
        if style == "stamp":
            size = 64
        if style == "smash" and lines == ["395₪"]:
            size = 92
        elif style == "smash":
            size = 58
        if lines and lines[0] == "מינוקסידיל 5%":
            size = 52
        if lines == ["הקישור בפרופיל"]:
            size = 60
        chip_block(
            canvas,
            int(H * 0.14),
            lines,
            size=size,
            opacity=op,
            slide_x=slide,
            pop=pop,
            style=style,
            rotate=rot,
        )
    if t >= 2.4:
        lo = ease_out(min(1.0, (t - 2.4) / 0.4))
        paste_logo(canvas, logo, opacity=0.9 * lo)
    return add_grain(canvas, amount=0.012, seed=i * 23 + 2).convert("RGB")


def make_audio(path: Path) -> None:
    """Punchier commerce bed — kicks + impacts synced to jump-cuts."""
    sr = 44100
    n = int(DUR * sr)
    rng = np.random.default_rng(11)
    t = np.arange(n) / sr
    bpm = 126
    beat = 60 / bpm

    def adsr(length, a=0.01, d=0.08, s=0.7, r=0.1):
        a_n, d_n = int(a * sr), int(d * sr)
        r_n = int(r * sr)
        s_n = max(0, length - a_n - d_n - r_n)
        e = np.concatenate(
            [np.linspace(0, 1, a_n), np.linspace(1, s, d_n), np.full(s_n, s), np.linspace(s, 0, r_n)]
        )
        return e[:length]

    kick = np.zeros(n)
    snare = np.zeros(n)
    for i, bt in enumerate(np.arange(0, DUR, beat)):
        i0 = int(bt * sr)
        length = int(0.2 * sr)
        if i0 + length > n:
            break
        tt = np.arange(length) / sr
        freq = 100 * np.exp(-17 * tt) + 40
        amp = 0.42 if i % 2 == 0 else 0.24
        kick[i0 : i0 + length] += amp * np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-10 * tt)
        if i % 2 == 1:
            sl = int(0.08 * sr)
            if i0 + sl <= n:
                noise = rng.standard_normal(sl)
                snare[i0 : i0 + sl] += 0.2 * noise * np.exp(-42 * np.arange(sl) / sr)

    bass = np.zeros(n)
    notes = [73.42, 73.42, 87.31, 65.41]
    bar = 4 * beat
    for bi, start in enumerate(np.arange(0, DUR, bar)):
        note = notes[bi % len(notes)]
        i0 = int(start * sr)
        length = min(int(bar * sr * 0.88), n - i0)
        if length <= 0:
            break
        tt = np.arange(length) / sr
        wave_b = 0.55 * np.sin(2 * np.pi * note * tt) + 0.22 * np.sin(2 * np.pi * note * 2 * tt)
        bass[i0 : i0 + length] += 0.16 * wave_b * adsr(length)

    pad = np.zeros(n)
    for f in (146.83, 174.61, 220.0):
        pad += np.sin(2 * np.pi * f * (1 + 0.002 * rng.standard_normal()) * t)
    pad = pad / 4.2 * 0.06 * (0.8 + 0.2 * np.sin(2 * np.pi * 0.12 * t))
    pad = np.convolve(pad, np.ones(41) / 41, mode="same")

    pluck = np.zeros(n)
    melody = [
        (0.4, 293.66, 0.3),
        (2.25, 392.0, 0.28),
        (3.8, 440.0, 0.3),
        (5.55, 349.23, 0.25),
        (6.5, 523.25, 0.35),
        (8.7, 392.0, 0.3),
        (10.2, 349.23, 0.35),
        (13.1, 293.66, 0.4),
    ]
    for st, freq, length_s in melody:
        i0 = int(st * sr)
        length = min(int(length_s * sr), n - i0)
        if length <= 0:
            continue
        tt = np.arange(length) / sr
        tone = np.sin(2 * np.pi * freq * tt) * np.exp(-2.8 * tt)
        tone += 0.2 * np.sin(2 * np.pi * freq * 2 * tt) * np.exp(-5 * tt)
        pluck[i0 : i0 + length] += 0.1 * tone

    whoosh = np.zeros(n)
    impact = np.zeros(n)
    for wt, amp in ((0.04, 0.16), (2.45, 0.34), (3.8, 0.26), (6.0, 0.22), (7.3, 0.4), (8.45, 0.28), (11.3, 0.2), (13.8, 0.22)):
        i0 = int(wt * sr)
        length = min(int(0.26 * sr), n - i0)
        if length <= 0:
            continue
        noise = np.convolve(rng.standard_normal(length), np.ones(80) / 80, mode="same")
        env = np.sin(np.linspace(0, np.pi, length)) ** 1.4
        whoosh[i0 : i0 + length] += 0.07 * amp * noise * env
        # sub impact thump
        tt = np.arange(length) / sr
        impact[i0 : i0 + length] += amp * 0.35 * np.sin(2 * np.pi * (55 * np.exp(-20 * tt)) * tt) * np.exp(-12 * tt)

    bed = kick + snare + bass + pad + pluck + whoosh + impact
    quiet = int(0.06 * sr)
    bed[:quiet] *= np.linspace(0.6, 1, quiet)
    peak = np.max(np.abs(bed)) + 1e-9
    bed = np.tanh(bed / peak * 0.72 * 1.1) * 0.92
    bed = np.convolve(bed, np.ones(4) / 4, mode="same")
    fi, fo = int(0.08 * sr), int(0.45 * sr)
    bed[:fi] *= np.linspace(0, 1, fi)
    bed[-fo:] *= np.linspace(1, 0, fo)
    audio = np.clip(bed, -1, 1)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(x * 30000)) for x in audio))


def build_grid_cover(box_src: Image.Image) -> Image.Image:
    """Navy BF + 395₪ cover — center-safe for IG grid + YT Shorts frame-0 thumb."""
    safe_top = 420
    canvas = Image.new("RGBA", (W, H), (8, 18, 42, 255))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i in range(12, 0, -1):
        r = 120 + i * 45
        gd.ellipse((W // 2 - r, 780 - r, W // 2 + r, 780 + r), fill=(28, 60, 120, max(0, 10 - i)))
    canvas = Image.alpha_composite(canvas, glow)

    box = box_src.convert("RGBA")
    bw = 500
    bh = int(box.height * bw / box.width)
    box = box.resize((bw, bh), Image.Resampling.LANCZOS)
    plate = Image.new("RGBA", (bw + 40, bh + 32), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    pd.rounded_rectangle((0, 0, bw + 40, bh + 32), radius=18, fill=(248, 249, 251, 255))
    bx = (W - (bw + 40)) // 2
    by = safe_top + 28
    canvas.alpha_composite(plate, (bx, by))
    canvas.alpha_composite(box, (bx + 20, by + 16))

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = by + bh + 32 + 18

    def measure(text: str, size: int) -> tuple[int, int]:
        bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), text, font=font(size))
        return bb[2] - bb[0], bb[3] - bb[1]

    def centered(yy: int, text: str, size: int, fill: tuple[int, ...], *, rtl: bool = True) -> None:
        kw: dict = dict(font=font(size), fill=fill, anchor="mm")
        if rtl and any("\u0590" <= c <= "\u05FF" for c in text):
            kw["direction"] = "rtl"
            kw["language"] = "he"
        d.text((W // 2, yy), text, **kw)

    bf = "BLACK FRIDAY"
    ww, hh = measure(bf, 46)
    bfw, bfh = ww + 52, hh + 26
    bfx = (W - bfw) // 2
    d.rounded_rectangle((bfx, y, bfx + bfw, y + bfh), radius=12, fill=(196, 22, 32, 255))
    centered(y + bfh // 2, bf, 46, (255, 255, 255, 255), rtl=False)
    y += bfh + 18

    price = "395₪"
    ww, hh = measure(price, 160)
    pw, ph = ww + 80, hh + 44
    px = (W - pw) // 2
    d.rounded_rectangle((px, y, px + pw, y + ph), radius=28, fill=(0, 0, 0, 250))
    centered(y + ph // 2, price, 160, (255, 255, 255, 255), rtl=False)
    y += ph + 20

    centered(y, "מחיר שובר שוק", 54, (255, 205, 55, 255))
    y += 62
    centered(y, "מינוקסידיל 5% · 3 חודשים קצף", 36, (225, 232, 245, 255))
    y += 52
    centered(y, "מה יש בקופסה הכחולה מארה״ב?", 34, (165, 180, 210, 255))
    return Image.alpha_composite(canvas, layer).convert("RGB")


def render() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    frames = OUT / "frames"
    if frames.exists():
        shutil.rmtree(frames)
    frames.mkdir()

    cans = load_rgb(ASSETS / "cans.png")
    box_src = load_rgb(ASSETS / "box.png")
    logo_path = Path(os.environ.get("MINOX_LOGO", "/tmp/minox-mp/main-logo.png"))
    logo = prepare_logo(logo_path, width=210)

    def pad_pack(im: Image.Image, top: float = 0.22, side: float = 0.08, bottom: float = 0.08) -> Image.Image:
        pad_t = int(im.height * top)
        pad_s = int(im.width * side)
        pad_b = int(im.height * bottom)
        out = Image.new("RGB", (im.width + 2 * pad_s, im.height + pad_t + pad_b), (236, 238, 242))
        out.paste(im, (pad_s, pad_t))
        return out

    trio = pad_pack(cans, top=0.26, side=0.12, bottom=0.14)
    box = pad_pack(box_src, top=0.22, side=0.14, bottom=0.12)

    cover = build_grid_cover(box_src)
    cover_path = OUT / "MinoxShop_ABC_curiosity_COVER.jpg"
    cover.save(cover_path, quality=95)

    total = COVER_HOLD_N + N
    print(f"Rendering {total} frames ({COVER_HOLD_SEC:.1f}s cover hold + v8 body)…")
    for i in range(COVER_HOLD_N):
        cover.save(frames / f"f_{i:05d}.png")
    for i in range(N):
        im = frame_at(i, box, trio, logo)
        im.save(frames / f"f_{COVER_HOLD_N + i:05d}.png")
        if i % 60 == 0:
            print(f"  body {i}/{N}")

    audio = OUT / "audio.wav"
    make_audio(audio)
    # Pad lead silence so music still syncs to the body after the cover hold
    if COVER_HOLD_N > 0:
        with wave.open(str(audio), "rb") as r:
            sr = r.getframerate()
            sw = r.getsampwidth()
            ch = r.getnchannels()
            body = r.readframes(r.getnframes())
        lead = b"\x00" * (int(COVER_HOLD_SEC * sr) * sw * ch)
        with wave.open(str(audio), "wb") as w:
            w.setnchannels(ch)
            w.setsampwidth(sw)
            w.setframerate(sr)
            w.writeframes(lead + body)

    mp4 = OUT / "MinoxShop_ABC_curiosity_15s.mp4"
    yt_mp4 = OUT / "MinoxShop_ABC_curiosity_YT.mp4"
    subprocess.check_call(
        [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", str(frames / "f_%05d.png"),
            "-i", str(audio),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k",
            "-shortest", "-movflags", "+faststart",
            str(mp4),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    shutil.copy2(mp4, yt_mp4)

    ART.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mp4, ART / "DOWNLOAD_MinoxShop_ABC_curiosity_15s.mp4")
    shutil.copy2(yt_mp4, ART / "DOWNLOAD_MinoxShop_ABC_curiosity_YT.mp4")
    shutil.copy2(cover_path, ART / "DOWNLOAD_MinoxShop_ABC_curiosity_COVER.jpg")
    shutil.copy2(mp4, ART / "abc_foam_curiosity_demo.mp4")
    shutil.copy2(cover_path, ART / "abc_foam_curiosity_cover.jpg")
    for label, sec in (("hook", 0.4), ("bf", 3.0), ("clarity", 4.8), ("tease", 6.5), ("price", 7.8), ("cta", 14.2)):
        frame_at(int(sec * FPS), box, trio, logo).save(ART / f"abc_preview_{label}.jpg", quality=92)
    print("Wrote", mp4, "+ cover hold for YT thumb")
    return mp4


if __name__ == "__main__":
    render()
