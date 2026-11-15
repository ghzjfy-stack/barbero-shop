#!/usr/bin/env python3
"""MinoxShop TikTok beard hook v4 — drip on hole, clean kit.

Replace weird "islands" + double-mirror with drip-on-hole.
Clean packshot (no white smear). Clear spoken Hebrew. CapCut-silent.
"""
from __future__ import annotations

import math
import shutil
import subprocess
import wave
from array import array
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/tmp/beard-reel-v4")
ASSETS = ROOT / "assets"
FRAMES = ROOT / "frames"
EXPORTS = Path("/agent/repos/barbero-shop/exports")
ARTIFACTS = Path("/opt/cursor/artifacts")
for p in (FRAMES, ASSETS, EXPORTS, ARTIFACTS):
    p.mkdir(parents=True, exist_ok=True)

REPO_ASSETS = Path("/agent/repos/barbero-shop/exports/tiktok-beard-v4-assets")


def _asset(name: str) -> Path:
    local = ASSETS / name
    if local.exists():
        return local
    return REPO_ASSETS / name


HOLE_P = _asset("hole.jpg")
DRIP_P = _asset("drip.jpg")
FULL_P = _asset("full.jpg")
KIT_P = _asset("kit.png")
LOGO_P = _asset("logo.png")

W, H = 1080, 1920
FPS = 30
DURATION = 11.0
N = int(DURATION * FPS)

INK = (9, 9, 9)
IVORY = (244, 241, 234)
GOLD = (198, 161, 91)
GOLD_SOFT = (228, 210, 162)
MUTED = (163, 158, 147)

# DejaVu renders Hebrew + punctuation without tofu
FONT_HE_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_HE_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_LAT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size: int, bold: bool = True, he: bool = True):
    if he:
        return ImageFont.truetype(FONT_HE_B if bold else FONT_HE_R, size)
    return ImageFont.truetype(FONT_LAT_B, size)


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 0.5 * (1 - math.cos(math.pi * t))


def ease_out_back(t: float) -> float:
    t = max(0.0, min(1.0, t))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def line_u(t: float, start: float, end: float, fi: float = 0.22, fo: float = 0.25) -> float:
    if t < start or t > end:
        return 0.0
    u = 1.0
    if t < start + fi:
        u = ease_out((t - start) / fi)
    if t > end - fo:
        u *= max(0.0, 1.0 - (t - (end - fo)) / fo)
    return u


def is_latin_glyph(ch: str) -> bool:
    o = ord(ch)
    if ch in "₪$€£":
        return True
    if 48 <= o <= 57 or 65 <= o <= 90 or 97 <= o <= 122:
        return True
    return False


def text_bb(draw, text, fnt, language=None):
    kw = {"language": language} if language else {}
    bb = draw.textbbox((0, 0), text, font=fnt, **kw)
    return bb[2] - bb[0], bb[3] - bb[1], bb


def measure_mixed(draw, text: str, size: int, bold: bool = True):
    f_he = font(size, bold, True)
    f_lat = font(size, bold, False)
    total = 0
    i = 0
    while i < len(text):
        lat = is_latin_glyph(text[i])
        j = i + 1
        while j < len(text) and is_latin_glyph(text[j]) == lat:
            j += 1
        chunk = text[i:j]
        fnt = f_lat if lat else f_he
        tw, _, _ = text_bb(draw, chunk, fnt, None if lat else "he")
        total += tw
        i = j
    _, th, _ = text_bb(draw, "א", f_he, "he")
    return total, th


def draw_mixed_at(layer, text: str, x_left: int, y: int, size: int, fill, alpha: int = 255, bold: bool = True):
    if alpha < 8:
        return 0
    d = ImageDraw.Draw(layer)
    f_he = font(size, bold, True)
    f_lat = font(size, bold, False)
    runs = []
    i = 0
    while i < len(text):
        lat = is_latin_glyph(text[i])
        j = i + 1
        while j < len(text) and is_latin_glyph(text[j]) == lat:
            j += 1
        runs.append((text[i:j], lat))
        i = j
    x = x_left
    a = int(max(0, min(255, alpha)))
    color = (*fill[:3], a)
    for chunk, lat in reversed(runs):
        fnt = f_lat if lat else f_he
        tw, th, bb = text_bb(d, chunk, fnt, None if lat else "he")
        xy = (x - bb[0], y - bb[1])
        if lat:
            d.text(xy, chunk, font=fnt, fill=color)
        else:
            d.text(xy, chunk, font=fnt, fill=color, language="he")
        x += tw
    return x - x_left


