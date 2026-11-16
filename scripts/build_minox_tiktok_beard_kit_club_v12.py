#!/usr/bin/env python3
"""MinoxShop TikTok beard kit-club v12 — club copy aligned to foam/scrubber canon.

CTA whisper matches existing brand language (two soft lines under ₪765):
«עשרה אחוז נקודות בונוס»
«בנוסף לנקודות על כל קנייה»
CapCut-silent.
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

ROOT = Path("/tmp/beard-reel-v12")
ASSETS = ROOT / "assets"
FRAMES = ROOT / "frames"
EXPORTS = Path("/agent/repos/barbero-shop/exports")
ARTIFACTS = Path("/opt/cursor/artifacts")
for p in (FRAMES, ASSETS, EXPORTS, ARTIFACTS):
    p.mkdir(parents=True, exist_ok=True)

REPO_ASSETS = Path("/agent/repos/barbero-shop/exports/tiktok-beard-v10-assets")
FALLBACK_ASSETS = Path("/agent/repos/barbero-shop/exports/tiktok-beard-v9-assets")


def _asset(name: str) -> Path:
    for base in (ASSETS, REPO_ASSETS, FALLBACK_ASSETS):
        p = base / name
        if p.exists():
            return p
    return REPO_ASSETS / name


BEFORE_P = _asset("before.jpg")
THIN_P = _asset("thin.jpg")
DROP_P = _asset("drop.jpg")
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
GOLD_HI = (236, 214, 158)
GOLD_LO = (148, 118, 58)

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


def cover_zoom(im: Image.Image, zoom: float, y_bias: float = 0.38) -> Image.Image:
    zoom = max(1.0, min(1.14, zoom))
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
    # micro pop on caption entry
    y_off = int((1.0 - min(1.0, u * 1.4)) * 18)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_mixed_centered(shadow, text, y + 3 + y_off, size, (0, 0, 0), int(a * 0.7), True)
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    im.alpha_composite(shadow)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_mixed_centered(layer, text, y + y_off, size, fill, a, True)
    im.alpha_composite(layer)


def apply_logo(im: Image.Image, alpha: float):
    if LOGO is None or alpha < 0.04:
        return
    logo = LOGO.copy()
    logo.putalpha(logo.split()[-1].point(lambda a: int(a * alpha)))
    im.alpha_composite(logo, ((W - logo.size[0]) // 2, 48))


def gold_backlight(im, cx: int, cy: int, rx: int, ry: int, strength: float):
    if strength < 0.04:
        return
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - cx) / max(1, rx)) ** 2 + ((yy - cy) / max(1, ry)) ** 2)
    glow = np.clip(1 - r, 0, 1) ** 2 * strength
    layer = np.zeros((H, W, 4), np.float32)
    layer[:, :, 0] = GOLD[0] * glow
    layer[:, :, 1] = GOLD[1] * glow
    layer[:, :, 2] = GOLD[2] * glow
    layer[:, :, 3] = 255 * glow * 0.48
    im.alpha_composite(Image.fromarray(np.clip(layer, 0, 255).astype(np.uint8), "RGBA"))


def specular_sweep(im, px, py, pw, ph, t_local: float):
    """Soft narrow sheen — no thick CapCut streak."""
    u = max(0.0, min(1.0, t_local))
    if u < 0.04 or u > 0.96:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x = int(px + pw * u)
    a = int(78 * math.sin(math.pi * u))
    # thin angled ribbon only
    d.polygon(
        [(x - 8, py + 40), (x + 6, py + 40), (x + 18, py + ph - 60), (x + 2, py + ph - 60)],
        fill=(255, 240, 200, a),
    )
    d.polygon(
        [(x - 2, py + 55), (x + 3, py + 55), (x + 8, py + ph - 80), (x + 3, py + ph - 80)],
        fill=(255, 252, 245, int(a * 0.55)),
    )
    im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(4)))


def wink_sparkle(im, x, y, phase, scale=1.0):
    """Tiny premium glint — not scattered glitter."""
    if phase < 0 or phase > 1:
        return
    a = int(190 * math.sin(math.pi * phase))
    if a < 18:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    s = int(10 * scale * (0.75 + 0.25 * math.sin(math.pi * phase)))
    d.polygon([(x, y - s), (x + 2, y), (x, y + s), (x - 2, y)], fill=(255, 236, 190, a))
    d.polygon([(x - s, y), (x, y + 2), (x + s, y), (x, y - 2)], fill=(255, 248, 220, a))
    im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.8)))


def place_kit(
    im,
    max_w: int,
    y_center: int,
    pop: float,
    alpha: float = 1.0,
    specular_t: float | None = None,
    sparkle: bool = False,
    t: float = 0.0,
):
    if KIT is None or pop < 0.02 or alpha < 0.02:
        return
    p = KIT.copy()
    # punchier scale entrance — keep pharma faces smooth (no Unsharp fry)
    target = int(max_w * (0.82 + 0.18 * ease_out_back(min(1.0, pop))))
    p.thumbnail((target, target), Image.Resampling.LANCZOS)
    p = ImageEnhance.Contrast(p).enhance(1.02)
    p = ImageEnhance.Color(p).enhance(1.03)
    p = ImageEnhance.Brightness(p).enhance(1.01)
    if alpha < 0.99:
        p.putalpha(p.split()[-1].point(lambda a: int(a * alpha)))
    pw, ph = p.size
    px = (W - pw) // 2
    rise = int((1.0 - min(1.0, pop)) * 70)
    py = int(y_center - ph / 2) + rise
    gold_backlight(im, W // 2, py + ph // 2, int(pw * 0.55), int(ph * 0.48), strength=0.14 * pop * alpha)
    # soft contact shadow under kit (overlaps bottom edge slightly to hide micro-AA)
    if pop > 0.35:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        sx0, sy0 = px + int(pw * 0.12), py + ph - 22
        sx1, sy1 = px + int(pw * 0.88), py + ph + 26
        sd.ellipse([sx0, sy0, sx1, sy1], fill=(0, 0, 0, int(72 * pop * alpha)))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    im.alpha_composite(p, (px, py))
    # thin soft under-edge veil
    if pop > 0.5:
        veil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        vd = ImageDraw.Draw(veil)
        vd.rectangle([px + 8, py + ph - 3, px + pw - 8, py + ph + 1], fill=(0, 0, 0, int(90 * alpha)))
        im.alpha_composite(veil.filter(ImageFilter.GaussianBlur(2)))
    if specular_t is not None:
        specular_sweep(im, px, py, pw, ph, specular_t)
    if sparkle and pop > 0.7:
        # single soft silver-bar glint only (panel: kill diamond field)
        phase1 = ((t - 6.85) % 2.1) / 0.45
        if 0 <= phase1 <= 1:
            wink_sparkle(im, px + int(pw * 0.34), py + int(ph * 0.13), phase1, scale=0.55)


def soft_price(im, u: float, y: int = 1280):
    if u < 0.05:
        return
    a = int(255 * min(1.0, u * 1.2))
    y_off = int((1.0 - min(1.0, u * 1.35)) * 14)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_mixed_centered(layer, "₪765 לשנה שלמה", y + y_off, 44, GOLD, a, True)
    im.alpha_composite(layer)


def club_whisper(im, u: float, y: int = 1345):
    """Two-line club canon (foam/scrubber): bonus ON TOP of regular points."""
    if u < 0.05:
        return
    a1 = int(200 * min(1.0, u * 1.12))
    a2 = int(165 * min(1.0, u * 1.05))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_mixed_centered(layer, "עשרה אחוז נקודות בונוס", y, 28, GOLD_SOFT, a1, True)
    draw_mixed_centered(layer, "בנוסף לנקודות על כל קנייה", y + 42, 24, (210, 200, 178), a2, True)
    im.alpha_composite(layer)


def cta_chip(im, u: float, t: float = 0.0):
    """Premium gold CTA: drop shadow + vertical gradient + rim highlight."""
    if u < 0.05:
        return
    a = int(255 * min(1.0, u * 1.2))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bw, bh = 700, 88
    y0 = 1545
    pulse = 1.0 + 0.018 * (0.5 + 0.5 * math.sin((t - 9.35) * 2 * math.pi / 0.95))
    enter = 0.92 + 0.08 * ease_out_back(min(1.0, u))
    scale = enter * pulse
    bw2, bh2 = int(bw * scale), int(bh * scale)
    x0 = (W - bw2) // 2
    y0p = y0 - (bh2 - bh) // 2

    # drop shadow
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle(
        [x0 + 4, y0p + 8, x0 + bw2 + 4, y0p + bh2 + 10],
        22,
        fill=(0, 0, 0, int(a * 0.45)),
    )
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))

    # gradient body
    btn = Image.new("RGBA", (bw2, bh2), (0, 0, 0, 0))
    bd = ImageDraw.Draw(btn)
    for row in range(bh2):
        k = row / max(1, bh2 - 1)
        r = int(GOLD_HI[0] * (1 - k) + GOLD_LO[0] * k)
        g = int(GOLD_HI[1] * (1 - k) + GOLD_LO[1] * k)
        b = int(GOLD_HI[2] * (1 - k) + GOLD_LO[2] * k)
        bd.line([(0, row), (bw2, row)], fill=(r, g, b, a))
    mask = Image.new("L", (bw2, bh2), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, bw2 - 1, bh2 - 1], 22, fill=255)
    btn.putalpha(Image.composite(btn.split()[-1], Image.new("L", (bw2, bh2), 0), mask))
    layer.alpha_composite(btn, (x0, y0p))

    # bright rim
    rim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim)
    rd.rounded_rectangle(
        [x0, y0p, x0 + bw2 - 1, y0p + bh2 - 1],
        22,
        outline=(255, 236, 190, int(a * 0.55)),
        width=2,
    )
    rd.rounded_rectangle(
        [x0 + 2, y0p + 2, x0 + bw2 - 3, y0p + bh2 // 2],
        18,
        outline=(255, 250, 230, int(a * 0.28)),
        width=1,
    )
    layer.alpha_composite(rim)
    draw_mixed_centered(layer, "וואטסאפ בביו", y0p + 24, 34, INK, a, True)
    im.alpha_composite(layer)


LOGO = load_logo()
BEFORE = Image.open(BEFORE_P).convert("RGB")
THIN = Image.open(THIN_P).convert("RGB")
DROP = Image.open(DROP_P).convert("RGB")
FULL = Image.open(FULL_P).convert("RGB")
KIT = Image.open(KIT_P).convert("RGBA") if KIT_P.exists() else None


def face_plate(src: Image.Image, zoom: float, y_bias: float, vig: float, bright: float = 1.0, contrast: float = 1.0, sharp: float = 1.12):
    photo = cover_zoom(src, zoom, y_bias=y_bias)
    photo = ImageEnhance.Sharpness(photo).enhance(sharp)
    if bright != 1.0:
        photo = ImageEnhance.Brightness(photo).enhance(bright)
    if contrast != 1.0:
        photo = ImageEnhance.Contrast(photo).enhance(contrast)
    photo = ImageEnhance.Color(photo).enhance(1.05)
    return vignette(photo.convert("RGBA"), vig)


def blend_face(im, layer: Image.Image, alpha: float):
    if alpha < 0.02:
        return
    if alpha < 0.99:
        layer = layer.copy()
        layer.putalpha(layer.split()[-1].point(lambda a: int(a * alpha)))
    im.alpha_composite(layer)


def render_frame(i: int) -> Image.Image:
    t = i / FPS
    im = bg(t)
    logo_a = min(1.0, t / 0.35) if t < DURATION - 0.2 else max(0.0, (DURATION - t) / 0.2)

    # A 0–2.0 BEFORE — soft dissolve into drop near end
    if t < 2.05:
        z = 1.04 + 0.05 * ease_in_out(min(1.0, t / 1.9))
        layer = face_plate(BEFORE, z, y_bias=0.34, vig=0.24, contrast=1.06, sharp=1.14)
        fa = ease_out(min(1.0, t / 0.22))
        blend_face(im, layer, fa)
        # dissolve prep into drop
        if t >= 1.85:
            mix = ease_in_out((t - 1.85) / 0.2)
            drop = face_plate(DROP, 1.05, y_bias=0.46, vig=0.26, contrast=1.08, sharp=1.18)
            blend_face(im, drop, mix)
        apply_logo(im, logo_a * 0.85)
        bare_caption(im, "יש לי חור בזקן", 1480, 50, IVORY, line_u(t, 0.25, 1.95, 0.25, 0.2))
        return im.convert("RGB")

    # B 2.0–3.9 dropper — dissolve into after
    if t < 3.95:
        z = 1.05 + 0.06 * ease_in_out(min(1.0, (t - 2.0) / 1.8))
        layer = face_plate(DROP, z, y_bias=0.46, vig=0.26, contrast=1.08, sharp=1.18)
        blend_face(im, layer, 1.0)
        if t >= 3.70:
            mix = ease_in_out((t - 3.70) / 0.25)
            after = face_plate(FULL, 1.02, y_bias=0.34, vig=0.20, bright=1.03, contrast=1.06, sharp=1.12)
            blend_face(im, after, mix)
        apply_logo(im, logo_a)
        bare_caption(im, "טיפה על החור", 1480, 48, IVORY, line_u(t, 2.15, 3.8, 0.22, 0.2))
        return im.convert("RGB")

    # C 3.9–6.5 AFTER — dissolve into product bg
    if t < 6.55:
        z = 1.02 + 0.04 * ease_in_out(min(1.0, (t - 3.90) / 2.4))
        layer = face_plate(FULL, z, y_bias=0.34, vig=0.20, bright=1.03, contrast=1.06, sharp=1.12)
        face_a = 1.0
        if t >= 6.25:
            face_a = 1.0 - ease_in_out((t - 6.25) / 0.3)
        blend_face(im, layer, face_a)
        apply_logo(im, logo_a)
        bare_caption(im, "אחרי כמה חודשים", 1480, 48, GOLD_SOFT, line_u(t, 4.05, 6.35, 0.22, 0.22))
        # early product ghost rise
        if t >= 6.25:
            pu = ease_out((t - 6.25) / 0.3)
            place_kit(im, 980, 640, pop=pu * 0.55, alpha=pu * 0.7, specular_t=None, sparkle=False, t=t)
        return im.convert("RGB")

    # D 6.5–8.55 glossy product — punchy entrance + restrained shine
    # Crossfade into CTA layout from 8.25 so no black pop
    if t < 8.55:
        apply_logo(im, logo_a)
        u = line_u(t, 6.5, 8.45, 0.32, 0.2)
        float_z = 1.0 + 0.025 * math.sin((t - 6.5) * 2.1)
        local = max(0.0, min(1.0, (t - 6.55) / 1.45))
        spec = local if local < 0.95 else None
        if t >= 7.55:
            spec = max(0.0, min(1.0, (t - 7.55) / 0.85))
        # morph size/pos toward CTA kit — captions out fully before price in
        morph = ease_in_out(max(0.0, min(1.0, (t - 8.10) / 0.45))) if t >= 8.10 else 0.0
        max_w = int((1040 * float_z) * (1 - morph) + (980 * float_z) * morph)
        y_c = int((620 - 8 * math.sin((t - 6.5) * 1.5)) * (1 - morph) + 560 * morph)
        place_kit(
            im,
            max_w,
            y_c,
            pop=max(u, morph),
            alpha=1.0,
            specular_t=spec if morph < 0.5 else 0.40,
            sparkle=(morph < 0.35),
            t=t,
        )
        # product copy gone by morph~0.55; price starts only after that
        cap_fade = max(0.0, 1.0 - morph / 0.55)
        bare_caption(im, "מארז כפול מקורי", 1385, 40, GOLD_SOFT, line_u(t, 6.65, 8.2, 0.25, 0.18) * cap_fade)
        bare_caption(im, "קירקלנד גם לזקן", 1470, 46, IVORY, u * cap_fade)
        bare_caption(im, "לא רק לראש", 1560, 40, GOLD_SOFT, line_u(t, 7.1, 8.2, 0.25, 0.18) * cap_fade)
        price_in = max(0.0, (morph - 0.55) / 0.45)
        if price_in > 0.04:
            soft_price(im, price_in, y=1265)
        return im.convert("RGB")

    # E 8.55–11: larger kit → price / two-line club / CTA
    apply_logo(im, logo_a)
    float_z = 1.0 + 0.012 * math.sin((t - 8.55) * 1.7)
    place_kit(
        im,
        int(980 * float_z),
        540,
        pop=1.0,
        alpha=0.99,
        specular_t=0.40 + 0.04 * math.sin((t - 8.55) * 1.4),
        sparkle=False,
        t=t,
    )
    soft_price(im, line_u(t, 8.55, 11.0, 0.15, 0.1), y=1265)
    club_whisper(im, line_u(t, 8.85, 11.0, 0.22, 0.1), y=1345)
    cta_chip(im, line_u(t, 9.25, 11.0, 0.28, 0.1), t=t)
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
    print(f"rendering TikTok beard kit-club v12 {N} frames…")
    for f in FRAMES.glob("*.jpg"):
        f.unlink()
    cover = None
    cover_i = int(7.2 * FPS)
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

    mp4_name = "MinoxShop-TIKTOK-beard-kit-club-v12-11s.mp4"
    cover_name = "MinoxShop-TIKTOK-beard-kit-club-v12-COVER.jpg"
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
    for label, sec in [("before", 0.9), ("drop", 2.8), ("full", 5.0), ("product", 7.2), ("cta", 9.9)]:
        src = FRAMES / f"f_{int(sec * FPS):04d}.jpg"
        shutil.copy(src, qa / f"{label}.jpg")
        shutil.copy(src, ARTIFACTS / f"beard-v12-{label}.jpg")
    demo = ARTIFACTS / "beard-v12-product-beats-demo.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-ss", "6.4", "-i", str(out_mp4), "-t", "4.6",
            "-c:v", "libx264", "-crf", "22", "-preset", "fast", "-an", str(demo),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print("OK", out_mp4, out_mp4.stat().st_size)


if __name__ == "__main__":
    main()
