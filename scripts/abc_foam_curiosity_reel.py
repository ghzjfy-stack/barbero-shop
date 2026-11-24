#!/usr/bin/env python3
"""MinoxShop Amazon Basic Care foam — curiosity launch reel v3.

15s · 1080×1920 · FULL-BLEED product photos (no cutout fringe).
Hook: מה יש בקופסה הכחולה מארה״ב?
Curiosity via question + delayed price — product always whole and sharp.
"""

from __future__ import annotations

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

WHITE = (255, 255, 255)
INK = (18, 20, 24)


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



def _corner_bg(im: Image.Image) -> tuple[int, int, int]:
    """Sample packshot corner so the tall stage matches with no seam."""
    arr = np.array(im.convert("RGB"))
    patches = [
        arr[0:12, 0:12],
        arr[0:12, -12:],
        arr[-12:, 0:12],
        arr[-12:, -12:],
    ]
    mean = np.mean(np.concatenate([p.reshape(-1, 3) for p in patches], axis=0), axis=0)
    return tuple(int(c) for c in mean)


def studio_plate(
    im: Image.Image,
    *,
    scale: float = 0.96,
    dy: float = 0.0,
) -> Image.Image:
    """Place the FULL product photo on a seamless matching studio stage.

    Contain (never mid-face crop). Canvas color = packshot corners → no rectangle seam.
    """
    bg = _corner_bg(im)
    canvas = Image.new("RGB", (W, H), bg)
    # Large product — fill most of the reel height while keeping whole asset
    max_w, max_h = int(W * 0.96 * scale), int(H * 0.82 * scale)
    fit_scale = min(max_w / im.width, max_h / im.height)
    nw, nh = max(1, int(im.width * fit_scale)), max(1, int(im.height * fit_scale))
    product = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (W - nw) // 2
    # Sit under chips with tight bottom margin
    y = int(H * 0.17) + max(0, (int(H * 0.78) - nh) // 2) + int(dy)
    y = max(int(H * 0.16), min(H - nh - 16, y))
    canvas.paste(product, (x, y))
    return canvas


def stage_grade(im: Image.Image) -> Image.Image:
    """Light grade + soft top veil for chips — keep studio seamless."""
    im = ImageEnhance.Contrast(im).enhance(1.03)
    im = ImageEnhance.Color(im).enhance(1.03)
    base = im.convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(0, int(H * 0.22)):
        a = int(70 * (1 - y / (H * 0.22)) ** 1.2)
        od.line((0, y, W, y), fill=(30, 40, 55, a))
    # Very light edge vignette only
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    for i in range(5):
        pad = 30 + i * 55
        vd.rectangle((0, 0, W, H), outline=(20, 28, 40, 4 + i * 4), width=pad)
    vig = vig.filter(ImageFilter.GaussianBlur(32))
    out = Image.alpha_composite(base, overlay)
    out = Image.alpha_composite(out, vig)
    return out


def add_grain(im: Image.Image, amount: float = 0.008, seed: int = 0) -> Image.Image:
    rng = np.random.default_rng(seed)
    arr = np.array(im.convert("RGBA")).astype(np.float32)
    noise = rng.standard_normal(arr.shape[:2]) * (255 * amount)
    arr[..., :3] = np.clip(arr[..., :3] + noise[..., None], 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    *,
    size: int = 64,
    fill=WHITE,
    anchor: str = "mm",
    rtl: bool = True,
    bold: bool = True,
) -> None:
    f = font(size, bold=bold)
    kwargs: dict = dict(font=f, fill=fill, anchor=anchor)
    has_he = any("\u0590" <= ch <= "\u05FF" for ch in text)
    if rtl and has_he:
        kwargs["direction"] = "rtl"
        kwargs["language"] = "he"
    draw.text(xy, text, **kwargs)


def chip_block(
    canvas: Image.Image,
    cy: int,
    lines: list[str],
    *,
    size: int = 46,
    opacity: float = 1.0,
    slide_x: float = 0.0,
) -> None:
    if opacity <= 0.02:
        return
    f = font(size)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    widths, heights = [], []
    for line in lines:
        bbox = probe.textbbox((0, 0), line, font=f, direction="rtl", language="he")
        widths.append(bbox[2] - bbox[0])
        heights.append(bbox[3] - bbox[1])
    pad_x, pad_y, gap = 44, 20, 8
    pw = max(widths) + pad_x * 2
    ph = sum(heights) + gap * (len(lines) - 1) + pad_y * 2
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0 = (W - pw) // 2 + int(slide_x)
    y0 = cy - ph // 2
    # Soft shadow under chip
    d.rounded_rectangle(
        (x0 + 3, y0 + 4, x0 + pw + 3, y0 + ph + 4),
        radius=24,
        fill=(0, 0, 0, int(90 * opacity)),
    )
    d.rounded_rectangle(
        (x0, y0, x0 + pw, y0 + ph),
        radius=24,
        fill=(255, 255, 255, int(240 * opacity)),
    )
    y = y0 + pad_y
    for line, th in zip(lines, heights):
        draw_text(
            d,
            (x0 + pw // 2, y + th // 2),
            line,
            size=size,
            fill=(*INK, int(255 * opacity)),
            rtl=True,
        )
        y += th + gap
    canvas.alpha_composite(layer)


def chip_at(t: float) -> tuple[list[str], float, float] | None:
    if 0.35 <= t < 4.8:
        local = t - 0.35
        if local < 0.28:
            slide = 36 * (1 - ease_out(local / 0.28))
            op = ease_out(local / 0.28)
        elif t > 4.6:
            op = 1.0 - ease_in((t - 4.6) / 0.2)
            slide = 0.0
        else:
            op, slide = 1.0, 0.0
        return (["מה יש בקופסה הכחולה", "מארה״ב?"], op, slide)
    if 4.9 <= t < 7.6:
        local = t - 4.9
        op = ease_out(min(1.0, local / 0.22))
        if t > 7.4:
            op = 1.0 - ease_in((t - 7.4) / 0.2)
        # No drug name on-screen — Meta Boost often flags minoxidil/health claims
        return (["קצף לגברים מארה״ב"], op, 0.0)
    if 7.7 <= t < 9.3:
        local = t - 7.7
        op = ease_out(min(1.0, local / 0.2))
        if t > 9.15:
            op = 1.0 - ease_in((t - 9.15) / 0.15)
        return (["3 חודשים"], op, 0.0)
    if 9.4 <= t < 10.6:
        local = t - 9.4
        op = ease_out(min(1.0, local / 0.2))
        if t > 10.45:
            op = 1.0 - ease_in((t - 10.45) / 0.15)
        return (["395₪"], op, 0.0)
    if 10.7 <= t < 12.6:
        local = t - 10.7
        op = ease_out(min(1.0, local / 0.2))
        if t > 12.45:
            op = 1.0 - ease_in((t - 12.45) / 0.15)
        return (["יבוא מארה״ב · משלוח חינם"], op, 0.0)
    if 12.75 <= t <= 15.01:
        local = t - 12.75
        op = ease_out(min(1.0, local / 0.25))
        return (["הקישור בפרופיל"], op, 0.0)
    return None


def crossfade(a: Image.Image, b: Image.Image, t: float) -> Image.Image:
    t = max(0.0, min(1.0, t))
    return Image.blend(a.convert("RGB"), b.convert("RGB"), t)


def frame_at(i: int, box: Image.Image, cans: Image.Image) -> Image.Image:
    """Boost-safe: cans only — carton prints 'Compare to Rogaine' and Meta blocks boost."""
    t = i / FPS
    chip_y = int(H * 0.14)
    _ = box  # kept for API compat / optional future boost-safe carton

    # Whole cans always visible — studio contain + gentle Ken Burns.
    if t < 4.8:
        local = t / 4.8
        sc = 0.94 + 0.06 * ease_out(local)
        drop = 14 * (1 - ease_out(min(1.0, t / 0.35))) if t < 0.35 else 0
        plate = studio_plate(cans, scale=sc, dy=drop)
        canvas = stage_grade(plate)
    elif t < 12.4:
        local = (t - 4.8) / 7.6
        sc = 0.98 + 0.05 * ease_out(local)
        plate = studio_plate(cans, scale=sc)
        canvas = stage_grade(plate)
    else:
        local = (t - 12.4) / 2.6
        sc = 1.02 + 0.04 * ease_out(local)
        plate = studio_plate(cans, scale=sc)
        canvas = stage_grade(plate)

    if canvas.mode != "RGBA":
        canvas = canvas.convert("RGBA")

    info = chip_at(t)
    if info:
        lines, op, slide = info
        size = 50 if len(lines) > 1 else 52
        if lines == ["395₪"]:
            size = 66
        if lines == ["הקישור בפרופיל"]:
            size = 56
        chip_block(canvas, chip_y, lines, size=size, opacity=op, slide_x=slide)

    canvas = add_grain(canvas, amount=0.008, seed=i * 17 + 3)
    return canvas.convert("RGB")


def make_audio(path: Path) -> None:
    sr = 44100
    n = int(DUR * sr)
    rng = np.random.default_rng(42)
    room = rng.standard_normal(n)
    room = np.convolve(room, np.ones(180) / 180, mode="same") * 0.026
    bed = room.copy()

    def thump(at: float, amp: float, length_s: float = 0.26, f0: float = 58.0) -> None:
        i0 = int(at * sr)
        length = min(int(length_s * sr), n - i0)
        if length <= 0 or i0 >= n:
            return
        tt = np.arange(length) / sr
        freq = f0 * np.exp(-11 * tt) + 28
        bed[i0 : i0 + length] += amp * np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-7.0 * tt)

    def whoosh(at: float, amp: float, length_s: float = 0.4) -> None:
        i0 = int(at * sr)
        length = min(int(length_s * sr), n - i0)
        if length <= 0 or i0 >= n:
            return
        noise = np.convolve(rng.standard_normal(length), np.ones(100) / 100, mode="same")
        env = np.sin(np.linspace(0, np.pi, length)) ** 1.5
        bed[i0 : i0 + length] += amp * noise * env

    thump(0.12, 0.16, 0.28, 52)
    whoosh(4.85, 0.04, 0.45)
    thump(4.9, 0.09, 0.18, 70)
    thump(9.4, 0.08, 0.16, 90)
    whoosh(12.5, 0.035, 0.5)
    thump(12.55, 0.09, 0.28, 48)

    quiet = int(0.3 * sr)
    bed[:quiet] *= np.linspace(0.2, 1.0, quiet)
    peak = np.max(np.abs(bed)) + 1e-9
    bed = np.tanh(bed / peak * 0.55 * 1.05) * 0.85
    bed = np.convolve(bed, np.ones(9) / 9, mode="same")
    fi, fo = int(0.15 * sr), int(0.5 * sr)
    bed[:fi] *= np.linspace(0, 1, fi)
    bed[-fo:] *= np.linspace(1, 0, fo)
    audio = np.clip(bed, -1, 1)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(x * 28000)) for x in audio))


