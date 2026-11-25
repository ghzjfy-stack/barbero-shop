#!/usr/bin/env python3
"""MinoxShop Member's Mark — shave fake-out reel.

Hook (MinoxShop version of viral barber fake-cut):
red “shave line” on thinning crown → STOP → Member's Mark 5% drops reveal.

Hero SKU: members-mark-liquid-man · 6 months · 375₪
Also nods that foam exists.

15s + 0.8s cover hold for YT Shorts thumb.
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
COVER_HOLD_SEC = 0.8
COVER_HOLD_N = int(round(COVER_HOLD_SEC * FPS))

ASSETS = Path(os.environ.get("MM_ASSETS", "/tmp/mm-reel"))
OUT = Path(os.environ.get("MM_OUT", "/tmp/mm-shave-fakeout"))
ART = Path("/opt/cursor/artifacts")
LOGO_PATH = Path(os.environ.get("MINOX_LOGO", "/tmp/minox-mp/main-logo.png"))

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


def grade(im: Image.Image, *, contrast: float = 1.1, bright: float = 0.94) -> Image.Image:
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Color(im).enhance(1.05)
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


def chip_block(canvas: Image.Image, y: int, lines: list[str], *, size: int, opacity: float, style: str = "dark", pop: float = 1.0):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(size)
    widths, heights = [], []
    for line in lines:
        bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), line, font=f)
        widths.append(bb[2] - bb[0])
        heights.append(bb[3] - bb[1])
    pad_x, pad_y, gap = 36, 22, 10
    box_w = max(widths) + pad_x * 2
    box_h = sum(heights) + gap * (len(lines) - 1) + pad_y * 2
    box_w = int(box_w * (0.92 + 0.08 * pop))
    x0 = (W - box_w) // 2
    y0 = y
    if style == "stamp":
        fill = (8, 12, 20, int(230 * opacity))
        radius = 18
    elif style == "alert":
        fill = (196, 22, 32, int(235 * opacity))
        radius = 16
    else:
        fill = (0, 0, 0, int(200 * opacity))
        radius = 22
    d.rounded_rectangle((x0, y0, x0 + box_w, y0 + box_h), radius=radius, fill=fill)
    cy = y0 + pad_y
    for i, line in enumerate(lines):
        draw_text(d, (W // 2, cy + heights[i] // 2), line, size=size, fill=(255, 255, 255, int(255 * opacity)))
        cy += heights[i] + gap
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
    dx = int(amount * 10 * math.sin(t * 55))
    dy = int(amount * 8 * math.cos(t * 47))
    base = Image.new("RGB", (W, H), (20, 22, 28))
    base.paste(im, (dx, dy))
    return base


def red_shave_line(canvas: Image.Image, t: float):
    """Viral fake-cut cue: bright red strip down thinning crown."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # line grows in
    progress = ease_out(min(1.0, t / 1.1))
    x = int(W * 0.50 + 6 * math.sin(t * 18))
    y0 = int(H * 0.22)
    y1 = int(H * (0.22 + 0.38 * progress))
    for w, a in ((28, 50), (14, 120), (6, 230)):
        d.line((x, y0, x, y1), fill=(220, 30, 40, a), width=w)
    # tip glow
    if progress > 0.2:
        r = 18
        d.ellipse((x - r, y1 - r, x + r, y1 + r), fill=(255, 80, 80, 160))
    canvas.alpha_composite(layer)


def flash_white(im: Image.Image, amount: float) -> Image.Image:
    if amount <= 0:
        return im
    white = Image.new("RGB", (W, H), (255, 255, 255))
    return Image.blend(im, white, min(1.0, amount))


def chip_at(t: float):
    # returns lines, opacity, style, size
    if 0.15 <= t < 2.35:
        return ["לגלח את זה", "ולגמור עם זה?"], 1.0, "alert", 56
    if 2.45 <= t < 3.35:
        return ["רגע."], 1.0, "stamp", 72
    if 3.5 <= t < 5.6:
        return ["מינוקסידיל 5%", "טיפות · Member's Mark"], 1.0, "dark", 48
    if 5.7 <= t < 7.5:
        return ["6 חודשים"], 1.0, "stamp", 64
    if 7.55 <= t < 9.0:
        return ["375₪"], 1.0, "stamp", 110
    if 9.1 <= t < 10.7:
        return ["מחיר שובר שוק", "יש גם קצף במלאי"], 1.0, "dark", 44
    if 10.8 <= t < 12.5:
        return ["משלוח חינם", "עד הבית עם שליח"], 1.0, "dark", 46
    if 12.6 <= t < 14.9:
        return ["הקישור בפרופיל"], 1.0, "stamp", 52
    return None


def beat_camera(t: float):
    # phase: scalp scare → product
    if t < 2.4:
        return 1.18 + 0.04 * math.sin(t * 9), 0.48, 0.32, 0.0, 0.55 + 0.25 * math.sin(t * 22)
    if t < 3.4:
        # hard stop card — keep dark (no white flash washout)
        return 1.0, 0.5, 0.45, 0.0, 0.0
    if t < 7.4:
        z = 1.0 + 0.03 * math.sin((t - 3.4) * 2.2)
        return z, 0.5, 0.48, 0.0, 0.08
    if t < 9.1:
        return 1.08, 0.5, 0.5, 0.35 if t < 7.7 else 0.0, 0.2
    return 1.0 + 0.02 * (t - 9.1) * 0.1, 0.5, 0.5, 0.0, 0.05


