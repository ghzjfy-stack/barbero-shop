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
    # Clarity-first story: hook → BF → WHAT IT IS → price smash → proof → door → warmth → CTA
    # Hook from frame 0 — mute scroll / hook-rate (first 1–2s decide views)
    if 0.0 <= t < 2.6:
        if t < 0.18:
            return (["מה יש בקופסה הכחולה", "מארה״ב?"], ease_out(t / 0.18), 36 * (1 - ease_out(t / 0.18)), 0.96 + 0.1 * ease_out(t / 0.18))
        if t > 2.4:
            return (["מה יש בקופסה הכחולה", "מארה״ב?"], 1 - ease_in((t - 2.4) / 0.2), 0.0, 1.0)
        return (["מה יש בקופסה הכחולה", "מארה״ב?"], 1.0, 0.0, 1.0)
    if 2.7 <= t < 4.2:
        local = t - 2.7
        op = ease_out(min(1, local / 0.16))
        if t > 4.0:
            op = 1 - ease_in((t - 4.0) / 0.2)
        return (["BLACK FRIDAY"], op, 0.0, 1.14 if local < 0.26 else 1.0)
    if 4.3 <= t < 6.4:
        local = t - 4.3
        op = ease_out(min(1, local / 0.16))
        if t > 6.2:
            op = 1 - ease_in((t - 6.2) / 0.2)
        # The clarity beat — no guessing what the product does
        return (["מינוקסידיל 5%", "לחיזוק וצמיחת השיער"], op, 0.0, 1.1 if local < 0.28 else 1.0)
    if 6.5 <= t < 8.3:
        local = t - 6.5
        op = ease_out(min(1, local / 0.16))
        if t > 8.1:
            op = 1 - ease_in((t - 8.1) / 0.2)
        return (["מחיר שובר שוק", "395₪"], op, 0.0, 1.16 if local < 0.28 else 1.0)
    if 8.4 <= t < 10.0:
        local = t - 8.4
        op = ease_out(min(1, local / 0.16))
        if t > 9.8:
            op = 1 - ease_in((t - 9.8) / 0.2)
        return (["3 חודשים · קצף לגברים"], op, 0.0, 1.06 if local < 0.25 else 1.0)
    if 10.1 <= t < 11.8:
        local = t - 10.1
        op = ease_out(min(1, local / 0.16))
        if t > 11.6:
            op = 1 - ease_in((t - 11.6) / 0.2)
        return (["משלוח חינם עד הבית", "עם שליח"], op, 0.0, 1.04 if local < 0.25 else 1.0)
    if 11.9 <= t < 13.1:
        local = t - 11.9
        op = ease_out(min(1, local / 0.18))
        if t > 12.9:
            op = 1 - ease_in((t - 12.9) / 0.2)
        return (["אנחנו פה בשבילכם"], op, 0.0, 1.08 if local < 0.28 else 1.0)
    if 13.2 <= t <= 15.01:
        local = t - 13.2
        return (["הקישור בפרופיל"], ease_out(min(1, local / 0.22)), 0.0, 1.08 if local < 0.28 else 1.0)
    return None


def beat_camera(t: float) -> tuple[float, float, float, float]:
    """zoom≤1.0; box → cans; flash on reveal + clarity beat."""
    if t < 2.7:
        local = t / 2.7
        # tiny open flash = motion in first frames (hook rate)
        flash = 0.22 * (1 - t / 0.2) if t < 0.2 else 0.0
        return 1.0, 0.44 + 0.10 * ease_out(local), 0.5, max(0, flash)
    if t < 4.3:
        local = (t - 2.7) / 1.6
        flash = 0.6 * (1 - local / 0.12) if local < 0.12 else 0.0
        return 1.0, 0.52 - 0.04 * ease_out(local), 0.5, max(0, flash)
    if t < 6.5:
        local = (t - 4.3) / 2.2
        flash = 0.35 * (1 - local / 0.1) if local < 0.1 else 0.0
        return 1.0, 0.50, 0.5, max(0, flash)
    if t < 8.4:
        local = (t - 6.5) / 1.9
        flash = 0.45 * (1 - local / 0.1) if local < 0.1 else 0.0
        return 1.0, 0.50, 0.5, max(0, flash)
    if t < 10.1:
        local = (t - 8.4) / 1.7
        return 1.0, 0.46 + 0.08 * ease_out(local), 0.5, 0.0
    if t < 11.9:
        local = (t - 10.1) / 1.8
        return 1.0, 0.54 - 0.08 * ease_out(local), 0.5, 0.0
    if t < 13.2:
        return 1.0, 0.50, 0.5, 0.0
    local = (t - 13.2) / 1.8
    flash = 0.28 * (1 - local / 0.1) if local < 0.1 else 0.0
    return 1.0, 0.50, 0.5, max(0, flash)


