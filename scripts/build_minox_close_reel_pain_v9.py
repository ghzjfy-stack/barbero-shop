#!/usr/bin/env python3
"""MinoxShop CLOSE reel v9 — eye contact + CapCut silence.

Same natural Hebrew as v7; portraits stare at camera. Silent audio
for CapCut music overlay.
"""
from __future__ import annotations

import io

import math
import shutil
import subprocess
import wave
from array import array
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/tmp/close-reel-pain-v9")
ASSETS = ROOT / "assets"
FRAMES = ROOT / "frames"
EXPORTS = Path("/agent/repos/barbero-shop/exports")
ARTIFACTS = Path("/opt/cursor/artifacts")
for p in (FRAMES, ASSETS, EXPORTS, ARTIFACTS):
    p.mkdir(parents=True, exist_ok=True)

LIQ = Path("/tmp/ig-ok/liq2048.png")
MIRROR_P = ASSETS / "mirror.jpg"
BEFORE_P = ASSETS / "before.jpg"
AFTER_P = ASSETS / "after.jpg"
LOGO_CANDIDATES = [
    Path("/tmp/minox-brand/main-logo.png"),
    Path("/tmp/two-boxes-v4/assets/main-logo.png"),
]

W, H = 1080, 1920
FPS = 30
DURATION = 10.5
N = int(DURATION * FPS)

INK = (9, 9, 9)
IVORY = (244, 241, 234)
GOLD = (198, 161, 91)
GOLD_SOFT = (228, 210, 162)
MUTED = (163, 158, 147)
CARD = (252, 250, 247)

FONT_HE_B = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Bold.ttf"
FONT_HE_R = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf"
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
    if ch in "?!.·|:;,/\\-+*=#%&@'\"₪$€£()[]{}<>—–":
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
    widths = []
    for chunk, lat in reversed(runs):
        fnt = f_lat if lat else f_he
        tw, th, bb = text_bb(d, chunk, fnt, None if lat else "he")
        widths.append((chunk, lat, fnt, tw, th, bb))
    x = x_left
    a = int(max(0, min(255, alpha)))
    color = (*fill[:3], a)
    for chunk, lat, fnt, tw, th, bb in widths:
        xy = (x - bb[0], y - bb[1])
        if lat:
            d.text(xy, chunk, font=fnt, fill=color)
        else:
            d.text(xy, chunk, font=fnt, fill=color, language="he")
        x += tw
    return sum(w[3] for w in widths)


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
    for p in LOGO_CANDIDATES:
        if p.exists():
            logo = Image.open(p).convert("RGBA")
            a = np.asarray(logo).copy()
            rgb = a[:, :, :3].astype(np.float32)
            mn, mx = rgb.min(2), rgb.max(2)
            bgm = (mn > 195) & ((mx - mn) < 35) & (rgb.mean(2) > 215)
            a[:, :, 3] = np.where(bgm, 0, a[:, :, 3]).astype(np.uint8)
            logo = Image.fromarray(a, "RGBA")
            logo.thumbnail((100, 100), Image.Resampling.LANCZOS)
            return logo
    return None


def prep_product():
    src = Image.open(LIQ).convert("RGBA")
    arr = np.asarray(src)
    rgb = arr[:, :, :3]
    mask = ~((rgb[:, :, 0] > 248) & (rgb[:, :, 1] > 248) & (rgb[:, :, 2] > 248))
    ys, xs = np.where(mask)
    pad = 56
    prod = src.crop(
        (max(0, xs.min() - pad), max(0, ys.min() - pad), min(src.size[0], xs.max() + pad), min(src.size[1], ys.max() + pad))
    )
    solid = Image.new("RGBA", prod.size, (*CARD, 255))
    solid.alpha_composite(prod)
    return ImageEnhance.Contrast(ImageEnhance.Sharpness(solid).enhance(1.4)).enhance(1.06)


def cover_zoom(im: Image.Image, zoom: float, y_bias: float = 0.38) -> Image.Image:
    zoom = max(1.0, zoom)
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