def draw_mixed_centered(layer, text: str, y: int, size: int, fill, alpha: int = 255, bold: bool = True):
    if alpha < 8:
        return
    d = ImageDraw.Draw(layer)
    tw, _ = measure_mixed(d, text, size, bold)
    draw_mixed_at(layer, text, (W - tw) // 2, y, size, fill, alpha, bold)


def bg(t: float = 0.0) -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W * 0.88) / 780) ** 2 + ((yy + 60) / 520) ** 2)
    glow = np.clip(1 - r, 0, 1) ** 2 * (0.09 + 0.015 * math.sin(t * 1.2))
    base = np.array(INK, np.float32)
    gold = np.array(GOLD, np.float32)
    return Image.fromarray(
        np.clip(base + (gold - base) * glow[:, :, None], 0, 255).astype(np.uint8), "RGB"
    ).convert("RGBA")


def load_logo():
    if not LOGO_P.exists():
        return None
    logo = Image.open(LOGO_P).convert("RGBA")
    a = np.asarray(logo).copy()
    rgb = a[:, :, :3].astype(np.float32)
    mn, mx = rgb.min(2), rgb.max(2)
    bgm = (mn > 195) & ((mx - mn) < 35) & (rgb.mean(2) > 215)
    a[:, :, 3] = np.where(bgm, 0, a[:, :, 3]).astype(np.uint8)
    logo = Image.fromarray(a, "RGBA")
    logo.thumbnail((100, 100), Image.Resampling.LANCZOS)
    return logo


def breathing_room(im: Image.Image, pad: float = 0.16) -> Image.Image:
    """Expand canvas with blurred edge fill so Ken Burns never chops faces."""
    im = im.convert("RGB")
    w, h = im.size
    pw, ph = int(w * pad), int(h * pad)
    canvas = im.resize((w + 2 * pw, h + 2 * ph), Image.Resampling.LANCZOS)
    canvas = canvas.filter(ImageFilter.GaussianBlur(28))
    # darken edge fill slightly so subject pops
    canvas = ImageEnhance.Brightness(canvas).enhance(0.72)
    canvas.paste(im, (pw, ph))
    return canvas


def cover_zoom(im: Image.Image, zoom: float, y_bias: float = 0.38) -> Image.Image:
    zoom = max(1.0, min(1.12, zoom))
    w, h = im.size
    target_aspect = W / H
    src_aspect = w / h
    if src_aspect > target_aspect:
        base_h = h / zoom
        base_w = base_h * target_aspect
    else:
        base_w = w / zoom
        base_h = base_w / target_aspect
    base_w = min(base_w, w)
    base_h = min(base_h, h)
    x0 = (w - base_w) / 2
    y0 = max(0.0, min(h - base_h, (h - base_h) * y_bias))
    crop = im.crop((int(x0), int(y0), int(x0 + base_w), int(y0 + base_h)))
    return crop.resize((W, H), Image.Resampling.LANCZOS)


