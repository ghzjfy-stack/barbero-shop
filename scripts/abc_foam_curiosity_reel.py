#!/usr/bin/env python3
"""MinoxShop Amazon Basic Care — curiosity reel v6 (impression cut).

15s · 1080×1920 · cans-only (boost-safe, no Rogaine carton).
Dark atmosphere + clean edge-keyed cans + punchier motion.
Hook: מה יש בקופסה הכחולה מארה״ב?
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
LIFE = Path(os.environ.get("MINOX_ASSETS", "/tmp/minox-mp"))
OUT = Path(os.environ.get("ABC_OUT", "/tmp/abc-foam-curiosity"))
ART = Path("/opt/cursor/artifacts")

FONT = "/usr/share/fonts/truetype/croscore/Arimo-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/croscore/Arimo-Regular.ttf"

WHITE = (255, 255, 255)
INK = (14, 16, 20)


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


def fit_contain(im: Image.Image, tw: int, th: int) -> Image.Image:
    scale = min(tw / im.width, th / im.height)
    nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    return im.resize((nw, nh), Image.Resampling.LANCZOS)


def packshot_plate(
    canvas: Image.Image,
    pack: Image.Image,
    *,
    cy: int,
    max_w: int,
    max_h: int,
    scale: float = 1.0,
    dx: int = 0,
    dy: int = 0,
) -> None:
    """Paste FULL RGB packshot (caps intact — no keying). Soft-feather sides/bottom only."""
    im = fit_contain(pack.convert("RGB"), int(max_w * scale), int(max_h * scale)).convert("RGBA")
    # Asymmetric feather: almost no top fade so clear caps stay crisp;
    # sides + bottom melt into the dark stage.
    mask = Image.new("L", im.size, 255)
    md = ImageDraw.Draw(mask)
    side = max(22, int(im.width * 0.05))
    bottom = max(28, int(im.height * 0.06))
    # NO top fade — clear caps must stay fully opaque
    md.rectangle((0, im.height - bottom, im.width, im.height), fill=0)
    md.rectangle((0, 0, side, im.height), fill=0)
    md.rectangle((im.width - side, 0, im.width, im.height), fill=0)
    mask = mask.filter(ImageFilter.GaussianBlur(max(14, side // 2)))
    im.putalpha(mask)
    x = (W - im.width) // 2 + dx
    y = cy - im.height // 2 + dy
    canvas.alpha_composite(im, (x, y))


def fit_cover(im: Image.Image, tw: int, th: int, zoom: float = 1.0, pan: float = 0.5) -> Image.Image:
    zoom = max(1.0, zoom)
    scale = max(tw / im.width, th / im.height) * zoom
    nw, nh = max(tw, int(im.width * scale)), max(th, int(im.height * scale))
    r = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - tw) // 2
    max_y = max(0, nh - th)
    y = int(max_y * max(0.0, min(1.0, pan)))
    return r.crop((x, y, x + tw, y + th))


def dark_stage(life: Image.Image | None, t: float) -> Image.Image:
    """Moody navy stage with slow-drifting blurred life plate."""
    canvas = Image.new("RGBA", (W, H), (8, 10, 16, 255))
    if life is not None:
        zoom = 1.08 + 0.06 * ease_out(min(1.0, t / DUR))
        pan = 0.35 + 0.15 * (t / DUR)
        bg = fit_cover(life.convert("RGBA"), W, H, zoom=zoom, pan=pan)
        bg = ImageEnhance.Brightness(bg).enhance(0.28)
        bg = ImageEnhance.Color(bg).enhance(0.55)
        bg = bg.filter(ImageFilter.GaussianBlur(18))
        canvas = Image.alpha_composite(canvas, bg)
    # Navy glow behind product
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy = W // 2, int(H * 0.55)
    for r, a in ((580, 70), (380, 95), (220, 120)):
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(30, 55, 95, a))
    glow = glow.filter(ImageFilter.GaussianBlur(50))
    canvas = Image.alpha_composite(canvas, glow)
    # Soft top veil only above chip zone — stop before product caps
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(veil)
    for y in range(0, int(H * 0.18)):
        a = int(100 * (1 - y / (H * 0.18)) ** 1.2)
        vd.line((0, y, W, y), fill=(4, 6, 10, a))
    for y in range(int(H * 0.82), H):
        a = int(140 * ((y - H * 0.82) / (H * 0.18)))
        vd.line((0, y, W, y), fill=(4, 6, 10, min(170, a)))
    # Vignette
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vgd = ImageDraw.Draw(vig)
    for i in range(8):
        pad = 24 + i * 48
        vgd.rectangle((0, 0, W, H), outline=(0, 0, 0, 8 + i * 7), width=pad)
    vig = vig.filter(ImageFilter.GaussianBlur(26))
    canvas = Image.alpha_composite(canvas, veil)
    return Image.alpha_composite(canvas, vig)



def add_grain(im: Image.Image, amount: float = 0.012, seed: int = 0) -> Image.Image:
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
    if rtl and any("\u0590" <= ch <= "\u05FF" for ch in text):
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
    scale: float = 1.0,
) -> None:
    if opacity <= 0.02:
        return
    size = max(28, int(size * scale))
    f = font(size)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    widths, heights = [], []
    for line in lines:
        bbox = probe.textbbox((0, 0), line, font=f, direction="rtl", language="he")
        widths.append(bbox[2] - bbox[0])
        heights.append(bbox[3] - bbox[1])
    pad_x, pad_y, gap = 48, 22, 8
    pw = max(widths) + pad_x * 2
    ph = sum(heights) + gap * (len(lines) - 1) + pad_y * 2
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0 = (W - pw) // 2 + int(slide_x)
    y0 = cy - ph // 2
    d.rounded_rectangle(
        (x0 + 4, y0 + 5, x0 + pw + 4, y0 + ph + 5),
        radius=26,
        fill=(0, 0, 0, int(110 * opacity)),
    )
    d.rounded_rectangle(
        (x0, y0, x0 + pw, y0 + ph),
        radius=26,
        fill=(255, 255, 255, int(242 * opacity)),
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


def chip_at(t: float) -> tuple[list[str], float, float, float] | None:
    """lines, opacity, slide_x, pop_scale"""
    if 0.30 <= t < 4.5:
        local = t - 0.30
        if local < 0.32:
            slide = 52 * (1 - ease_out(local / 0.32))
            op = ease_out(local / 0.32)
            pop = 0.92 + 0.12 * ease_out(local / 0.32)
        elif t > 4.25:
            op = 1.0 - ease_in((t - 4.25) / 0.25)
            slide, pop = 0.0, 1.0
        else:
            op, slide, pop = 1.0, 0.0, 1.0
        return (["מה יש בקופסה הכחולה", "מארה״ב?"], op, slide, pop)
    if 4.6 <= t < 7.3:
        local = t - 4.6
        op = ease_out(min(1.0, local / 0.2))
        pop = 1.0 + 0.08 * (1 - ease_out(min(1.0, local / 0.35)))
        if t > 7.1:
            op = 1.0 - ease_in((t - 7.1) / 0.2)
        return (["קצף לגברים מארה״ב"], op, 0.0, pop)
    if 7.4 <= t < 9.2:
        local = t - 7.4
        op = ease_out(min(1.0, local / 0.18))
        pop = 1.0 + 0.1 * (1 - ease_out(min(1.0, local / 0.3)))
        if t > 9.0:
            op = 1.0 - ease_in((t - 9.0) / 0.2)
        return (["3 חודשים"], op, 0.0, pop)
    if 9.3 <= t < 10.7:
        local = t - 9.3
        op = ease_out(min(1.0, local / 0.18))
        pop = 1.0 + 0.14 * (1 - ease_out(min(1.0, local / 0.28)))
        if t > 10.5:
            op = 1.0 - ease_in((t - 10.5) / 0.2)
        return (["395₪"], op, 0.0, pop)
    if 10.8 <= t < 12.6:
        local = t - 10.8
        op = ease_out(min(1.0, local / 0.2))
        pop = 1.0
        if t > 12.4:
            op = 1.0 - ease_in((t - 12.4) / 0.2)
        return (["יבוא מארה״ב · משלוח חינם"], op, 0.0, pop)
    if 12.75 <= t <= 15.01:
        local = t - 12.75
        op = ease_out(min(1.0, local / 0.25))
        pop = 1.0 + 0.06 * (1 - ease_out(min(1.0, local / 0.35)))
        return (["הקישור בפרופיל"], op, 0.0, pop)
    return None


def one_can(cans: Image.Image) -> Image.Image:
    """Left can only, full height including clear cap — no neighbor sliver."""
    w, h = cans.size
    # Keep top/bottom padding from packshot so the clear cap stays whole
    return cans.crop((int(w * 0.02), int(h * 0.02), int(w * 0.36), int(h * 0.98)))


def frame_at(
    i: int,
    cans: Image.Image,
    can1: Image.Image,
    life: Image.Image | None,
) -> Image.Image:
    t = i / FPS
    canvas = dark_stage(life, t)
    chip_y = int(H * 0.15)

    # Full packshots (no keying) so clear caps stay intact.
    # 0–4.5  three cans settle + slow push-in (hook)
    # 4.5–7.4 hard cut to one can
    # 7.4–12.5 three cans again (price/facts)
    # 12.5–15  push-in + CTA
    if t < 4.5:
        local = t / 4.5
        drop = 28 * (1 - ease_out(min(1.0, t / 0.4))) if t < 0.4 else 0
        sc = 0.86 + 0.08 * ease_out(local)
        dx = int(10 * np.sin(local * np.pi))
        # Slightly lower + modest scale → headroom above clear caps
        packshot_plate(
            canvas,
            cans,
            cy=int(H * 0.58) + int(drop),
            max_w=920,
            max_h=1180,
            scale=sc,
            dx=dx,
        )
    elif t < 7.4:
        punch = 1.12 if t < 4.5 + 4 / FPS else 1.06 - 0.04 * ease_out(
            min(1.0, (t - 4.5 - 4 / FPS) / 2.5)
        )
        packshot_plate(
            canvas,
            can1,
            cy=int(H * 0.57),
            max_w=560,
            max_h=1240,
            scale=punch,
        )
    elif t < 12.5:
        local = (t - 7.4) / 5.1
        sc = 0.92 + 0.06 * ease_out(local)
        dx = int(-8 + 16 * ease_in_out(local))
        packshot_plate(
            canvas,
            cans,
            cy=int(H * 0.58),
            max_w=940,
            max_h=1200,
            scale=sc,
            dx=dx,
        )
    else:
        local = (t - 12.5) / 2.5
        sc = 0.96 + 0.06 * ease_in(local)
        packshot_plate(
            canvas,
            cans,
            cy=int(H * 0.58),
            max_w=940,
            max_h=1200,
            scale=sc,
        )

    info = chip_at(t)
    if info:
        lines, op, slide, pop = info
        size = 50 if len(lines) > 1 else 54
        if lines == ["395₪"]:
            size = 70
        if lines == ["הקישור בפרופיל"]:
            size = 58
        chip_block(canvas, chip_y, lines, size=size, opacity=op, slide_x=slide, scale=pop)

    return add_grain(canvas, amount=0.012, seed=i * 19 + 5).convert("RGB")


def make_audio(path: Path) -> None:
    sr = 44100
    n = int(DUR * sr)
    rng = np.random.default_rng(7)
    t = np.arange(n) / sr
    # Soft dark pad
    pad = np.zeros(n)
    for f in (73.42, 87.31, 110.0, 146.83):
        pad += np.sin(2 * np.pi * f * (1 + 0.0015 * rng.standard_normal()) * t)
    pad = pad / 5.0 * 0.07
    pad *= 0.75 + 0.25 * np.sin(2 * np.pi * 0.09 * t)
    room = np.convolve(rng.standard_normal(n), np.ones(160) / 160, mode="same") * 0.02
    bed = pad + room

    def thump(at: float, amp: float, length_s: float = 0.28, f0: float = 55.0) -> None:
        i0 = int(at * sr)
        length = min(int(length_s * sr), n - i0)
        if length <= 0 or i0 >= n:
            return
        tt = np.arange(length) / sr
        freq = f0 * np.exp(-12 * tt) + 30
        bed[i0 : i0 + length] += amp * np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-7.2 * tt)

    def whoosh(at: float, amp: float, length_s: float = 0.4) -> None:
        i0 = int(at * sr)
        length = min(int(length_s * sr), n - i0)
        if length <= 0 or i0 >= n:
            return
        noise = np.convolve(rng.standard_normal(length), np.ones(90) / 90, mode="same")
        env = np.sin(np.linspace(0, np.pi, length)) ** 1.5
        bed[i0 : i0 + length] += amp * noise * env

    thump(0.10, 0.22, 0.3, 50)
    whoosh(4.48, 0.05, 0.42)
    thump(4.52, 0.16, 0.2, 70)
    thump(7.4, 0.12, 0.18, 80)
    thump(9.3, 0.14, 0.2, 95)
    whoosh(12.5, 0.045, 0.5)
    thump(12.55, 0.12, 0.28, 48)

    quiet = int(0.28 * sr)
    bed[:quiet] *= np.linspace(0.15, 1.0, quiet)
    peak = np.max(np.abs(bed)) + 1e-9
    bed = np.tanh(bed / peak * 0.62 * 1.05) * 0.88
    bed = np.convolve(bed, np.ones(7) / 7, mode="same")
    fi, fo = int(0.12 * sr), int(0.55 * sr)
    bed[:fi] *= np.linspace(0, 1, fi)
    bed[-fo:] *= np.linspace(1, 0, fo)
    audio = np.clip(bed, -1, 1)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(b"".join(struct.pack("<h", int(x * 29000)) for x in audio))


def render() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    frames = OUT / "frames"
    if frames.exists():
        shutil.rmtree(frames)
    frames.mkdir()

    cans_raw = load_rgb(ASSETS / "cans.png")
    # Extra white headroom so clear caps never sit on the plate edge
    pad_t = int(cans_raw.height * 0.10)
    pad_s = int(cans_raw.width * 0.05)
    pad_b = int(cans_raw.height * 0.05)
    cans = Image.new(
        "RGB",
        (cans_raw.width + 2 * pad_s, cans_raw.height + pad_t + pad_b),
        (255, 255, 255),
    )
    cans.paste(cans_raw, (pad_s, pad_t))
    can1 = one_can(cans)
    life = None
    for cand in (LIFE / "journey-growth.jpg", LIFE / "hero-life.png"):
        if cand.exists():
            life = load_rgb(cand)
            break

    print(f"Rendering {N} frames (v6 impression)…")
    for i in range(N):
        im = frame_at(i, cans, can1, life)
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

    cover = frame_at(int(1.15 * FPS), cans, can1, life)
    cover_path = OUT / "MinoxShop_ABC_curiosity_COVER.jpg"
    cover.save(cover_path, quality=95)

    ART.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mp4, ART / "DOWNLOAD_MinoxShop_ABC_curiosity_15s.mp4")
    shutil.copy2(cover_path, ART / "DOWNLOAD_MinoxShop_ABC_curiosity_COVER.jpg")
    shutil.copy2(mp4, ART / "abc_foam_curiosity_demo.mp4")
    shutil.copy2(cover_path, ART / "abc_foam_curiosity_cover.jpg")
    for label, sec in (("hook", 1.15), ("punch", 5.2), ("price", 9.6), ("cta", 13.4)):
        frame_at(int(sec * FPS), cans, can1, life).save(ART / f"abc_preview_{label}.jpg", quality=92)

    print("Wrote", mp4)
    return mp4


if __name__ == "__main__":
    render()