def foam_sparkles(canvas: Image.Image, t: float, seed: int = 7) -> None:
    """Soft rising foam dots — product-coded motion, not falling-hair stock."""
    if t < 2.7:
        return
    rng = np.random.default_rng(seed)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    life = min(1.0, (t - 2.7) / 0.6)
    for i in range(18):
        # deterministic float paths
        x = int((0.12 + 0.76 * ((i * 37 % 100) / 100)) * W)
        speed = 28 + (i * 13 % 40)
        y = int(H * 0.92 - ((t * speed * 8 + i * 90) % (H * 0.75)))
        r = 3 + (i % 4)
        a = int((55 + (i % 5) * 8) * life * (0.55 + 0.45 * abs(math.sin(t * 1.7 + i))))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, a))
        if i % 3 == 0:
            d.ellipse((x - r // 2, y - r - 6, x + r // 2, y - r), fill=(255, 255, 255, a // 2))
    canvas.alpha_composite(layer)
    _ = rng  # keep seed hook for future variance


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
    zoom, fx, fy, flash = beat_camera(t)
    # Hook on the blue carton (matches copy) → reveal cans
    src = box if t < 2.7 else trio
    plate = cover_window(src, zoom=zoom, focus_x=fx, focus_y=fy)
    # Soft loop back to box in last 0.6s — Shorts/Reels replay boost, doesn't change story
    if t >= 14.4:
        box_plate = cover_window(box, zoom=1.0, focus_x=0.50, focus_y=0.5)
        plate = Image.blend(plate.convert("RGB"), box_plate.convert("RGB"), ease_in((t - 14.4) / 0.6))
    canvas = grade(plate)
    canvas = flash_white(canvas, flash)
    foam_sparkles(canvas, t, seed=7)
    info = chip_at(t)
    if info:
        lines, op, slide, pop = info
        size = 50 if len(lines) > 1 else 54
        if lines and lines[0] == "BLACK FRIDAY":
            size = 58
        if lines and lines[0] == "מינוקסידיל 5%":
            size = 52
        if lines == ["מחיר שובר שוק", "395₪"]:
            size = 56
        if lines == ["אנחנו פה בשבילכם"]:
            size = 52
        if lines == ["הקישור בפרופיל"]:
            size = 58
        chip_block(canvas, int(H * 0.14), lines, size=size, opacity=op, slide_x=slide, pop=pop)
    # Logo fades in after the box tease — brand match to other reels
    if t >= 2.7:
        lo = ease_out(min(1.0, (t - 2.7) / 0.45))
        paste_logo(canvas, logo, opacity=0.9 * lo)
    return add_grain(canvas, amount=0.01, seed=i * 23 + 2).convert("RGB")


def make_audio(path: Path) -> None:
    """Warm soft beat — closer to BF reel energy, not hollow pad."""
    sr = 44100
    n = int(DUR * sr)
    rng = np.random.default_rng(11)
    t = np.arange(n) / sr
    bpm = 118  # tighter groove, less sleepy
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
        length = int(0.22 * sr)
        if i0 + length > n:
            break
        tt = np.arange(length) / sr
        freq = 95 * np.exp(-16 * tt) + 42
        amp = 0.38 if i % 2 == 0 else 0.22
        kick[i0 : i0 + length] += amp * np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-9 * tt)
        if i % 2 == 1:  # clap on offbeats
            sl = int(0.09 * sr)
            if i0 + sl <= n:
                noise = rng.standard_normal(sl)
                snare[i0 : i0 + sl] += 0.16 * noise * np.exp(-38 * np.arange(sl) / sr)

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
    # Hit on story cuts — SFX = retention cue across mute-off viewers
    for wt, amp in ((0.05, 0.14), (2.7, 0.28), (4.3, 0.2), (6.5, 0.24), (10.1, 0.16), (13.2, 0.18)):
        i0 = int(wt * sr)
        length = min(int(0.28 * sr), n - i0)
        if length <= 0:
            continue
        noise = np.convolve(rng.standard_normal(length), np.ones(100) / 100, mode="same")
        env = np.sin(np.linspace(0, np.pi, length)) ** 1.5
        whoosh[i0 : i0 + length] += 0.055 * amp * noise * env

    bed = kick + snare + bass + pad + pluck + whoosh
    quiet = int(0.08 * sr)  # almost immediate — don't bury the open
    bed[:quiet] *= np.linspace(0.55, 1, quiet)
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

    print(f"Rendering {N} frames (v7 box→cans + logo)…")
    for i in range(N):
        im = frame_at(i, box, trio, logo)
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

    cover = frame_at(int(0.35 * FPS), box, trio, logo)
    cover_path = OUT / "MinoxShop_ABC_curiosity_COVER.jpg"
    cover.save(cover_path, quality=95)

    ART.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mp4, ART / "DOWNLOAD_MinoxShop_ABC_curiosity_15s.mp4")
    shutil.copy2(cover_path, ART / "DOWNLOAD_MinoxShop_ABC_curiosity_COVER.jpg")
    shutil.copy2(mp4, ART / "abc_foam_curiosity_demo.mp4")
    shutil.copy2(cover_path, ART / "abc_foam_curiosity_cover.jpg")
    for label, sec in (("hook", 0.35), ("bf", 3.5), ("clarity", 5.2), ("ship", 10.5), ("cta", 13.5)):
        frame_at(int(sec * FPS), box, trio, logo).save(ART / f"abc_preview_{label}.jpg", quality=92)
    print("Wrote", mp4)
    return mp4


if __name__ == "__main__":
    render()
