#!/usr/bin/env python3
"""MinoxShop Amazon Basic Care — curiosity reel v7 FULL-BLEED.

New direction (user feedback: cutouts looked bad, static, weird music):
- Product photo fills the entire 1080×1920 frame (cover crop) — no stickers, no keying.
- Varied Ken Burns windows + hard cuts so it doesn't feel like one looping still.
- Warm soft beat (BF-style), not a hollow pad.

15s · cans only (boost-safer) · Hebrew chips · CTA הקישור בפרופיל
Hook: מה יש בקופסה הכחולה מארה״ב?
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


def chip_block(canvas, cy, lines, *, size=48, opacity=1.0, slide_x=0.0, pop=1.0):
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
    pad_x, pad_y, gap = 46, 20, 8
    pw = max(widths) + pad_x * 2
    ph = sum(heights) + gap * (len(lines) - 1) + pad_y * 2
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0 = (W - pw) // 2 + int(slide_x)
    y0 = cy - ph // 2
    d.rounded_rectangle((x0 + 3, y0 + 4, x0 + pw + 3, y0 + ph + 4), radius=24, fill=(0, 0, 0, int(100 * opacity)))
    d.rounded_rectangle((x0, y0, x0 + pw, y0 + ph), radius=24, fill=(255, 255, 255, int(240 * opacity)))
    y = y0 + pad_y
    for line, th in zip(lines, heights):
        draw_text(d, (x0 + pw // 2, y + th // 2), line, size=size, fill=(*INK, int(255 * opacity)))
        y += th + gap
    canvas.alpha_composite(layer)


def chip_at(t: float):
    if 0.28 <= t < 3.8:
        local = t - 0.28
        if local < 0.28:
            return (["מה יש בקופסה הכחולה", "מארה״ב?"], ease_out(local / 0.28), 44 * (1 - ease_out(local / 0.28)), 0.94 + 0.1 * ease_out(local / 0.28))
        if t > 3.55:
            return (["מה יש בקופסה הכחולה", "מארה״ב?"], 1 - ease_in((t - 3.55) / 0.25), 0.0, 1.0)
        return (["מה יש בקופסה הכחולה", "מארה״ב?"], 1.0, 0.0, 1.0)
    if 3.9 <= t < 6.6:
        local = t - 3.9
        op = ease_out(min(1, local / 0.2))
        if t > 6.4:
            op = 1 - ease_in((t - 6.4) / 0.2)
        return (["קצף לגברים מארה״ב"], op, 0.0, 1.0 + 0.08 * (1 - ease_out(min(1, local / 0.3))))
    if 6.7 <= t < 8.8:
        local = t - 6.7
        op = ease_out(min(1, local / 0.18))
        if t > 8.6:
            op = 1 - ease_in((t - 8.6) / 0.2)
        return (["3 חודשים"], op, 0.0, 1.08 if local < 0.25 else 1.0)
    if 8.9 <= t < 10.7:
        local = t - 8.9
        op = ease_out(min(1, local / 0.18))
        if t > 10.5:
            op = 1 - ease_in((t - 10.5) / 0.2)
        return (["395₪"], op, 0.0, 1.12 if local < 0.25 else 1.0)
    if 10.8 <= t < 12.7:
        local = t - 10.8
        op = ease_out(min(1, local / 0.2))
        if t > 12.5:
            op = 1 - ease_in((t - 12.5) / 0.2)
        return (["יבוא מארה״ב · משלוח חינם"], op, 0.0, 1.0)
    if 12.85 <= t <= 15.01:
        local = t - 12.85
        return (["הקישור בפרופיל"], ease_out(min(1, local / 0.25)), 0.0, 1.06 if local < 0.3 else 1.0)
    return None


def beat_camera(t: float) -> tuple[float, float, float, float]:
    """Return zoom, focus_x, focus_y, flash.

    focus_y≈0 keeps the TOP of the packshot (clear caps) in frame.
    """
    # 0–3.8: full trio, caps visible, gentle push
    if t < 3.8:
        local = t / 3.8
        return 1.02 + 0.06 * ease_out(local), 0.50, 0.08 + 0.06 * local, 0.0
    # 3.8–5.2: left can — still show cap
    if t < 5.2:
        local = (t - 3.8) / 1.4
        flash = 0.5 * (1 - local / 0.12) if local < 0.12 else 0.0
        return 1.28 + 0.06 * ease_out(local), 0.16, 0.10 + 0.05 * local, max(0, flash)
    # 5.2–6.7: right can — cap visible
    if t < 6.7:
        local = (t - 5.2) / 1.5
        flash = 0.4 * (1 - local / 0.1) if local < 0.1 else 0.0
        return 1.26 + 0.05 * ease_out(local), 0.84, 0.12, max(0, flash)
    # 6.7–8.9: pull back trio for "3 months"
    if t < 8.9:
        local = (t - 6.7) / 2.2
        flash = 0.3 * (1 - local / 0.1) if local < 0.1 else 0.0
        return 1.04 + 0.05 * ease_out(local), 0.50, 0.12 + 0.05 * local, max(0, flash)
    # 8.9–10.8: slight push for price (keep caps)
    if t < 10.8:
        local = (t - 8.9) / 1.9
        flash = 0.45 * (1 - local / 0.1) if local < 0.1 else 0.0
        return 1.18 + 0.05 * ease_out(local), 0.50, 0.18, max(0, flash)
    # 10.8–12.8: wide for shipping
    if t < 12.8:
        local = (t - 10.8) / 2.0
        return 1.03 + 0.04 * ease_out(local), 0.50, 0.10, 0.0
    # 12.8–15: slow push CTA
    local = (t - 12.8) / 2.2
    return 1.06 + 0.10 * ease_in(local), 0.50, 0.08 + 0.04 * local, 0.0


def frame_at(i: int, trio: Image.Image, single: Image.Image) -> Image.Image:
    t = i / FPS
    zoom, fx, fy, flash = beat_camera(t)
    # Close beats use a real single-can plate (not a zoom into the trio)
    use_single = 3.8 <= t < 6.7 or 8.9 <= t < 10.8
    src = single if use_single else trio
    if use_single:
        # Recenter camera for single-can plate
        if 3.8 <= t < 5.2:
            zoom, fx, fy = 1.08 + 0.08 * ease_out((t - 3.8) / 1.4), 0.50, 0.10
        elif t < 6.7:
            zoom, fx, fy = 1.10 + 0.06 * ease_out((t - 5.2) / 1.5), 0.50, 0.12
        else:
            zoom, fx, fy = 1.15 + 0.06 * ease_out((t - 8.9) / 1.9), 0.50, 0.35
    plate = cover_window(src, zoom=zoom, focus_x=fx, focus_y=fy)
    canvas = grade(plate)
    canvas = flash_white(canvas, flash)
    info = chip_at(t)
    if info:
        lines, op, slide, pop = info
        size = 50 if len(lines) > 1 else 54
        if lines == ["395₪"]:
            size = 72
        if lines == ["הקישור בפרופיל"]:
            size = 58
        chip_block(canvas, int(H * 0.14), lines, size=size, opacity=op, slide_x=slide, pop=pop)
    return add_grain(canvas, amount=0.01, seed=i * 23 + 2).convert("RGB")


def make_audio(path: Path) -> None:
    """Warm soft beat — closer to BF reel energy, not hollow pad."""
    sr = 44100
    n = int(DUR * sr)
    rng = np.random.default_rng(11)
    t = np.arange(n) / sr
    bpm = 96
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
    for i, bt in enumerate(np.arange(0, DUR, beat)):
        i0 = int(bt * sr)
        length = int(0.22 * sr)
        if i0 + length > n:
            break
        tt = np.arange(length) / sr
        freq = 90 * np.exp(-15 * tt) + 40
        amp = 0.24 if i % 2 == 0 else 0.14
        kick[i0 : i0 + length] += amp * np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-8 * tt)

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
        wave_b = 0.55 * np.sin(2 * np.pi * note * tt) + 0.2 * np.sin(2 * np.pi * note * 2 * tt)
        bass[i0 : i0 + length] += 0.14 * wave_b * adsr(length)

    pad = np.zeros(n)
    for f in (146.83, 174.61, 220.0):
        pad += np.sin(2 * np.pi * f * (1 + 0.002 * rng.standard_normal()) * t)
    pad = pad / 4.2 * 0.07 * (0.8 + 0.2 * np.sin(2 * np.pi * 0.12 * t))
    pad = np.convolve(pad, np.ones(41) / 41, mode="same")

    pluck = np.zeros(n)
    melody = [
        (0.5, 293.66, 0.35),
        (2.0, 349.23, 0.3),
        (3.9, 392.0, 0.35),
        (5.3, 349.23, 0.3),
        (6.8, 440.0, 0.35),
        (8.9, 392.0, 0.35),
        (10.9, 349.23, 0.4),
        (12.9, 293.66, 0.45),
    ]
    for st, freq, length_s in melody:
        i0 = int(st * sr)
        length = min(int(length_s * sr), n - i0)
        if length <= 0:
            continue
        tt = np.arange(length) / sr
        tone = np.sin(2 * np.pi * freq * tt) * np.exp(-2.8 * tt)
        tone += 0.18 * np.sin(2 * np.pi * freq * 2 * tt) * np.exp(-5 * tt)
        pluck[i0 : i0 + length] += 0.085 * tone

    whoosh = np.zeros(n)
    for wt, amp in ((3.82, 0.2), (5.22, 0.16), (6.72, 0.14), (8.92, 0.18), (12.85, 0.16)):
        i0 = int(wt * sr)
        length = min(int(0.28 * sr), n - i0)
        if length <= 0:
            continue
        noise = np.convolve(rng.standard_normal(length), np.ones(100) / 100, mode="same")
        env = np.sin(np.linspace(0, np.pi, length)) ** 1.5
        whoosh[i0 : i0 + length] += 0.04 * amp * noise * env

    bed = kick + bass + pad + pluck + whoosh
    quiet = int(0.25 * sr)
    bed[:quiet] *= np.linspace(0.2, 1, quiet)
    peak = np.max(np.abs(bed)) + 1e-9
    bed = np.tanh(bed / peak * 0.68 * 1.08) * 0.9
    bed = np.convolve(bed, np.ones(5) / 5, mode="same")
    fi, fo = int(0.12 * sr), int(0.55 * sr)
    bed[:fi] *= np.linspace(0, 1, fi)
    bed[-fo:] *= np.linspace(1, 0, fo)
    audio = np.clip(bed, -1, 1)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(x * 30000)) for x in audio))


def render() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    frames = OUT / "frames"
    if frames.exists():
        shutil.rmtree(frames)
    frames.mkdir()

    cans = load_rgb(ASSETS / "cans.png")

    def pad_pack(im: Image.Image, top: float = 0.14) -> Image.Image:
        pad_t = int(im.height * top)
        pad_s = int(im.width * 0.05)
        pad_b = int(im.height * 0.05)
        out = Image.new("RGB", (im.width + 2 * pad_s, im.height + pad_t + pad_b), (255, 255, 255))
        out.paste(im, (pad_s, pad_t))
        return out

    trio = pad_pack(cans, top=0.14)
    # Single can from left of original (full height of can + pad)
    w, h = cans.size
    single = pad_pack(cans.crop((int(w * 0.02), 0, int(w * 0.38), h)), top=0.16)

    print(f"Rendering {N} frames (v7 full-bleed)…")
    for i in range(N):
        im = frame_at(i, trio, single)
        im.save(frames / f"f_{i:05d}.png")
        if i % 60 == 0:
            print(f"  {i}/{N}")

    audio = OUT / "audio.wav"
    make_audio(audio)
    mp4 = OUT / "MinoxShop_ABC_curiosity_15s.mp4"
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

    cover = frame_at(int(1.0 * FPS), trio, single)
    cover_path = OUT / "MinoxShop_ABC_curiosity_COVER.jpg"
    cover.save(cover_path, quality=95)

    ART.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mp4, ART / "DOWNLOAD_MinoxShop_ABC_curiosity_15s.mp4")
    shutil.copy2(cover_path, ART / "DOWNLOAD_MinoxShop_ABC_curiosity_COVER.jpg")
    shutil.copy2(mp4, ART / "abc_foam_curiosity_demo.mp4")
    shutil.copy2(cover_path, ART / "abc_foam_curiosity_cover.jpg")
    for label, sec in (("hook", 1.0), ("left", 4.4), ("price", 9.4), ("cta", 13.3)):
        frame_at(int(sec * FPS), trio, single).save(ART / f"abc_preview_{label}.jpg", quality=92)

    print("Wrote", mp4)
    return mp4


if __name__ == "__main__":
    render()
