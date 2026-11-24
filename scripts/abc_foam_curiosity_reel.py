#!/usr/bin/env python3
"""MinoxShop Amazon Basic Care foam — curiosity launch reel.

15s · 1080×1920 · Hebrew chips · soft room-tone audio · profile CTA.
Hook: מה יש בקופסה הכחולה מארה״ב?
Grok polish: withhold → reveal → loop back to the same crop.
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
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, DUR = 1080, 1920, 30, 15
N = FPS * DUR

ASSETS = Path(os.environ.get("ABC_ASSETS", "/tmp/minox-amazon"))
OUT = Path(os.environ.get("ABC_OUT", "/tmp/abc-foam-curiosity"))
ART = Path("/opt/cursor/artifacts")

FONT = "/usr/share/fonts/truetype/croscore/Arimo-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/croscore/Arimo-Regular.ttf"

WHITE = (255, 255, 255)
INK = (18, 20, 24)
COUNTER = (12, 16, 20)


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


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def knock_white(im: Image.Image, thresh: float = 220.0) -> Image.Image:
    """Fringe near-white studio plate into soft alpha; slight edge soften."""
    arr = np.array(im).astype(np.float32)
    rgb = arr[..., :3]
    whiteness = np.min(rgb, axis=2)
    fringe = np.clip((whiteness - thresh) / 28.0, 0, 1)
    arr[..., 3] = arr[..., 3] * (1.0 - fringe * 0.98)
    out = Image.fromarray(arr.astype(np.uint8), "RGBA")
    # Soften hard cut edges without eating the product
    a = out.split()[-1].filter(ImageFilter.GaussianBlur(0.8))
    out.putalpha(a)
    return out


def fit_contain(im: Image.Image, tw: int, th: int) -> Image.Image:
    scale = min(tw / im.width, th / im.height)
    nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    return im.resize((nw, nh), Image.Resampling.LANCZOS)


def dark_counter() -> Image.Image:
    canvas = Image.new("RGBA", (W, H), (*COUNTER, 255))
    # subtle vertical gradient + warm navy glow
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for y in range(H):
        a = int(55 * (y / H))
        d.line((0, y, W, y), fill=(0, 0, 0, a))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy = int(W * 0.55), int(H * 0.58)
    for r, a in ((520, 55), (340, 70), (200, 90)):
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(28, 48, 78, a))
    glow = glow.filter(ImageFilter.GaussianBlur(48))
    canvas = Image.alpha_composite(canvas, overlay)
    canvas = Image.alpha_composite(canvas, glow)
    # vignette
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    for i in range(10):
        pad = 30 + i * 55
        vd.rectangle((0, 0, W, H), outline=(0, 0, 0, 10 + i * 7), width=pad)
    vig = vig.filter(ImageFilter.GaussianBlur(28))
    return Image.alpha_composite(canvas, vig)


def add_grain(im: Image.Image, amount: float = 0.02, seed: int = 0) -> Image.Image:
    rng = np.random.default_rng(seed)
    arr = np.array(im).astype(np.float32)
    noise = rng.standard_normal(arr.shape[:2]) * (255 * amount)
    arr[..., :3] = np.clip(arr[..., :3] + noise[..., None], 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def soft_shadow(size: tuple[int, int], blur: int = 42, opacity: int = 90) -> Image.Image:
    """Soft contact shadow only — no bright floor spotlight (avoids banding)."""
    w, h = size
    sh = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    # Dark oval under product feet
    d.ellipse(
        (int(w * 0.18) + 40, int(h * 0.82) + 40, int(w * 0.82) + 40, int(h * 0.96) + 40),
        fill=(0, 0, 0, opacity),
    )
    # Very soft navy pool (low alpha) — extra blur kills banding
    d.ellipse(
        (int(w * 0.10) + 40, int(h * 0.78) + 40, int(w * 0.90) + 40, int(h * 1.02) + 40),
        fill=(20, 36, 58, 35),
    )
    return sh.filter(ImageFilter.GaussianBlur(max(36, blur)))


def paste_product(
    canvas: Image.Image,
    product: Image.Image,
    *,
    cy: int,
    max_w: int,
    max_h: int,
    scale: float = 1.0,
    dx: int = 0,
    dy: int = 0,
    shadow_blur: int = 42,
    shadow_op: int = 90,
) -> None:
    im = fit_contain(product, int(max_w * scale), int(max_h * scale))
    shadow = soft_shadow(im.size, blur=shadow_blur, opacity=shadow_op)
    sx = (W - shadow.width) // 2 + dx
    sy = cy - im.height // 2 + dy + 8
    # Clamp so shadow never goes off-canvas (avoids hard clip banding)
    sx = max(0, min(W - shadow.width, sx))
    sy = max(0, min(H - shadow.height, sy))
    canvas.alpha_composite(shadow, (sx, sy))
    x = (W - im.width) // 2 + dx
    y = cy - im.height // 2 + dy
    canvas.alpha_composite(im, (x, y))


def draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    *,
    size: int = 64,
    fill=WHITE,
    anchor: str = "mm",
    rtl: bool = True,
    stroke: int = 0,
    stroke_fill=(0, 0, 0),
    bold: bool = True,
) -> None:
    f = font(size, bold=bold)
    kwargs = dict(font=f, fill=fill, anchor=anchor)
    if stroke:
        kwargs["stroke_width"] = stroke
        kwargs["stroke_fill"] = stroke_fill
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
    pad_x, pad_y, gap = 46, 22, 10
    pw = max(widths) + pad_x * 2
    ph = sum(heights) + gap * (len(lines) - 1) + pad_y * 2
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0 = (W - pw) // 2 + int(slide_x)
    y0 = cy - ph // 2
    fill = (255, 255, 255, int(235 * opacity))
    d.rounded_rectangle((x0, y0, x0 + pw, y0 + ph), radius=26, fill=fill)
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


def flap_wedge(canvas: Image.Image, open_t: float) -> None:
    """Matte black cardboard flap growing from top — carton 'opening' without real video."""
    open_t = max(0.0, min(1.0, open_t))
    if open_t <= 0.01:
        return
    h = int(160 * ease_out(open_t))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # trapezoid flap descending
    top = int(H * 0.38)
    d.polygon(
        [
            (int(W * 0.18), top),
            (int(W * 0.82), top),
            (int(W * 0.88), top + h),
            (int(W * 0.12), top + h),
        ],
        fill=(8, 10, 12, int(220 * open_t)),
    )
    layer = layer.filter(ImageFilter.GaussianBlur(2))
    canvas.alpha_composite(layer)


def foam_puff(canvas: Image.Image, cx: int, cy: int, t: float) -> None:
    """Subtle foam bloom — keep soft so it never reads as a lens flare."""
    if t <= 0 or t > 1.2:
        return
    a = ease_out(min(1.0, t / 0.4)) * (1.0 - ease_in(max(0.0, (t - 0.7) / 0.5)))
    if a <= 0.02:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r = int(18 + 22 * a)
    for i, (ox, oy, rr) in enumerate(
        ((0, 0, r), (-12, 8, int(r * 0.65)), (11, 6, int(r * 0.55)))
    ):
        alpha = int((110 - i * 22) * a)
        d.ellipse((cx + ox - rr, cy + oy - rr, cx + ox + rr, cy + oy + rr), fill=(245, 248, 255, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(8))
    canvas.alpha_composite(layer)


def one_can_crop(cans: Image.Image) -> Image.Image:
    """One can only — cap + blue label top. No multi-can read."""
    w, h = cans.size
    # Leftmost can, mostly upper body
    x0 = int(w * 0.02)
    x1 = int(w * 0.38)
    y0 = int(h * 0.00)
    y1 = int(h * 0.62)
    return cans.crop((x0, y0, x1, y1))


def box_safe_face(box: Image.Image) -> Image.Image:
    """Front without the right-side 'Compare to Rogaine' badge."""
    w, h = box.size
    # Badge sits mid-right; keep left ~62% and drop the top wordmark strip a bit
    return box.crop((0, int(h * 0.08), int(w * 0.62), h))


def box_bottom_mystery(box: Image.Image) -> Image.Image:
    """Lower-right navy corner — 3-can icon + color. No brand, no compare, little readable copy."""
    w, h = box.size
    return box.crop((int(w * 0.42), int(h * 0.62), int(w * 0.98), int(h * 0.99)))


def chip_at(t: float) -> tuple[list[str], float, float] | None:
    """Return (lines, opacity, slide_x) for current time. Split chips per Grok."""
    # Hook 0.40–5.40 with RTL slide-in
    if 0.40 <= t < 5.40:
        local = t - 0.40
        if local < 0.28:
            slide = 48 * (1 - ease_out(local / 0.28))
            op = ease_out(local / 0.28)
        elif t > 5.25:
            op = 1.0 - ease_in((t - 5.25) / 0.15)
            slide = 0.0
        else:
            op, slide = 1.0, 0.0
        return (["מה יש בקופסה הכחולה", "מארה״ב?"], op, slide)
    if 5.45 <= t < 7.55:
        local = t - 5.45
        op = ease_out(min(1.0, local / 0.22))
        if t > 7.40:
            op = 1.0 - ease_in((t - 7.40) / 0.15)
        return (["מינוקסידיל 5% · קצף לגברים"], op, 0.0)
    if 7.60 <= t < 9.35:
        local = t - 7.60
        op = ease_out(min(1.0, local / 0.2))
        if t > 9.20:
            op = 1.0 - ease_in((t - 9.20) / 0.15)
        return (["3 חודשים"], op, 0.0)
    if 9.40 <= t < 10.50:
        local = t - 9.40
        op = ease_out(min(1.0, local / 0.2))
        if t > 10.35:
            op = 1.0 - ease_in((t - 10.35) / 0.15)
        return (["395₪"], op, 0.0)
    if 10.55 <= t < 12.60:
        local = t - 10.55
        op = ease_out(min(1.0, local / 0.2))
        if t > 12.45:
            op = 1.0 - ease_in((t - 12.45) / 0.15)
        return (["יבוא מארה״ב · משלוח חינם"], op, 0.0)
    if 12.70 <= t <= 15.01:
        local = t - 12.70
        op = ease_out(min(1.0, local / 0.25))
        return (["הקישור בפרופיל"], op, 0.0)
    return None


def frame_at(
    i: int,
    box: Image.Image,
    cans: Image.Image,
    can_one: Image.Image,
    box_safe: Image.Image,
    box_mystery: Image.Image,
) -> Image.Image:
    t = i / FPS
    canvas = dark_counter()
    chip_y = int(H * 0.22)  # upper third ~18–28%

    # --- Beat 1: 0–3.5 mystery corner (no wordmark, no Rogaine badge) ---
    if t < 3.5:
        if t < 0.35:
            drop = 22 * (1 - ease_out(t / 0.35))
            blur = int(36 - 14 * ease_out(t / 0.35))
            zoom = 1.38
        else:
            drop = 0
            blur = 22
            local = (t - 0.35) / 3.15
            zoom = 1.38 - 0.20 * ease_out(local)  # → 1.18
        scale = 1.35 * (zoom / 1.28)
        paste_product(
            canvas,
            box_mystery,
            cy=int(H * 0.58) + int(drop),
            max_w=780,
            max_h=680,
            scale=scale,
            shadow_blur=blur,
            shadow_op=int(140 * (0.7 + 0.3 * (1 - drop / 22 if t < 0.35 else 1))),
        )

    # --- Beat 2a: 3.5–5.3 flap open on SAFE face (Rogaine badge cropped out) ---
    elif t < 5.3:
        local = (t - 3.5) / 1.8
        zoom = 1.18 + 0.08 * ease_out(local)
        paste_product(
            canvas,
            box_safe,
            cy=int(H * 0.56),
            max_w=720,
            max_h=980,
            scale=0.95 * zoom / 1.2,
            shadow_blur=24,
        )
        flap_wedge(canvas, ease_out(local))

    # --- Beat 2b: 5.3–7.5 one can + soft foam puff ---
    elif t < 7.5:
        if t < 5.3 + 4 / FPS:
            punch = 1.16
        else:
            punch = 1.16 - 0.08 * ease_out((t - 5.3 - 4 / FPS) / 2.0)  # → 1.08
        paste_product(
            canvas,
            can_one,
            cy=int(H * 0.54),
            max_w=560,
            max_h=980,
            scale=punch,
            shadow_blur=26,
        )
        foam_puff(canvas, W // 2 + 90, int(H * 0.68), t - 5.45)

    # --- Beat 3: 7.5–11.5 three cans counted, then hold ---
    elif t < 11.5:
        base = cans
        if t < 8.15:
            w, h = base.size
            piece = base.crop((0, 0, int(w * 0.38), h))
            paste_product(canvas, piece, cy=int(H * 0.55), max_w=400, max_h=980, scale=1.08)
        elif t < 8.85:
            slide = ease_out(min(1.0, (t - 8.15) / 0.32))
            w, h = base.size
            piece = base.crop((0, 0, int(w * (0.38 + 0.32 * slide)), h))
            dx = int(140 * (1 - slide))
            paste_product(
                canvas, piece, cy=int(H * 0.55), max_w=640, max_h=980, scale=1.0, dx=-dx // 2
            )
        else:
            slide = ease_out(min(1.0, (t - 8.85) / 0.32)) if t < 9.2 else 1.0
            dx = int(140 * (1 - slide)) if t < 9.2 else 0
            paste_product(
                canvas,
                base,
                cy=int(H * 0.55),
                max_w=920,
                max_h=1000,
                scale=0.98,
                dx=-dx // 3,
            )

    # --- Beat 4: 11.5–15 close on safe face, then push into mystery corner ---
    else:
        if t < 12.4:
            close_t = 1.0 - ease_in_out((t - 11.5) / 0.9)
            paste_product(
                canvas,
                box_safe,
                cy=int(H * 0.56),
                max_w=720,
                max_h=980,
                scale=0.95,
                shadow_blur=24,
            )
            flap_wedge(canvas, max(0.0, close_t * 0.85))
        else:
            local = (t - 12.4) / 2.6
            zoom = 1.12 + 0.46 * ease_in(local)  # → 1.58
            paste_product(
                canvas,
                box_mystery,
                cy=int(H * 0.58),
                max_w=780,
                max_h=680,
                scale=1.35 * (zoom / 1.28),
                shadow_blur=22,
            )

    # Chips
    chip_info = chip_at(t)
    if chip_info:
        lines, op, slide = chip_info
        size = 48 if len(lines) > 1 or len(lines[0]) > 18 else 52
        if lines == ["הקישור בפרופיל"]:
            size = 54
        if lines == ["395₪"]:
            size = 64
        chip_block(canvas, chip_y, lines, size=size, opacity=op, slide_x=slide)

    canvas = add_grain(canvas, amount=0.012, seed=i * 17 + 3)
    return canvas.convert("RGB")


def make_audio(path: Path) -> None:
    """Quiet room tone + timed foley (set-down, crease, puff, taps, whoosh). No VO."""
    sr = 44100
    n = int(DUR * sr)
    rng = np.random.default_rng(42)
    t = np.arange(n) / sr

    # Steady room tone (very soft brownish noise)
    room = rng.standard_normal(n)
    room = np.convolve(room, np.ones(180) / 180, mode="same")
    room *= 0.028

    bed = room.copy()

    def add_thump(at: float, amp: float, length_s: float = 0.26, f0: float = 58.0) -> None:
        i0 = int(at * sr)
        length = int(length_s * sr)
        if i0 >= n:
            return
        length = min(length, n - i0)
        tt = np.arange(length) / sr
        freq = f0 * np.exp(-11 * tt) + 28
        hit = np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-7.0 * tt)
        bed[i0 : i0 + length] += amp * hit

    def add_noise_burst(at: float, amp: float, length_s: float, smooth: int = 90) -> None:
        i0 = int(at * sr)
        length = int(length_s * sr)
        if i0 >= n:
            return
        length = min(length, n - i0)
        noise = rng.standard_normal(length)
        noise = np.convolve(noise, np.ones(smooth) / smooth, mode="same")
        env = np.sin(np.linspace(0, np.pi, length)) ** 1.5
        bed[i0 : i0 + length] += amp * noise * env

    # 0.12–0.38 set-down thump
    add_thump(0.12, 0.22, 0.28, 52)
    # 3.52–4.05 cardboard crease
    add_noise_burst(3.52, 0.045, 0.48, smooth=40)
    # 5.32 dry cut tick + 5.45 soft air puff
    add_thump(5.32, 0.12, 0.12, 90)
    add_noise_burst(5.45, 0.038, 0.28, smooth=70)
    # 8.15 / 8.85 can taps
    add_thump(8.15, 0.10, 0.10, 140)
    add_thump(8.85, 0.10, 0.10, 130)
    # 11.55 flap shut
    add_thump(11.55, 0.14, 0.28, 48)
    add_noise_burst(11.55, 0.03, 0.35, smooth=55)
    # 12.55 low whoosh under push
    add_noise_burst(12.55, 0.04, 0.55, smooth=120)
    add_thump(12.55, 0.08, 0.35, 42)

    # near-silence under first hook text settle
    quiet = int(0.35 * sr)
    bed[:quiet] *= np.linspace(0.2, 1.0, quiet)

    peak = np.max(np.abs(bed)) + 1e-9
    bed = bed / peak * 0.55
    bed = np.tanh(bed * 1.05) * 0.85
    bed = np.convolve(bed, np.ones(9) / 9, mode="same")

    fade_in = int(0.15 * sr)
    fade_out = int(0.5 * sr)
    bed[:fade_in] *= np.linspace(0, 1, fade_in)
    bed[-fade_out:] *= np.linspace(1, 0, fade_out)

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

    box_raw = load_rgba(ASSETS / "box.png")
    cans_raw = load_rgba(ASSETS / "cans.png")
    box = knock_white(box_raw)
    cans = knock_white(cans_raw)
    can_one = knock_white(one_can_crop(cans_raw))
    box_safe = knock_white(box_safe_face(box_raw))
    box_mystery = knock_white(box_bottom_mystery(box_raw))

    print(f"Rendering {N} frames…")
    for i in range(N):
        im = frame_at(i, box, cans, can_one, box_safe, box_mystery)
        im.save(frames / f"f_{i:05d}.png")
        if i % 60 == 0:
            print(f"  {i}/{N}")

    audio = OUT / "audio.wav"
    make_audio(audio)

    mp4 = OUT / "MinoxShop_ABC_curiosity_15s.mp4"
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(frames / f"f_%05d.png"),
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
    ]
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Cover: t=1.20s, square-friendly chip already upper
    cover = frame_at(int(1.20 * FPS), box, cans, can_one, box_safe, box_mystery)
    cover_path = OUT / "MinoxShop_ABC_curiosity_COVER.jpg"
    cover.save(cover_path, quality=95)

    ART.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mp4, ART / "DOWNLOAD_MinoxShop_ABC_curiosity_15s.mp4")
    shutil.copy2(cover_path, ART / "DOWNLOAD_MinoxShop_ABC_curiosity_COVER.jpg")
    shutil.copy2(mp4, ART / "abc_foam_curiosity_demo.mp4")
    shutil.copy2(cover_path, ART / "abc_foam_curiosity_cover.jpg")

    # Preview stills for QA
    for label, sec in (("hook", 1.2), ("open", 4.2), ("can", 6.0), ("price", 9.8), ("cta", 13.5)):
        frame_at(int(sec * FPS), box, cans, can_one, box_safe, box_mystery).save(
            ART / f"abc_preview_{label}.jpg", quality=92
        )

    print("Wrote", mp4)
    print("Wrote", cover_path)
    return mp4


if __name__ == "__main__":
    render()