def trim_white_edge(im: Image.Image) -> Image.Image:
    arr = np.asarray(im.convert("RGB"))
    bright = arr.mean(axis=2) > 230
    col = bright.mean(axis=0)
    left = 0
    for i, f in enumerate(col):
        if f < 0.3:
            left = i
            break
    right = arr.shape[1] - 1
    for i in range(arr.shape[1] - 1, -1, -1):
        if col[i] < 0.5:
            right = i
            break
    if right - left < arr.shape[1] * 0.7:
        return im
    return im.crop((left, 0, right + 1, arr.shape[0]))


LOGO = load_logo()
PROD = prep_product()
MIRROR = Image.open(MIRROR_P).convert("RGB")
BEFORE = ImageEnhance.Contrast(Image.open(BEFORE_P).convert("RGB")).enhance(1.06)
AFTER = ImageEnhance.Contrast(ImageEnhance.Brightness(Image.open(AFTER_P).convert("RGB")).enhance(1.04)).enhance(1.08)


def apply_logo(im, alpha: float, y: int = 44):
    if LOGO is None or alpha < 0.05:
        return
    logo = LOGO.copy()
    logo.putalpha(logo.split()[-1].point(lambda a: int(a * alpha)))
    im.alpha_composite(logo, ((W - logo.size[0]) // 2, y))


def bare_caption(im, text, y, size, fill, u):
    if u < 0.04:
        return
    a = int(255 * min(1.0, u * 1.2))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # soft shadow for readability on photo
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_mixed_centered(shadow, text, y + 2, size, (0, 0, 0), int(a * 0.55), True)
    shadow = shadow.filter(ImageFilter.GaussianBlur(4))
    im.alpha_composite(shadow)
    draw_mixed_centered(layer, text, y, size, fill, a, True)
    im.alpha_composite(layer)


def place_product(im, max_w: int, y_center: int, pop: float, alpha: float = 1.0):
    if pop < 0.02 or alpha < 0.02:
        return
    p = PROD.copy()
    inner = max_w - 48
    p.thumbnail((inner, int(inner * 0.95)), Image.Resampling.LANCZOS)
    scale = 0.90 + 0.10 * ease_out_back(min(1.0, pop))
    pw = max(1, int(p.size[0] * scale))
    ph = max(1, int(p.size[1] * scale))
    pp = p.resize((pw, ph), Image.Resampling.LANCZOS)
    card_w = min(W - 80, pw + 56)
    card_h = ph + 48
    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    aa = pop * alpha
    cd.rounded_rectangle([0, 0, card_w - 1, card_h - 1], 22, fill=(*CARD, int(255 * aa)))
    cd.rounded_rectangle([1, 1, card_w - 2, card_h - 2], 21, outline=(*GOLD, int(45 * aa)), width=1)
    card.alpha_composite(pp, ((card_w - pw) // 2, (card_h - ph) // 2))
    bw, bh = 92, 44
    badge = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.rounded_rectangle([0, 0, bw - 1, bh - 1], 10, fill=(9, 9, 9, int(240 * aa)), outline=(*GOLD, int(220 * aa)), width=2)
    bf = font(22, True, False)
    bb = bd.textbbox((0, 0), "x2", font=bf)
    bd.text(((bw - (bb[2] - bb[0])) // 2 - bb[0], (bh - (bb[3] - bb[1])) // 2 - bb[1] - 1), "x2", font=bf, fill=(*GOLD, int(255 * aa)))
    card.alpha_composite(badge, (16, 14))
    px = (W - card_w) // 2
    py = int(y_center - card_h / 2)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.ellipse([px + 40, py + card_h - 12, px + card_w - 40, py + card_h + 28], fill=(0, 0, 0, int(80 * aa)))
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    im.alpha_composite(sh)
    im.alpha_composite(card, (px, py))


def price_block(im, u: float, strike_u: float = 1.0):
    if u < 0.05:
        return
    a = int(255 * min(1.0, u * 1.2))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_mixed_centered(layer, "₪1050", 1180, 34, MUTED, int(a * 0.85), True)
    d = ImageDraw.Draw(layer)
    tw, _ = measure_mixed(d, "₪1050", 34, True)
    x0 = (W - tw) // 2
    sw = max(0.0, min(1.0, strike_u))
    d.line([(x0, 1198), (x0 + int(tw * sw), 1198)], fill=(*MUTED, a), width=3)
    pop = 0.88 + 0.12 * ease_out_back(min(1.0, u))
    draw_mixed_centered(layer, "₪765", 1240, int(92 * pop), GOLD, a, True)
    draw_mixed_centered(layer, "רק ₪64 לחודש", 1360, 34, IVORY, a, True)
    im.alpha_composite(layer)


def cta_block(im, u: float, t: float = 0.0):
    if u < 0.05:
        return
    a = int(255 * min(1.0, u * 1.2))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bw, bh = 780, 96
    y0 = 1480
    pulse = 1.0 + 0.03 * (0.5 + 0.5 * math.sin((t - 7.6) * 2 * math.pi / 0.9))
    enter = 0.94 + 0.06 * ease_out_back(min(1.0, u))
    scale = enter * pulse
    bw2, bh2 = int(bw * scale), int(bh * scale)
    x0 = (W - bw2) // 2
    y0p = y0 - (bh2 - bh) // 2
    d.rounded_rectangle([x0, y0p, x0 + bw2, y0p + bh2], 22, fill=(*GOLD, a))
    draw_mixed_centered(layer, "הזמנה בוואטסאפ", y0p + 22, 40, INK, a, True)
    draw_mixed_centered(layer, "הקישור בפרופיל", y0p + bh2 + 28, 30, GOLD_SOFT, a, True)
    im.alpha_composite(layer)


def vignette(im: Image.Image, strength: float = 0.45):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cy, cx = H * 0.42, W * 0.5
    r = np.sqrt(((xx - cx) / (W * 0.62)) ** 2 + ((yy - cy) / (H * 0.55)) ** 2)
    dark = np.clip((r - 0.55) / 0.85, 0, 1) ** 1.4 * strength
    arr = np.asarray(im.convert("RGBA")).astype(np.float32)
    arr[:, :, :3] *= (1 - dark)[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def render_frame(i: int) -> Image.Image:
    t = i / FPS
    im = bg(t)
    logo_a = min(1.0, t / 0.35) if t < DURATION - 0.25 else max(0.0, (DURATION - t) / 0.25)

    # --- A: mirror concern 0–2.6 (clear human) ---
    if t < 2.65:
        z = 1.02 + 0.10 * ease_in_out(min(1.0, t / 2.5))
        photo = cover_zoom(MIRROR, z, y_bias=0.42)  # face + eyes to camera
        photo = ImageEnhance.Contrast(photo).enhance(1.05)
        layer = vignette(photo.convert("RGBA"), 0.38)
        fa = ease_out(min(1.0, t / 0.28))
        if fa < 0.99:
            layer.putalpha(layer.split()[-1].point(lambda a: int(a * fa)))
        im.alpha_composite(layer)
        apply_logo(im, logo_a * 0.9)
        u1 = line_u(t, 0.3, 2.55, 0.28, 0.25)
        if u1 > 0:
            bare_caption(im, "רואה איך זה מדלדל?", 1460, 48, IVORY, u1)
        return im.convert("RGB")

    # --- B: before then after (full-frame — clear faces) ---
    if t < 5.40:
        use_after = t >= 3.85
        if 3.75 <= t < 4.05:
            u = ease_in_out((t - 3.75) / 0.30)
            b = vignette(cover_zoom(BEFORE, 1.08, 0.42).convert("RGBA"), 0.36)
            a = vignette(cover_zoom(AFTER, 1.06, 0.45).convert("RGBA"), 0.28)
            a = ImageEnhance.Brightness(a).enhance(1.06)
            a.putalpha(a.split()[-1].point(lambda x: int(255 * u)))
            layer = b
            layer.alpha_composite(a)
        else:
            src = AFTER if use_after else BEFORE
            z = 1.04 + 0.06 * ease_in_out(min(1.0, (t - (3.85 if use_after else 2.55)) / 1.3))
            photo = cover_zoom(src, z, y_bias=0.45 if use_after else 0.42)
            if use_after:
                photo = ImageEnhance.Brightness(photo).enhance(1.06)
                photo = ImageEnhance.Contrast(photo).enhance(1.08)
            layer = vignette(photo.convert("RGBA"), 0.28 if use_after else 0.36)
        im.alpha_composite(layer)
        apply_logo(im, logo_a)
        if not use_after:
            bare_caption(im, "לפני", 200, 30, MUTED, line_u(t, 2.6, 3.85, 0.2, 0.2))
            bare_caption(im, "עוד שנה ככה ותהיה קרח", 1460, 44, IVORY, line_u(t, 2.7, 3.85, 0.25, 0.22))
        else:
            bare_caption(im, "אחרי", 200, 30, GOLD, line_u(t, 3.9, 5.3, 0.2, 0.2))
            bare_caption(im, "יש דרך לעצור את זה", 1460, 48, IVORY, line_u(t, 4.0, 5.3, 0.25, 0.22))
        return im.convert("RGB")

    # --- C: offer product 5.35–7.55 ---
    apply_logo(im, logo_a)
    if 5.35 <= t < 7.55:
        u_prod = line_u(t, 5.35, 7.55, 0.3, 0.22)
        place_product(im, 860, 480, pop=u_prod, alpha=1.0)
        bare_caption(im, "קירקלנד מינוקסידיל 5%", 1025, 32, GOLD_SOFT, u_prod)
        bare_caption(im, "מארז כפול לשנה שלמה", 1085, 38, IVORY, u_prod)
        strike = ease_out(min(1.0, max(0.0, (t - 5.7) / 0.3)))
        price_block(im, u_prod, strike_u=strike)
        return im.convert("RGB")

    # --- D: WA 7.55–10.5 ---
    apply_logo(im, logo_a)
    u_cta = line_u(t, 7.55, 10.5, 0.28, 0.12)
    place_product(im, 560, 450, pop=1.0, alpha=0.95)
    price_block(im, 0.95, strike_u=1.0)
    cta_block(im, u_cta, t=t)
    u_line = line_u(t, 8.1, 10.4, 0.25, 0.15)
    if u_line > 0:
        bare_caption(im, "כתוב בוואטסאפ ונסגור היום", 1680, 32, GOLD_SOFT, u_line)

    return im.convert("RGB")


def write_soft_audio(path: Path, duration: float, sr: int = 44100):
    """Silent track for CapCut music overlay."""
    n = int(sr * duration)
    pcm = array("h", [0] * n)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def main():
    print(f"rendering pain-hook v9 {N} frames…")
    for f in FRAMES.glob("*.jpg"):
        f.unlink()
    cover = None
    for i in range(N):
        frame = render_frame(i)
        frame.save(FRAMES / f"f_{i:04d}.jpg", quality=93, subsampling=0)
        if i == int(1.2 * FPS):
            cover = frame.copy()
        if i % 30 == 0:
            print(f"  {i}/{N}")
    if cover is None:
        cover = Image.open(FRAMES / "f_0036.jpg")

    wav = ROOT / "audio.wav"
    write_soft_audio(wav, DURATION)

    mp4_name = "MinoxShop-CLOSE-pain-v9-10s.mp4"
    cover_name = "MinoxShop-CLOSE-pain-v9-COVER.jpg"
    out_mp4 = EXPORTS / mp4_name
    out_cover = EXPORTS / cover_name
    cover.save(out_cover, quality=95, subsampling=0)
    cover.save(ARTIFACTS / cover_name, quality=95, subsampling=0)

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES / "f_%04d.jpg"),
        "-i", str(wav),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        str(out_mp4),
    ]
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.copy2(out_mp4, ARTIFACTS / mp4_name)
    # also overwrite main pain export name for continuity
    shutil.copy2(out_mp4, EXPORTS / "MinoxShop-CLOSE-pain-double-765-10s.mp4")
    shutil.copy2(out_cover, EXPORTS / "MinoxShop-CLOSE-pain-double-765-COVER.jpg")
    print("OK", out_mp4, out_mp4.stat().st_size)


if __name__ == "__main__":
    main()