def vignette(im: Image.Image, strength: float = 0.45):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cy, cx = H * 0.42, W * 0.5
    r = np.sqrt(((xx - cx) / (W * 0.62)) ** 2 + ((yy - cy) / (H * 0.55)) ** 2)
    dark = np.clip((r - 0.55) / 0.85, 0, 1) ** 1.4 * strength
    arr = np.asarray(im.convert("RGBA")).astype(np.float32)
    arr[:, :, :3] *= (1 - dark)[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def bare_caption(im, text, y, size, fill, u):
    if u < 0.04:
        return
    a = int(255 * min(1.0, u * 1.25))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_mixed_centered(shadow, text, y + 3, size, (0, 0, 0), int(a * 0.7), True)
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    im.alpha_composite(shadow)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_mixed_centered(layer, text, y, size, fill, a, True)
    im.alpha_composite(layer)


def apply_logo(im: Image.Image, alpha: float):
    if LOGO is None or alpha < 0.04:
        return
    logo = LOGO.copy()
    logo.putalpha(logo.split()[-1].point(lambda a: int(a * alpha)))
    im.alpha_composite(logo, ((W - logo.size[0]) // 2, 48))


def place_kit(im, max_w: int, y_center: int, pop: float, alpha: float = 1.0):
    if KIT is None or pop < 0.02 or alpha < 0.02:
        return
    p = KIT.copy()
    p.thumbnail((int(max_w * (0.92 + 0.08 * ease_out_back(min(1.0, pop)))), int(max_w)), Image.Resampling.LANCZOS)
    p = ImageEnhance.Contrast(p).enhance(1.05)
    p = ImageEnhance.Sharpness(p).enhance(1.1)
    if alpha < 0.99:
        p.putalpha(p.split()[-1].point(lambda a: int(a * alpha)))
    pw, ph = p.size
    px = (W - pw) // 2
    py = int(y_center - ph / 2)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.ellipse([px + 40, py + ph - 10, px + pw - 40, py + ph + 30], fill=(0, 0, 0, int(100 * alpha * pop)))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    im.alpha_composite(sh)
    im.alpha_composite(p, (px, py))


def soft_price(im, u: float, y: int = 1380):
    if u < 0.05:
        return
    a = int(255 * min(1.0, u * 1.2))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_mixed_centered(layer, "₪765 לשנה שלמה", y, 44, GOLD, a, True)
    im.alpha_composite(layer)


def cta_chip(im, u: float, t: float = 0.0):
    if u < 0.05:
        return
    a = int(255 * min(1.0, u * 1.2))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bw, bh = 700, 84
    y0 = 1580
    pulse = 1.0 + 0.02 * (0.5 + 0.5 * math.sin((t - 9.2) * 2 * math.pi / 0.9))
    enter = 0.95 + 0.05 * ease_out_back(min(1.0, u))
    scale = enter * pulse
    bw2, bh2 = int(bw * scale), int(bh * scale)
    x0 = (W - bw2) // 2
    y0p = y0 - (bh2 - bh) // 2
    d.rounded_rectangle([x0, y0p, x0 + bw2, y0p + bh2], 20, fill=(*GOLD, a))
    draw_mixed_centered(layer, "וואטסאפ בביו", y0p + 22, 34, INK, a, True)
    im.alpha_composite(layer)


LOGO = load_logo()
HOLE = Image.open(HOLE_P).convert("RGB")
DRIP = Image.open(DRIP_P).convert("RGB")
FULL = Image.open(FULL_P).convert("RGB")
KIT = Image.open(KIT_P).convert("RGBA") if KIT_P.exists() else None


def face_plate(src: Image.Image, zoom: float, y_bias: float, vig: float, bright: float = 1.0, contrast: float = 1.0, sharp: float = 1.12):
    # Full-bleed like pain reel — soft zoom only (no letterbox padding)
    photo = cover_zoom(src, zoom, y_bias=y_bias)
    photo = ImageEnhance.Sharpness(photo).enhance(sharp)
    if bright != 1.0:
        photo = ImageEnhance.Brightness(photo).enhance(bright)
    if contrast != 1.0:
        photo = ImageEnhance.Contrast(photo).enhance(contrast)
    photo = ImageEnhance.Color(photo).enhance(1.05)
    return vignette(photo.convert("RGBA"), vig)


def render_frame(i: int) -> Image.Image:
    t = i / FPS
    im = bg(t)
    logo_a = min(1.0, t / 0.35) if t < DURATION - 0.2 else max(0.0, (DURATION - t) / 0.2)

    # A 0–1.8: clear hole
    if t < 1.80:
        z = 1.10 + 0.08 * ease_in_out(min(1.0, t / 1.7))
        layer = face_plate(HOLE, z, y_bias=0.46, vig=0.36, contrast=1.10, sharp=1.22)
        fa = ease_out(min(1.0, t / 0.22))
        if fa < 0.99:
            layer.putalpha(layer.split()[-1].point(lambda a: int(a * fa)))
        im.alpha_composite(layer)
        apply_logo(im, logo_a * 0.85)
        bare_caption(im, "פה לא צומח לי כלום", 1480, 48, IVORY, line_u(t, 0.25, 1.75, 0.25, 0.2))
        return im.convert("RGB")

    # B 1.8–3.8: DRIP on the hole (replaces weird islands + double mirror)
    if t < 3.80:
        z = 1.04 + 0.06 * ease_in_out(min(1.0, (t - 1.8) / 1.9))
        layer = face_plate(DRIP, z, y_bias=0.44, vig=0.30, contrast=1.08, sharp=1.18)
        im.alpha_composite(layer)
        apply_logo(im, logo_a)
        bare_caption(im, "שמים טיפה על החור", 1480, 46, IVORY, line_u(t, 1.95, 3.7, 0.22, 0.2))
        return im.convert("RGB")

    # C 3.8–5.5: jealousy full beard — HARD CUT (no ghost crossfade)
    if t < 5.50:
        z = 1.02 + 0.045 * ease_in_out(min(1.0, (t - 3.80) / 1.6))
        layer = face_plate(FULL, z, y_bias=0.40, vig=0.24, bright=1.05, contrast=1.08, sharp=1.16)
        im.alpha_composite(layer)
        apply_logo(im, logo_a)
        bare_caption(im, "איך יש לו זקן מלא?", 1480, 48, GOLD_SOFT, line_u(t, 3.9, 5.4, 0.22, 0.2))
        return im.convert("RGB")

    # D 5.5–8.0: clean product (no white smear) over soft drip blur
    if t < 8.00:
        plate = face_plate(DRIP, 1.12, y_bias=0.45, vig=0.55, bright=0.42, contrast=0.95, sharp=1.0)
        plate = plate.filter(ImageFilter.GaussianBlur(24))
        im.alpha_composite(plate)
        apply_logo(im, logo_a)
        u = line_u(t, 5.5, 7.95, 0.28, 0.16)
        float_z = 1.0 + 0.03 * math.sin((t - 5.5) * 2.0)
        place_kit(im, int(920 * float_z), int(680 - 8 * math.sin((t - 5.5) * 1.4)), pop=u, alpha=1.0)
        bare_caption(im, "קירקלנד גם לזקן", 1400, 44, IVORY, u)
        bare_caption(im, "לא רק לראש", 1500, 40, GOLD_SOFT, line_u(t, 6.05, 7.95, 0.25, 0.16))
        return im.convert("RGB")

    # E 8.0–11: product + price + WA
    plate = face_plate(DRIP, 1.10, y_bias=0.45, vig=0.58, bright=0.38, contrast=0.95, sharp=1.0)
    plate = plate.filter(ImageFilter.GaussianBlur(26))
    im.alpha_composite(plate)
    apply_logo(im, logo_a)
    float_z = 1.0 + 0.02 * math.sin((t - 8.0) * 1.8)
    place_kit(im, int(800 * float_z), 580, pop=1.0, alpha=0.98)
    soft_price(im, line_u(t, 8.1, 11.0, 0.22, 0.1), y=1280)
    cta_chip(im, line_u(t, 9.0, 11.0, 0.25, 0.1), t=t)
    return im.convert("RGB")


def write_silent(path: Path, duration: float, sr: int = 44100):
    n = int(sr * duration)
    pcm = array("h", [0] * n)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def main():
    print(f"rendering TikTok beard drip hook v4 {N} frames…")
    for f in FRAMES.glob("*.jpg"):
        f.unlink()
    cover = None
    cover_i = int(0.7 * FPS)
    for i in range(N):
        frame = render_frame(i)
        frame.save(FRAMES / f"f_{i:04d}.jpg", quality=94, subsampling=0)
        if i == cover_i:
            cover = frame.copy()
        if i % 30 == 0:
            print(f"  {i}/{N}")
    if cover is None:
        cover = Image.open(FRAMES / f"f_{cover_i:04d}.jpg")

    wav = ROOT / "audio.wav"
    write_silent(wav, DURATION)

    mp4_name = "MinoxShop-TIKTOK-beard-drip-v4-11s.mp4"
    cover_name = "MinoxShop-TIKTOK-beard-drip-v4-COVER.jpg"
    out_mp4 = EXPORTS / mp4_name
    out_cover = EXPORTS / cover_name
    cover.save(out_cover, quality=95, subsampling=0)
    cover.save(ARTIFACTS / cover_name, quality=95, subsampling=0)

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES / "f_%04d.jpg"),
        "-i", str(wav),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17", "-preset", "fast",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest", "-movflags", "+faststart",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.copy(out_mp4, ARTIFACTS / mp4_name)

    qa = ROOT / "qa"
    qa.mkdir(exist_ok=True)
    for label, sec in [("hole", 0.7), ("drip", 2.7), ("full", 4.5), ("product", 6.6), ("cta", 9.5)]:
        src = FRAMES / f"f_{int(sec * FPS):04d}.jpg"
        shutil.copy(src, qa / f"{label}.jpg")
        shutil.copy(src, ARTIFACTS / f"beard-v4-{label}.jpg")
    print("OK", out_mp4, out_mp4.stat().st_size)


if __name__ == "__main__":
    main()
