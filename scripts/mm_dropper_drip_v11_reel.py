#!/usr/bin/env python3
"""MinoxShop Member's Mark — dropper drip v11 (product beauty direction).

NEW direction (not clipper, not scalp hole):
macro on the glass dropper + animated drip → «טיפה אחת ביום»
→ hard cut → clean 6-pack · ₪375 · CTA «לינק בתגובה».
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

W, H, FPS, DUR = 1080, 1920, 30, 22.0
N = int(round(FPS * DUR))
COVER_HOLD_SEC = 0.8
COVER_HOLD_N = int(round(COVER_HOLD_SEC * FPS))

ASSETS = Path(os.environ.get("MM_ASSETS", "/tmp/mm-reel"))
OUT = Path(os.environ.get("MM_OUT", "/tmp/mm-dropper-v11"))
ART = Path("/opt/cursor/artifacts")
LOGO_PATH = Path(os.environ.get("MINOX_LOGO", "/tmp/minox-mp/main-logo.png"))
_REPO = Path(__file__).resolve().parent.parent / "reels/members-mark-liquid-v11/assets"

FONT = "/usr/share/fonts/truetype/croscore/Arimo-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/croscore/Arimo-Regular.ttf"

HOOK_END = 3.40
STOP_END = 4.70
PRODUCT_IN = 4.80
ID_END = 7.60
MONTHS_END = 9.80
PRICE_END = 12.80
SHIP_END = 16.20  # then CTA to 22s


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


def resolve_pack() -> Path:
    for p in (
        _REPO / "liquid_gall.jpg",
        ASSETS / "liquid_gall.jpg",
        Path("/tmp/minox-second-images/members-mark-liquid-man__SECOND.jpg"),
    ):
        if p.exists():
            return p
    raise FileNotFoundError("liquid pack image missing")


def cover_window(im: Image.Image, *, zoom: float, focus_x: float, focus_y: float) -> Image.Image:
    zoom = max(1.0, zoom)
    scale = max(W / im.width, H / im.height) * zoom
    nw, nh = max(W + 2, int(im.width * scale)), max(H + 2, int(im.height * scale))
    r = im.resize((nw, nh), Image.Resampling.LANCZOS)
    max_x, max_y = nw - W, nh - H
    x = int(max(0, min(max_x, max_x * focus_x)))
    y = int(max(0, min(max_y, max_y * focus_y)))
    return r.crop((x, y, x + W, y + H))


def fit_pack(
    im: Image.Image,
    *,
    zoom: float = 1.0,
    margin_x: float = 0.05,
    margin_y: float = 0.20,
    bg=(236, 238, 242),
) -> Image.Image:
    zoom = max(0.85, zoom)
    usable_w = int(W * (1 - 2 * margin_x) / zoom)
    usable_h = int(H * (1 - 2 * margin_y) / zoom)
    scale = min(usable_w / im.width, usable_h / im.height)
    nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    r = im.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (W, H), bg)
    canvas.paste(r, ((W - nw) // 2, (H - nh) // 2))
    return canvas


def grade(im: Image.Image, *, contrast=1.0, bright=1.0, color=1.0) -> Image.Image:
    im = ImageEnhance.Brightness(im).enhance(bright)
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Color(im).enhance(color)
    return im


def phone_photo(im: Image.Image, *, seed: int, strength: float = 1.0) -> Image.Image:
    rng = np.random.default_rng(seed % 10_000)
    arr = np.asarray(im).astype(np.float32)
    noise = rng.standard_normal(arr.shape).astype(np.float32) * (4.2 * strength)
    arr = np.clip(arr + noise, 0, 255)
    out = Image.fromarray(arr.astype(np.uint8))
    vig = Image.new("RGB", (W, H), (0, 0, 0))
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((-W * 0.15, -H * 0.05, W * 1.15, H * 1.05), fill=int(210 - 40 * strength))
    mask = mask.filter(ImageFilter.GaussianBlur(90))
    out = Image.composite(out, Image.blend(out, vig, 0.22 * strength), mask)
    return out


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
        pad_x, pad_y = 44, 22
        bw, bh = int(ww + pad_x), int(hh + pad_y)
        bx = (W - bw) // 2
        if style == "hook":
            fill = (255, 214, 40, int(245 * opacity))
            text_c = (12, 12, 12, int(255 * opacity))
            radius = 14
        elif style == "stamp":
            fill = (8, 10, 14, int(240 * opacity))
            text_c = (255, 255, 255, int(255 * opacity))
            radius = 18
        else:
            fill = (10, 12, 18, int(230 * opacity))
            text_c = (255, 255, 255, int(255 * opacity))
            radius = 16
        d.rounded_rectangle((bx, cy, bx + bw, cy + bh), radius=radius, fill=fill)
        draw_text(d, (W // 2, cy + bh // 2), line, size=int(size * scale), fill=text_c)
        cy += bh + 14
    canvas.alpha_composite(layer)


def prepare_logo(path: Path, width: int = 180) -> Image.Image:
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
    layer.alpha_composite(lg, ((W - lg.width) // 2, H - lg.height - 90))
    canvas.alpha_composite(layer)


def apply_shake(im: Image.Image, shake: float, t: float) -> Image.Image:
    if shake <= 0.01:
        return im
    dx = int(shake * 3 * math.sin(t * 37))
    dy = int(shake * 2 * math.cos(t * 29))
    out = Image.new("RGB", (W, H), (0, 0, 0))
    out.paste(im, (dx, dy))
    return out


def flash_white(im: Image.Image, amount: float) -> Image.Image:
    if amount <= 0:
        return im
    white = Image.new("RGB", (W, H), (255, 255, 255))
    return Image.blend(im, white, min(1.0, amount))


def draw_drip(canvas: Image.Image, t: float):
    """Animated liquid drop falling from tip of glass pipette (lower third)."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # tip sits roughly mid-lower when zoomed on dropper
    tip_x, tip_y = int(W * 0.52), int(H * 0.58)
    # cycle a drop every ~0.85s
    cycle = (t % 0.85) / 0.85
    fall = ease_in_out(cycle)
    dy = int(120 * fall)
    r = int(10 + 6 * (1.0 - abs(cycle - 0.55)))
    # elongated drip
    col = (70, 95, 140, int(220 * (1.0 - 0.35 * cycle)))
    d.ellipse((tip_x - r, tip_y + dy - r, tip_x + r, tip_y + dy + int(r * 1.4)), fill=col)
    # highlight
    d.ellipse(
        (tip_x - r // 2, tip_y + dy - r // 2, tip_x, tip_y + dy),
        fill=(210, 220, 235, int(160 * (1.0 - cycle))),
    )
    # soft splash near end of cycle
    if cycle > 0.82:
        sp = (cycle - 0.82) / 0.18
        sr = int(18 + 40 * sp)
        d.ellipse(
            (tip_x - sr, tip_y + 130 - sr // 3, tip_x + sr, tip_y + 130 + sr // 3),
            fill=(90, 110, 150, int(90 * (1.0 - sp))),
        )
    canvas.alpha_composite(layer)


def chip_at(t: float):
    def pop_since(start: float, win: float = 0.28) -> float:
        return ease_out(min(1.0, max(0.0, (t - start) / win)))

    if 0.05 <= t < HOOK_END:
        return ["טיפה אחת ביום"], 1.0, "hook", 62, pop_since(0.05)
    if HOOK_END + 0.04 <= t < STOP_END:
        return ["זה כל מה שצריך."], 1.0, "stamp", 64, pop_since(HOOK_END + 0.04, 0.22)
    if PRODUCT_IN <= t < ID_END:
        return ["מינוקסידיל 5%", "טיפות · Member's Mark"], 1.0, "dark", 50, pop_since(PRODUCT_IN)
    if ID_END <= t < MONTHS_END:
        return ["6 בקבוקים", "6 חודשים מלאים"], 1.0, "stamp", 56, pop_since(ID_END)
    if MONTHS_END <= t < PRICE_END:
        return ["BLACK FRIDAY", "₪375", "מחיר שובר שוק"], 1.0, "bf", 52, pop_since(MONTHS_END, 0.35)
    if PRICE_END <= t < SHIP_END:
        return ["משלוח חינם", "עד הבית עם שליח"], 1.0, "dark", 46, pop_since(PRICE_END, 0.40)
    if SHIP_END <= t < DUR - 0.08:
        return ["לינק בתגובה", "הזמנה · ₪375"], 1.0, "stamp", 52, pop_since(SHIP_END)
    return None


def beat_camera(t: float):
    if t < HOOK_END:
        # Macro push into the glass dropper lying in front of the bottles
        z = 2.35 + 0.55 * ease_out(t / HOOK_END) + 0.012 * math.sin(t * 4)
        return z, 0.50, 0.78 + 0.04 * ease_out(t / HOOK_END), 0.0, 0.08
    if t < STOP_END:
        return 1.0, 0.5, 0.5, 0.0, 0.0
    u = t - PRODUCT_IN
    z = 1.02 + 0.05 * min(1.0, u / 8.0) + 0.01 * math.sin(u * 1.3)
    flash = 0.20 if MONTHS_END <= t < MONTHS_END + 0.28 else 0.0
    return z, 0.5, 0.48, flash, 0.03


def draw_bf_stack(canvas: Image.Image, y: int, lines: list[str], *, opacity: float, pop: float):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    scale = 0.86 + 0.14 * pop
    cy = y
    bf = lines[0]
    fbf = font(44)
    bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), bf, font=fbf)
    ww, hh = bb[2] - bb[0], bb[3] - bb[1]
    bw, bh = int((ww + 52) * scale), int((hh + 26) * scale)
    bx = (W - bw) // 2
    d.rounded_rectangle((bx, cy, bx + bw, cy + bh), radius=12, fill=(196, 22, 32, int(245 * opacity)))
    draw_text(d, (W // 2, cy + bh // 2), bf, size=int(44 * scale), fill=(255, 255, 255, int(255 * opacity)))
    cy += bh + 18
    price = lines[1]
    fp = font(int(130 * scale))
    bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), price, font=fp)
    ww, hh = bb[2] - bb[0], bb[3] - bb[1]
    pw, ph = ww + 72, hh + 44
    px = (W - pw) // 2
    d.rounded_rectangle((px, cy, px + pw, cy + ph), radius=28, fill=(0, 0, 0, int(245 * opacity)))
    draw_text(d, (W // 2, cy + ph // 2), price, size=int(130 * scale), fill=(255, 255, 255, int(255 * opacity)))
    cy += ph + 18
    sub = lines[2]
    fsub = font(46)
    bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), sub, font=fsub)
    ww, hh = bb[2] - bb[0], bb[3] - bb[1]
    sw, sh = ww + 48, hh + 28
    sx = (W - sw) // 2
    d.rounded_rectangle((sx, cy, sx + sw, cy + sh), radius=16, fill=(255, 205, 55, int(240 * opacity)))
    draw_text(d, (W // 2, cy + sh // 2), sub, size=46, fill=(20, 18, 12, int(255 * opacity)))
    canvas.alpha_composite(layer)


def frame_at(i: int, pack: Image.Image, logo: Image.Image) -> Image.Image:
    t = i / FPS
    zoom, fx, fy, flash, shake = beat_camera(t)

    if t < HOOK_END:
        plate = cover_window(pack, zoom=zoom, focus_x=fx, focus_y=fy)
        plate = grade(plate, contrast=1.14, bright=1.02, color=1.05)
        plate = phone_photo(plate, seed=i, strength=0.55)
        canvas = plate.convert("RGBA")
        draw_drip(canvas, t)
    elif t < STOP_END:
        canvas = Image.new("RGBA", (W, H), (6, 8, 12, 255))
    else:
        pack_zoom = 1.0 + 0.03 * min(1.0, max(0.0, (t - PRODUCT_IN) / 7.0))
        plate = fit_pack(pack, zoom=pack_zoom, margin_x=0.04, margin_y=0.24)
        plate = grade(plate, contrast=1.12, bright=0.98, color=1.04)
        canvas = plate.convert("RGBA")
        vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        vd = ImageDraw.Draw(vig)
        for k, a in ((0, 0), (1, 14), (2, 28)):
            m = 40 + k * 70
            vd.rectangle((0, 0, W, m), fill=(8, 14, 28, a))
            vd.rectangle((0, H - m, W, H), fill=(8, 14, 28, a))
        canvas = Image.alpha_composite(canvas, vig)

    canvas_rgb = apply_shake(canvas.convert("RGB"), shake, t)
    canvas_rgb = flash_white(canvas_rgb, flash)
    canvas = canvas_rgb.convert("RGBA")

    info = chip_at(t)
    if info:
        lines, op, style, size, pop = info
        if style == "stamp" and lines and lines[0].startswith("זה"):
            y = int(H * 0.42)
            chip_block(canvas, y, lines, size=size, opacity=op, style=style, pop=pop)
        elif style == "bf":
            draw_bf_stack(canvas, int(H * 0.05), lines, opacity=op, pop=pop)
        else:
            y = int(H * 0.07)
            chip_block(canvas, y, lines, size=size, opacity=op, style=style, pop=pop)

    if t >= SHIP_END:
        paste_logo(canvas, logo, opacity=min(1.0, (t - SHIP_END) / 0.35))

    return canvas.convert("RGB")


def make_audio(path: Path):
    sr = 44100
    n = int(DUR * sr)
    t = np.arange(n) / sr
    rng = np.random.default_rng(31)
    beat = 60 / 124

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

    # Soft drip blips during hook (not clipper buzz)
    drips = np.zeros(n)
    hook_n = int(HOOK_END * sr)
    for k, start in enumerate(np.arange(0.15, HOOK_END, 0.85)):
        i0 = int(start * sr)
        length = min(int(0.18 * sr), n - i0)
        if length <= 0:
            break
        tt = np.arange(length) / sr
        freq = 880 * np.exp(-10 * tt) + 220
        drips[i0 : i0 + length] += 0.42 * np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-14 * tt)
        # tiny splash noise
        sl = min(int(0.05 * sr), length)
        drips[i0 : i0 + sl] += 0.12 * rng.standard_normal(sl) * np.exp(-50 * np.arange(sl) / sr)
    # airy bed under drips
    air = 0.04 * np.sin(2 * np.pi * 110 * t) * (t < HOOK_END)

    mute = np.ones(n)
    stop_a, stop_b = int(HOOK_END * sr), int(STOP_END * sr)
    mute[stop_a:stop_b] = 0.05

    kick = np.zeros(n)
    snare = np.zeros(n)
    for i, bt in enumerate(np.arange(STOP_END, DUR, beat)):
        i0 = int(bt * sr)
        length = int(0.22 * sr)
        if i0 + length > n:
            break
        tt = np.arange(length) / sr
        freq = 105 * np.exp(-16 * tt) + 42
        amp = 0.58 if i % 2 == 0 else 0.34
        kick[i0 : i0 + length] += amp * np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-9 * tt)
        if i % 2 == 1:
            sl = int(0.09 * sr)
            if i0 + sl <= n:
                snare[i0 : i0 + sl] += 0.28 * rng.standard_normal(sl) * np.exp(-38 * np.arange(sl) / sr)

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
        wave_b = 0.62 * np.sin(2 * np.pi * note * tt) + 0.28 * np.sin(2 * np.pi * note * 2 * tt)
        bass[i0 : i0 + length] += 0.26 * wave_b * adsr(length)

    impact = np.zeros(n)
    for wt, amp in (
        (HOOK_END, 0.90),
        (PRODUCT_IN, 0.65),
        (MONTHS_END, 1.10),
        (SHIP_END, 0.45),
    ):
        i0 = int(wt * sr)
        length = min(int(0.34 * sr), n - i0)
        if length <= 0:
            continue
        tt = np.arange(length) / sr
        impact[i0 : i0 + length] += amp * np.sin(2 * np.pi * (58 * np.exp(-15 * tt)) * tt) * np.exp(-9 * tt)

    riser = np.zeros(n)
    r0 = int((MONTHS_END - 0.45) * sr)
    rl = int(0.45 * sr)
    if r0 > 0 and r0 + rl < n:
        tt = np.arange(rl) / sr
        riser[r0 : r0 + rl] = 0.24 * np.sin(2 * np.pi * (220 + 820 * (tt / 0.45)) * tt) * (tt / 0.45)

    pad = np.zeros(n)
    for f in (146.83, 174.61, 220.0):
        pad += np.sin(2 * np.pi * f * t)
    pad = pad / 4.5 * 0.07
    pad[: int(STOP_END * sr)] *= 0.1

    bed = (drips + air + kick + snare + bass + pad + impact + riser) * mute
    gate = np.ones(n)
    gate[int(PRODUCT_IN * sr) :] = 1.18
    gate[int(MONTHS_END * sr) :] = 1.32
    bed = bed * gate
    peak = np.max(np.abs(bed)) + 1e-9
    bed = np.tanh(bed / peak * 1.18) * 0.98
    fi, fo = int(0.03 * sr), int(0.25 * sr)
    bed[:fi] *= np.linspace(0, 1, fi)
    bed[-fo:] *= np.linspace(1, 0, fo)
    audio = np.clip(bed, -1, 1)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(x * 32750)) for x in audio))


