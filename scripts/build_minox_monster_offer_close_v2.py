#!/usr/bin/env python3
"""MinoxShop MONSTER offer-close reel v2 — real product + spoken Hebrew.

~11s 9:16. Silent audio for CapCut music.
Short spoken hook → REAL packshot → ₪765 → WhatsApp.
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

ROOT = Path("/tmp/monster-trust-v2")
ASSETS = ROOT / "assets"
FRAMES = ROOT / "frames"
EXPORTS = Path("/agent/repos/barbero-shop/exports")
ARTIFACTS = Path("/opt/cursor/artifacts")
for p in (FRAMES, ASSETS, EXPORTS, ARTIFACTS):
    p.mkdir(parents=True, exist_ok=True)

LIQ = Path("/tmp/ig-ok/liq2048.png")
HERO_P = ASSETS / "feed.jpg"
PROD_P = ASSETS / "prod.png"
BG_P = ASSETS / "bg.jpg"
AFTER_P = ASSETS / "after.jpg"
LOGO_CANDIDATES = [
    Path("/tmp/minox-brand/main-logo.png"),
    Path("/tmp/two-boxes-v4/assets/main-logo.png"),
]

W, H = 1080, 1920
FPS = 30
DURATION = 11.0
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
    for chunk, lat in reversed(runs):
        fnt = f_lat if lat else f_he
        tw, th, bb = text_bb(d, chunk, fnt, None if lat else "he")
        color = (*fill, alpha) if len(fill) == 3 else fill
        xy = (x - bb[0], y - bb[1])
        if lat:
            d.text(xy, chunk, font=fnt, fill=color)
        else:
            d.text(xy, chunk, font=fnt, fill=color, language="he")
        x += tw


def draw_mixed_centered(layer, text: str, y: int, size: int, fill, alpha: int = 255, bold: bool = True):
    d = ImageDraw.Draw(layer)
    tw, _ = measure_mixed(d, text, size, bold)
    draw_mixed_at(layer, text, (W - tw) // 2, y, size, fill, alpha, bold)


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def cover_zoom(im: Image.Image, zoom: float, y_bias: float = 0.38) -> Image.Image:
    z = max(1.0, zoom)
    w, h = im.size
    base_w, base_h = W, H
    scale = max(base_w / w, base_h / h) * z
    nw, nh = int(w * scale), int(h * scale)
    resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x0 = (nw - base_w) // 2
    y0 = max(0, min(nh - base_h, int((nh - base_h) * y_bias)))
    return resized.crop((x0, y0, x0 + base_w, y0 + base_h))


def load_logo() -> Image.Image | None:
    for p in LOGO_CANDIDATES:
        if p.exists():
            logo = load_rgba(p)
            logo.thumbnail((280, 120), Image.Resampling.LANCZOS)
            return logo
    return None


LOGO = load_logo()
PROD = load_rgba(PROD_P) if PROD_P.exists() else (load_rgba(LIQ) if LIQ.exists() else None)
HERO = load_rgba(HERO_P) if HERO_P.exists() else None
BG = load_rgba(BG_P) if BG_P.exists() else None
AFTER = load_rgba(AFTER_P) if AFTER_P.exists() else None


def bg_dark(t: float) -> Image.Image:
    im = Image.new("RGBA", (W, H), (8, 9, 12, 255))
    # clean dark stage — no AI atmosphere plate
    # vignette
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H * 0.45) / (H * 0.6)) ** 2)
    dark = np.clip((r - 0.35) / 0.9, 0, 1) ** 1.3 * 0.55
    arr = np.asarray(im).astype(np.float32)
    arr[:, :, :3] *= (1 - dark)[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def apply_logo(im: Image.Image, alpha: float, y: int = 70):
    if LOGO is None or alpha < 0.04:
        return
    logo = LOGO.copy()
    logo.putalpha(logo.split()[-1].point(lambda a: int(a * alpha)))
    im.alpha_composite(logo, ((W - logo.size[0]) // 2, y))


def bare_caption(im, text, y, size, fill, u):
    if u < 0.04:
        return
    a = int(255 * min(1.0, u * 1.2))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_mixed_centered(shadow, text, y + 2, size, (0, 0, 0), int(a * 0.55), True)
    shadow = shadow.filter(ImageFilter.GaussianBlur(4))
    im.alpha_composite(shadow)
    draw_mixed_centered(layer, text, y, size, fill, a, True)
    im.alpha_composite(layer)


def place_product(im, max_w: int, y_center: int, pop: float, alpha: float = 1.0, src: Image.Image | None = None):
    if pop < 0.02 or alpha < 0.02:
        return
    src = src or PROD
    if src is None:
        return
    p = src.copy()
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
    cd.rounded_rectangle([1, 1, card_w - 2, card_h - 2], 21, outline=(*GOLD, int(50 * aa)), width=1)
    card.alpha_composite(pp, ((card_w - pw) // 2, (card_h - ph) // 2))
    bw, bh = 92, 44
    badge = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.rounded_rectangle([0, 0, bw - 1, bh - 1], 10, fill=(9, 9, 9, int(240 * aa)), outline=(*GOLD, int(220 * aa)), width=2)
    bf = font(22, True, False)
    bb = bd.textbbox((0, 0), "x2", font=bf)
    bd.text(
        ((bw - (bb[2] - bb[0])) // 2 - bb[0], (bh - (bb[3] - bb[1])) // 2 - bb[1] - 1),
        "x2",
        font=bf,
        fill=(*GOLD, int(255 * aa)),
    )
    card.alpha_composite(badge, (16, 14))
    px = (W - card_w) // 2
    py = int(y_center - card_h / 2)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.ellipse([px + 40, py + card_h - 12, px + card_w - 40, py + card_h + 28], fill=(0, 0, 0, int(90 * aa)))
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    im.alpha_composite(sh)
    im.alpha_composite(card, (px, py))


def price_block(im, u: float, strike_u: float = 1.0):
    if u < 0.05:
        return
    a = int(255 * min(1.0, u * 1.2))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_mixed_centered(layer, "₪1050", 1220, 34, MUTED, int(a * 0.85), True)
    d = ImageDraw.Draw(layer)
    tw, _ = measure_mixed(d, "₪1050", 34, True)
    x0 = (W - tw) // 2
    sw = max(0.0, min(1.0, strike_u))
    d.line([(x0, 1238), (x0 + int(tw * sw), 1238)], fill=(*MUTED, a), width=3)
    pop = 0.88 + 0.12 * ease_out_back(min(1.0, u))
    draw_mixed_centered(layer, "₪765", 1280, int(96 * pop), GOLD, a, True)
    draw_mixed_centered(layer, "רק ₪64 לחודש", 1405, 36, IVORY, a, True)
    im.alpha_composite(layer)


def cta_block(im, u: float, t: float = 0.0):
    if u < 0.05:
        return
    a = int(255 * min(1.0, u * 1.2))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bw, bh = 780, 96
    y0 = 1480
    pulse = 1.0 + 0.03 * (0.5 + 0.5 * math.sin((t - 8.0) * 2 * math.pi / 0.9))
    enter = 0.94 + 0.06 * ease_out_back(min(1.0, u))
    scale = enter * pulse
    bw2, bh2 = int(bw * scale), int(bh * scale)
    x0 = (W - bw2) // 2
    y0p = y0 - (bh2 - bh) // 2
    d.rounded_rectangle([x0, y0p, x0 + bw2, y0p + bh2], 22, fill=(*GOLD, a))
    draw_mixed_centered(layer, "הזמנה בוואטסאפ", y0p + 22, 40, INK, a, True)
    draw_mixed_centered(layer, "הקישור בפרופיל", y0p + bh2 + 28, 30, GOLD_SOFT, a, True)
    im.alpha_composite(layer)


def render_frame(i: int) -> Image.Image:
    t = i / FPS
    im = bg_dark(t)
    logo_a = min(1.0, t / 0.3) if t < DURATION - 0.2 else max(0.0, (DURATION - t) / 0.2)

    # A: spoken hook 0–2.2
    if t < 2.25:
        apply_logo(im, logo_a * 0.95)
        bare_caption(im, "שנה של מינוקס", 860, 52, IVORY, line_u(t, 0.2, 2.15, 0.28, 0.2))
        bare_caption(im, "בלי סיבוכים", 970, 46, GOLD_SOFT, line_u(t, 0.75, 2.15, 0.28, 0.2))
        return im.convert("RGB")

    # B: real product + offer 2.2–7.6
    apply_logo(im, logo_a)
    if 2.2 <= t < 7.65:
        u_prod = line_u(t, 2.2, 7.6, 0.28, 0.2)
        # Prefer real PNG packshot (liq) with x2 card — not AI hero
        place_product(im, 980, 500, pop=u_prod, alpha=1.0, src=PROD)
        bare_caption(im, "קירקלנד מינוקסידיל 5%", 1000, 32, GOLD_SOFT, u_prod)
        bare_caption(im, "מארז כפול לשנה שלמה", 1060, 38, IVORY, u_prod)
        bare_caption(im, "מקורי מארה״ב", 1125, 30, MUTED, u_prod)
        strike = ease_out(min(1.0, max(0.0, (t - 2.7) / 0.28)))
        price_block(im, u_prod, strike_u=strike)
        return im.convert("RGB")

    # C: CTA 7.65–11
    apply_logo(im, logo_a)
    u_cta = line_u(t, 7.65, 11.0, 0.28, 0.12)
    place_product(im, 620, 480, pop=1.0, alpha=0.95, src=PROD)
    price_block(im, 0.95, strike_u=1.0)
    cta_block(im, u_cta, t=t)
    bare_caption(im, "סוגרים בוואטסאפ", 1680, 34, GOLD_SOFT, line_u(t, 8.2, 10.9, 0.25, 0.15))
    return im.convert("RGB")


def write_silent_audio(path: Path, duration: float, sr: int = 44100):
    n = int(sr * duration)
    pcm = array("h", [0] * n)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def main():
    print(f"rendering monster offer-close v2 {N} frames…")
    for f in FRAMES.glob("*.jpg"):
        f.unlink()
    cover = None
    for i in range(N):
        frame = render_frame(i)
        frame.save(FRAMES / f"f_{i:04d}.jpg", quality=93, subsampling=0)
        if i == int(0.9 * FPS):
            cover = frame.copy()
        if i % 30 == 0:
            print(f"  {i}/{N}")
    if cover is None:
        cover = Image.open(FRAMES / "f_0030.jpg")

    wav = ROOT / "audio.wav"
    write_silent_audio(wav, DURATION)

    mp4_name = "MinoxShop-MONSTER-offer-close-v2-11s.mp4"
    cover_name = "MinoxShop-MONSTER-offer-close-v2-COVER.jpg"
    out_mp4 = EXPORTS / mp4_name
    out_cover = EXPORTS / cover_name
    cover.save(out_cover, quality=94, subsampling=0)
    cover.save(ARTIFACTS / cover_name, quality=94, subsampling=0)

    pattern = str(FRAMES / "f_%04d.jpg")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", pattern,
        "-i", str(wav),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest", "-movflags", "+faststart",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.copy(out_mp4, ARTIFACTS / mp4_name)
    print("OK", out_mp4, out_mp4.stat().st_size)


if __name__ == "__main__":
    main()