def frame_at(i: int, scalp: Image.Image, bottles: Image.Image, foam: Image.Image, logo: Image.Image) -> Image.Image:
    t = i / FPS
    zoom, fx, fy, flash, shake = beat_camera(t)
    if t < 2.45:
        plate = cover_window(scalp, zoom=zoom, focus_x=fx, focus_y=fy)
        plate = grade(plate, contrast=1.15, bright=0.9)
        canvas = plate.convert("RGBA")
        red_shave_line(canvas, t)
    elif t < 3.45:
        # hard cut black / stop
        canvas = Image.new("RGBA", (W, H), (8, 10, 16, 255))
    else:
        # product world — bottles hero; foam peeks late as alternate
        src = bottles
        if 9.3 <= t < 10.5:
            # quick foam nod
            src = foam
        plate = cover_window(src, zoom=zoom, focus_x=fx, focus_y=fy)
        plate = grade(plate)
        canvas = plate.convert("RGBA")
        if t >= 14.2:
            # soft end hold
            pass

    canvas_rgb = apply_shake(canvas.convert("RGB"), shake, t)
    canvas_rgb = flash_white(canvas_rgb, flash)
    canvas = canvas_rgb.convert("RGBA")

    info = chip_at(t)
    if info:
        lines, op, style, size = info
        y = int(H * (0.12 if t < 2.45 else 0.14 if style != "stamp" else 0.16))
        if lines == ["375₪"]:
            y = int(H * 0.38)
            size = 120
        chip_block(canvas, y, lines, size=size, opacity=op, style=style, pop=1.0)

    if t >= 3.6:
        paste_logo(canvas, logo, opacity=min(1.0, (t - 3.6) / 0.4))

    return canvas.convert("RGB")


def make_audio(path: Path):
    sr = 44100
    n = int(DUR * sr)
    t = np.arange(n) / sr
    rng = np.random.default_rng(11)
    beat = 60 / 126

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

    impact = np.zeros(n)
    for wt, amp in ((0.08, 0.2), (2.45, 0.55), (3.5, 0.4), (7.55, 0.5), (12.6, 0.25)):
        i0 = int(wt * sr)
        length = min(int(0.28 * sr), n - i0)
        if length <= 0:
            continue
        tt = np.arange(length) / sr
        impact[i0 : i0 + length] += amp * np.sin(2 * np.pi * (50 * np.exp(-18 * tt)) * tt) * np.exp(-11 * tt)
        noise = np.convolve(rng.standard_normal(length), np.ones(60) / 60, mode="same")
        impact[i0 : i0 + length] += 0.08 * amp * noise * np.sin(np.linspace(0, np.pi, length))

    pad = np.zeros(n)
    for f in (146.83, 174.61, 220.0):
        pad += np.sin(2 * np.pi * f * t)
    pad = pad / 4.5 * 0.05
    pad = np.convolve(pad, np.ones(41) / 41, mode="same")

    bed = kick + snare + bass + pad + impact
    peak = np.max(np.abs(bed)) + 1e-9
    bed = np.tanh(bed / peak * 0.75) * 0.92
    fi, fo = int(0.06 * sr), int(0.4 * sr)
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

    # product plate
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


def render() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    frames = OUT / "frames"
    if frames.exists():
        shutil.rmtree(frames)
    frames.mkdir()

    scalp = load_rgb(ASSETS / "scalp.jpg")
    bottles = load_rgb(ASSETS / "liquid_gall.jpg")
    foam = load_rgb(ASSETS / "foam_gall.jpg")
    logo = prepare_logo(LOGO_PATH, width=200)

    # pad product plates so caps/edges never clip
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
    cover_path = OUT / "MinoxShop_MM_fakeout_COVER.jpg"
    cover.save(cover_path, quality=95)

    total = COVER_HOLD_N + N
    print(f"Rendering {total} frames (cover hold + shave fake-out)…")
    for i in range(COVER_HOLD_N):
        cover.save(frames / f"f_{i:05d}.png")
    for i in range(N):
        im = frame_at(i, scalp, bottles_p, foam_p, logo)
        im.save(frames / f"f_{COVER_HOLD_N + i:05d}.png")
        if i % 60 == 0:
            print(f"  body {i}/{N}")

    audio = OUT / "audio.wav"
    make_audio(audio)
    if COVER_HOLD_N > 0:
        with wave.open(str(audio), "rb") as r:
            sr, sw, ch = r.getframerate(), r.getsampwidth(), r.getnchannels()
            body = r.readframes(r.getnframes())
        lead = b"\x00" * (int(COVER_HOLD_SEC * sr) * sw * ch)
        with wave.open(str(audio), "wb") as w:
            w.setnchannels(ch)
            w.setsampwidth(sw)
            w.setframerate(sr)
            w.writeframes(lead + body)

    mp4 = OUT / "MinoxShop_MM_fakeout_15s.mp4"
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

    ART.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mp4, ART / "DOWNLOAD_MinoxShop_MM_fakeout_15s.mp4")
    shutil.copy2(cover_path, ART / "DOWNLOAD_MinoxShop_MM_fakeout_COVER.jpg")
    shutil.copy2(mp4, ART / "mm_fakeout_demo.mp4")
    for label, sec in (("hook", 0.8), ("stop", 2.8), ("product", 4.5), ("price", 8.0), ("cta", 13.2)):
        frame_at(int(sec * FPS), scalp, bottles_p, foam_p, logo).save(ART / f"mm_preview_{label}.jpg", quality=92)
    print("Wrote", mp4)
    return mp4


if __name__ == "__main__":
    render()