def build_hook_cover(pack: Image.Image) -> Image.Image:
    plate = cover_window(pack, zoom=2.55, focus_x=0.50, focus_y=0.80)
    plate = grade(plate, contrast=1.16, bright=1.02, color=1.06)
    plate = phone_photo(plate, seed=9, strength=0.6)
    canvas = plate.convert("RGBA")
    draw_drip(canvas, 0.45)
    chip_block(canvas, int(H * 0.07), ["טיפה אחת ביום"], size=64, opacity=1.0, style="hook", pop=1.0)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = int(H * 0.78)
    price = "₪375"
    bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), price, font=font(108))
    ww, hh = bb[2] - bb[0], bb[3] - bb[1]
    pw, ph = ww + 56, hh + 28
    px = (W - pw) // 2
    d.rounded_rectangle((px, y, px + pw, y + ph), radius=22, fill=(0, 0, 0, 235))
    for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        draw_text(d, (W // 2 + ox, y + ph // 2 + oy), price, size=108, fill=(255, 205, 55, 255))
    draw_text(d, (W // 2, y + ph // 2), price, size=108, fill=(255, 255, 255, 255))
    y += ph + 14
    draw_text(d, (W // 2, y), "שישה בקבוקים · משלוח חינם", size=34, fill=(255, 220, 80, 255))
    return Image.alpha_composite(canvas, layer).convert("RGB")


def loudness_boost(src: Path, dst: Path):
    af = (
        "acompressor=threshold=-17dB:ratio=4.5:attack=5:release=55:makeup=8.5,"
        "alimiter=limit=0.90:attack=1:release=40:level=disabled,"
        "loudnorm=I=-9:TP=-1.2:LRA=7"
    )
    subprocess.check_call(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-af", af,
            "-ar", "44100", "-ac", "1", "-c:a", "pcm_s16le",
            str(dst),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def encode_mp4(frames_dir: Path, audio: Path, mp4: Path, start_idx: int = 0):
    pattern = frames_dir / "f_%05d.png"
    subprocess.check_call(
        [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-start_number", str(start_idx),
            "-i", str(pattern),
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

    pack = load_rgb(resolve_pack())
    logo = prepare_logo(LOGO_PATH if LOGO_PATH.exists() else _REPO / "main-logo.png", width=180)

    def pad_pack(im: Image.Image, top=0.08, side=0.06, bottom=0.08) -> Image.Image:
        pad_t = int(im.height * top)
        pad_s = int(im.width * side)
        pad_b = int(im.height * bottom)
        out = Image.new("RGB", (im.width + 2 * pad_s, im.height + pad_t + pad_b), (236, 238, 242))
        out.paste(im, (pad_s, pad_t))
        return out

    pack_p = pad_pack(pack)

    cover = build_hook_cover(pack)
    cover_path = OUT / "MinoxShop_MM_dropper_v11_COVER.jpg"
    cover.save(cover_path, quality=95)

    print(f"Rendering {N} frames (v11 dropper drip — טיפה אחת ביום)…")
    for i in range(N):
        im = frame_at(i, pack_p, logo)
        im.save(frames / f"f_{i:05d}.png")
        if i % 60 == 0:
            print(f"  body {i}/{N}")

    audio_raw = OUT / "audio_raw.wav"
    audio = OUT / "audio.wav"
    make_audio(audio_raw)
    loudness_boost(audio_raw, audio)

    mp4 = OUT / "MinoxShop_MM_dropper_v11_22s.mp4"
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
    yt_mp4 = OUT / "MinoxShop_MM_dropper_v11_YT.mp4"
    encode_mp4(yt_frames, yt_audio, yt_mp4)

    ART.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mp4, ART / "DOWNLOAD_MinoxShop_MM_dropper_v11_22s.mp4")
    shutil.copy2(yt_mp4, ART / "DOWNLOAD_MinoxShop_MM_dropper_v11_YT.mp4")
    shutil.copy2(cover_path, ART / "DOWNLOAD_MinoxShop_MM_dropper_v11_COVER.jpg")
    shutil.copy2(mp4, ART / "mm_dropper_v11_demo.mp4")
    for label, sec in (
        ("hook", 0.5),
        ("drip", 2.0),
        ("stop", 4.0),
        ("product", 5.5),
        ("six", 8.5),
        ("price", 11.0),
        ("ship", 14.5),
        ("cta", 18.5),
    ):
        frame_at(int(sec * FPS), pack_p, logo).save(ART / f"mm_v11_preview_{label}.jpg", quality=92)
    cover.save(ART / "mm_v11_preview_cover.jpg", quality=92)
    print("Wrote", mp4)
    print("Wrote", yt_mp4)
    return mp4


if __name__ == "__main__":
    render()