def render() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    frames = OUT / "frames"
    if frames.exists():
        shutil.rmtree(frames)
    frames.mkdir()

    # Cans only (no Rogaine carton). Chip copy avoids the drug name for Boost scans.
    box = load_rgb(ASSETS / "box.png")
    cans = load_rgb(ASSETS / "cans.png")

    print(f"Rendering {N} frames (full-bleed)…")
    for i in range(N):
        im = frame_at(i, box, cans)
        im.save(frames / f"f_{i:05d}.png")
        if i % 60 == 0:
            print(f"  {i}/{N}")

    audio = OUT / "audio.wav"
    make_audio(audio)

    mp4 = OUT / "MinoxShop_ABC_curiosity_15s.mp4"
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-framerate",
            str(FPS),
            "-i",
            str(frames / "f_%05d.png"),
            "-i",
            str(audio),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(mp4),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    cover = frame_at(int(1.2 * FPS), box, cans)
    cover_path = OUT / "MinoxShop_ABC_curiosity_COVER.jpg"
    cover.save(cover_path, quality=95)

    ART.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mp4, ART / "DOWNLOAD_MinoxShop_ABC_curiosity_15s.mp4")
    shutil.copy2(cover_path, ART / "DOWNLOAD_MinoxShop_ABC_curiosity_COVER.jpg")
    shutil.copy2(mp4, ART / "abc_foam_curiosity_demo.mp4")
    shutil.copy2(cover_path, ART / "abc_foam_curiosity_cover.jpg")

    for label, sec in (("hook", 1.2), ("swap", 5.8), ("cans", 8.5), ("price", 9.8), ("cta", 13.5)):
        frame_at(int(sec * FPS), box, cans).save(ART / f"abc_preview_{label}.jpg", quality=92)

    print("Wrote", mp4)
    print("Wrote", cover_path)
    return mp4


if __name__ == "__main__":
    render()
