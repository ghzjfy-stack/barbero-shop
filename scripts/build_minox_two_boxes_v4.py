#!/usr/bin/env python3
"""MinoxShop TWO BOXES v4 — pain hook + beat growth + bombastic closer.

Stops the scroll: gut-punch hook → dynamic month progression → clear offer.
No dry pack-deck presentation.
"""
from __future__ import annotations

import math
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/tmp/two-boxes-v4")
ASSETS = ROOT / "assets"
FRAMES = ROOT / "frames"
QA = ROOT / "qa"
SFX = ROOT / "sfx"
EXPORTS = Path("/agent/repos/barbero-shop/exports")
for p in (FRAMES, QA, EXPORTS, ASSETS, SFX):
    p.mkdir(parents=True, exist_ok=True)

for _SRC in (Path("/tmp/two-boxes-v3e/assets"), Path("/tmp/two-boxes-v3d/assets"), Path("/tmp/two-boxes-v3c/assets")):
    if _SRC.exists():
        for name in ("pack_trim.png", "main-logo.png", "ba-before.jpg", "ba-after.jpg", "res_after.jpg"):
            if (_SRC / name).exists() and not (ASSETS / name).exists():
                shutil.copy2(_SRC / name, ASSETS / name)
        break

W, H = 1080, 1920
FPS = 60
DURATION = 15.0
N = int(DURATION * FPS)

BLACK = (0, 0, 0)
NAVY = (10, 18, 34)
NAVY_DEEP = (4, 8, 18)
GOLD = (196, 158, 86)
GOLD_SOFT = (226, 199, 135)
YELLOW = (255, 220, 40)
IVORY = (248, 248, 250)
MUTED = (150, 160, 178)
CTA_BG = (255, 214, 50)
CTA_INK = (12, 14, 20)

FONT_HE_B = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Bold.ttf"
FONT_HE_R = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf"
FONT_LAT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size: int, bold: bool = True, he: bool = True):
    if he:
        return ImageFont.truetype(FONT_HE_B if bold else FONT_HE_R, size)
    return ImageFont.truetype(FONT_LAT_B, size)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return 0.5 * (1 - math.cos(math.pi * t))


def ease_out_back(t):
    t = max(0.0, min(1.0, t))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def text_bb(draw, text, fnt, language=None):
    kw = {"language": language} if language else {}
    bb = draw.textbbox((0, 0), text, font=fnt, **kw)
    return bb[2] - bb[0], bb[3] - bb[1], bb


def draw_he(d, xy, text, fnt, fill):
    d.text(xy, text, font=fnt, fill=fill, language="he")


def is_latin_glyph(ch: str) -> bool:
    """Digits, Latin, currency, ? and common punctuation — Noto HE tofus these."""
    o = ord(ch)
    if ch in "?!.·|:;,/\\-+*=#%&@'\"₪$€£()[]{}<>":
        return True
    if 48 <= o <= 57:  # 0-9
        return True
    if 65 <= o <= 90 or 97 <= o <= 122:
        return True
    return False


def measure_mixed(draw, text: str, size: int, bold: bool = True):
    """Width of mixed HE+Latin string (drawn LTR chunks, overall RTL placement)."""
    f_he = font(size, bold, he=True)
    f_lat = font(size, bold, he=False)
    total = 0
    i = 0
    while i < len(text):
        lat = is_latin_glyph(text[i])
        j = i + 1
        while j < len(text) and is_latin_glyph(text[j]) == lat:
            j += 1
        chunk = text[i:j]
        fnt = f_lat if lat else f_he
        tw, th, bb = text_bb(draw, chunk, fnt, None if lat else "he")
        total += tw
        i = j
    # height from Hebrew font
    _, th, _ = text_bb(draw, "א", f_he, "he")
    return total, th


def draw_mixed_at(layer, text: str, x_left: int, y: int, size: int, fill, alpha: int = 255, bold: bool = True):
    """Draw mixed HE+Latin at x_left. Runs placed right-to-left for Hebrew reading order."""
    if alpha < 8:
        return 0
    d = ImageDraw.Draw(layer)
    f_he = font(size, bold, he=True)
    f_lat = font(size, bold, he=False)
    runs = []
    i = 0
    while i < len(text):
        lat = is_latin_glyph(text[i])
        j = i + 1
        while j < len(text) and is_latin_glyph(text[j]) == lat:
            j += 1
        runs.append((text[i:j], lat))
        i = j
    # visual LTR order for RTL sentence = reverse runs
    widths = []
    for chunk, lat in reversed(runs):
        fnt = f_lat if lat else f_he
        tw, th, bb = text_bb(d, chunk, fnt, None if lat else "he")
        widths.append((chunk, lat, fnt, tw, th, bb))
    total = sum(w[3] for w in widths)
    x = x_left
    a = int(max(0, min(255, alpha)))
    color = (*fill[:3], a)
    for chunk, lat, fnt, tw, th, bb in widths:
        xy = (x - bb[0], y - bb[1])
        if lat:
            d.text(xy, chunk, font=fnt, fill=color)
        else:
            draw_he(d, xy, chunk, fnt, color)
        x += tw
    return total


def draw_mixed_centered(layer, text: str, y: int, size: int, fill, alpha: int = 255, bold: bool = True):
    """Center mixed Hebrew/Latin; RTL run order so readers see חודש 4 not 4 חודש."""
    if alpha < 8:
        return
    d = ImageDraw.Draw(layer)
    tw, _ = measure_mixed(d, text, size, bold)
    # measure_mixed sums run widths in logical order — same total
    draw_mixed_at(layer, text, (W - tw) // 2, y, size, fill, alpha, bold)


def trim_white_edge(im: Image.Image, thresh: float = 230.0, max_frac: float = 0.3) -> Image.Image:
    arr = np.asarray(im.convert("RGB"))
    bright = arr.mean(axis=2) > thresh
    col = bright.mean(axis=0)
    left = 0
    for i, f in enumerate(col):
        if f < max_frac:
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


PACK = Image.open(ASSETS / "pack_trim.png").convert("RGBA")
LOGO = Image.open(ASSETS / "main-logo.png").convert("RGBA")
BEFORE = Image.open(ASSETS / "ba-before.jpg").convert("RGB")
AFTER = trim_white_edge(Image.open(ASSETS / "ba-after.jpg").convert("RGB"))
AFTER = ImageEnhance.Brightness(AFTER).enhance(1.06)
AFTER = ImageEnhance.Contrast(AFTER).enhance(1.08)


def cover_zoom(im: Image.Image, zoom: float, y_bias: float = 0.40) -> Image.Image:
    """Full-bleed cover crop with Ken Burns zoom (>1 = tighter)."""
    zoom = max(1.0, zoom)
    w, h = im.size
    # target aspect of frame
    target_aspect = W / H
    src_aspect = w / h
    if src_aspect > target_aspect:
        # wider — fit height then zoom
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


def navy_field(t: float = 0.0) -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cy, cx = H * 0.40, W * 0.5
    r = np.sqrt(((xx - cx) / (W * 0.55)) ** 2 + ((yy - cy) / (H * 0.42)) ** 2)
    pulse = 0.03 * math.sin(t * 1.2)
    s = np.clip(1.05 - r + pulse, 0, 1) ** 1.3
    deep = np.array(NAVY_DEEP, np.float32)
    base = np.array(NAVY, np.float32)
    arr = deep + (base - deep) * s[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def text_c(im, text, y, size, fill, alpha=255, he=True, bold=True):
    if alpha < 8:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(size, bold, he)
    tw, th, bb = text_bb(d, text, f, "he" if he else None)
    a = int(max(0, min(255, alpha)))
    color = (*fill[:3], a)
    xy = ((W - tw) // 2 - bb[0], y - bb[1])
    if he:
        draw_he(d, xy, text, f, color)
    else:
        d.text(xy, text, font=f, fill=color)
    im.alpha_composite(layer)


def caption_pop(im, text, y, size, fill, u, bg=(0, 0, 0), pad=18):
    """Punchy caption on black pill — scroll-stop readable."""
    if u < 0.04:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    scale = 0.90 + 0.10 * ease_out_back(min(1.0, u * 1.4))
    sz = max(18, int(size * scale))
    tw, th = measure_mixed(d, text, sz, True)
    bw, bh = tw + pad * 2, th + pad
    x0 = (W - bw) // 2
    yy = y - int(20 * (1 - u))
    a = int(255 * min(1.0, u * 1.2))
    d.rounded_rectangle([x0, yy, x0 + bw, yy + bh], 18, fill=(*bg, int(a * 0.88)))
    # draw mixed into a temp then composite centered in pill
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_mixed_centered(tmp, text, yy + (bh - th) // 2, sz, fill, a, True)
    layer.alpha_composite(tmp)
    im.alpha_composite(layer)


def line_u(t, start, end, fi=0.18, fo=0.22):
    if t < start or t > end:
        return 0.0
    u = 1.0
    if t < start + fi:
        u = ease_out((t - start) / fi)
    if t > end - fo:
        u *= max(0.0, 1.0 - (t - (end - fo)) / fo)
    return u


def apply_logo(im, alpha, y=40, size=92):
    if alpha < 0.05:
        return
    logo = LOGO.copy()
    logo.thumbnail((size, size), Image.Resampling.LANCZOS)
    logo.putalpha(logo.split()[-1].point(lambda a: int(a * alpha)))
    im.alpha_composite(logo, ((W - logo.size[0]) // 2, y))


def soft_shadow(im, pack, px, py, a=170, blur=36):
    sh = Image.new("RGBA", pack.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, a), (0, 0), pack.split()[-1])
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    im.alpha_composite(sh, (px - 8, py + 28))


def floor_stage(im, y_line=1088, alpha=0.55):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([180, y_line - 18, W - 180, y_line + 34], fill=(0, 0, 0, int(110 * alpha)))
    d.line([(160, y_line), (W - 160, y_line)], fill=(*GOLD, int(90 * alpha)), width=1)
    im.alpha_composite(layer)


def place_pack(im, max_w, y_center, pop=1.0, alpha=1.0):
    pop = max(0.0, min(1.0, pop))
    if pop < 0.02 or alpha < 0.02:
        return None
    p = PACK.copy()
    p = ImageEnhance.Brightness(p).enhance(1.14)
    p = ImageEnhance.Contrast(p).enhance(1.12)
    max_w = min(max_w, W - 100)
    p.thumbnail((max_w, int(max_w * 0.9)), Image.Resampling.LANCZOS)
    scale = 0.86 + 0.14 * ease_out_back(pop)
    pw = max(1, int(p.size[0] * scale))
    ph = max(1, int(p.size[1] * scale))
    pp = p.resize((pw, ph), Image.Resampling.LANCZOS)
    aa = pop * alpha
    if aa < 0.99:
        pp.putalpha(pp.split()[-1].point(lambda a: int(a * aa)))
    px = (W - pw) // 2
    py = int(y_center - ph / 2)
    py = max(180, min(py, 900 - ph))
    floor_stage(im, y_line=py + ph - 8, alpha=0.5 * aa)
    soft_shadow(im, pp, px, py, a=int(180 * aa))
    im.alpha_composite(pp, (px, py))
    return px, py, pw, ph


def blend_growth(progress: float, zoom: float) -> Image.Image:
    """Before→after morph with aggressive zoom."""
    p = max(0.0, min(1.0, progress))
    before = cover_zoom(BEFORE, zoom, y_bias=0.38)
    after = cover_zoom(AFTER, zoom * 0.98, y_bias=0.36)
    if p < 0.02:
        return before.convert("RGBA")
    if p > 0.98:
        return after.convert("RGBA")
    # soft horizontal wipe + opacity blend for motion feel
    arr_b = np.asarray(before).astype(np.float32)
    arr_a = np.asarray(after).astype(np.float32)
    # radial grow from crown center
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W * 0.50, H * 0.42
    r = np.sqrt(((xx - cx) / (W * 0.55)) ** 2 + ((yy - cy) / (H * 0.42)) ** 2)
    # threshold expands with progress
    mask = np.clip((p * 1.35 - r) / 0.22, 0, 1)
    out = arr_b * (1 - mask[:, :, None]) + arr_a * mask[:, :, None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def month_chip(im, text, u, y=220):
    if u < 0.05:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pop = ease_out_back(min(1.0, u * 1.5))
    tw, th = measure_mixed(d, text, 34, True)
    bw, bh = tw + 48, th + 28
    x0 = (W - bw) // 2
    yy = y - int(30 * (1 - pop))
    a = int(255 * min(1.0, u))
    d.rounded_rectangle([x0, yy, x0 + bw, yy + bh], bh // 2, fill=(0, 0, 0, int(a * 0.82)))
    d.rounded_rectangle([x0, yy, x0 + bw, yy + bh], bh // 2, outline=(*YELLOW, a), width=3)
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_mixed_centered(tmp, text, yy + (bh - th) // 2, 34, YELLOW, a, True)
    layer.alpha_composite(tmp)
    im.alpha_composite(layer)


def cta_button(im, text, u, y=1680):
    if u < 0.05:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(48, True)
    tw, th, bb = text_bb(d, text, f, "he")
    pop = ease_out_back(min(1.0, u * 1.3))
    bw, bh = max(720, tw + 80), th + 44
    # pulse
    pulse = 1.0 + 0.03 * math.sin(u * 18)
    bw, bh = int(bw * pulse * (0.92 + 0.08 * pop)), int(bh * (0.92 + 0.08 * pop))
    x0 = (W - bw) // 2
    yy = y - int(40 * (1 - pop))
    a = int(255 * min(1.0, u))
    # shadow
    d.rounded_rectangle([x0 + 6, yy + 10, x0 + bw + 6, yy + bh + 10], bh // 2, fill=(0, 0, 0, int(a * 0.45)))
    d.rounded_rectangle([x0, yy, x0 + bw, yy + bh], bh // 2, fill=(*CTA_BG, a))
    draw_he(
        d,
        (x0 + (bw - tw) // 2 - bb[0], yy + (bh - th) // 2 - bb[1]),
        text,
        f,
        (*CTA_INK, a),
    )
    im.alpha_composite(layer)


def value_chip(im, text, y, alpha, size=28):
    """One centered offer pill — never overlaps siblings."""
    if alpha < 0.05:
        return 0
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    tw, th = measure_mixed(d, text, size, True)
    bw, bh = tw + 40, th + 26
    x = (W - bw) // 2
    a = int(245 * alpha)
    d.rounded_rectangle([x, y, x + bw, y + bh], bh // 2, fill=(255, 255, 255, int(22 * alpha)))
    d.rounded_rectangle([x, y, x + bw, y + bh], bh // 2, outline=(*GOLD, int(180 * alpha)), width=2)
    draw_mixed_at(layer, text, x + (bw - tw) // 2, y + (bh - th) // 2, size, IVORY, a, True)
    im.alpha_composite(layer)
    return bh


def hook_frame(t: float) -> Image.Image:
    """0–3s: extreme scalp + gut-punch question."""
    # aggressive push-in
    zoom = 1.55 + 0.55 * ease_out(min(1.0, t / 2.8))
    plate = cover_zoom(BEFORE, zoom, y_bias=0.40).convert("RGBA")
    # darken edges / vignette for text punch
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.55)) ** 2 + ((yy - H * 0.45) / (H * 0.55)) ** 2)
    vig = np.clip(r, 0, 1) ** 1.4
    arr = np.asarray(plate).astype(np.float32)
    arr[:, :, :3] *= (1 - 0.55 * vig)[:, :, None]
    # bottom black bar for text
    arr[int(H * 0.62) :, :, :3] *= 0.25
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")

    # black caption block
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    block_y0 = 1180
    d.rectangle([40, block_y0, W - 40, 1680], fill=(0, 0, 0, 210))
    im.alpha_composite(layer)

    # exclusive: kill line 1 before line 2
    u1 = line_u(t, -0.05, 1.35, fi=0.16, fo=0.18)
    u2 = line_u(t, 1.42, 3.05, fi=0.16, fo=0.20)
    if u1 > 0.04:
        caption_pop(im, "מתי הבנת", 1220, 64, YELLOW, u1, bg=(0, 0, 0), pad=16)
        caption_pop(im, "שאתה מאבד את השיער שלך", 1360, 46, IVORY, u1, bg=(0, 0, 0), pad=14)
    if u2 > 0.04:
        caption_pop(im, "למה המפרצים ממשיכים", 1220, 48, YELLOW, u2, bg=(0, 0, 0), pad=14)
        caption_pop(im, "לגדול כל חודש", 1360, 52, IVORY, u2, bg=(0, 0, 0), pad=14)

    apply_logo(im, 0.55 + 0.25 * min(1.0, t / 0.4), y=36, size=84)
    return im


def growth_frame(t: float) -> Image.Image:
    """3–9.2s: beat-synced month progression with zoom."""
    local = t - 3.0
    # stepped densify so month chips match denser crowns
    if local < 1.55:
        prog = 0.08 + 0.12 * ease_in_out(local / 1.55)
    elif local < 3.40:
        prog = 0.28 + 0.28 * ease_in_out((local - 1.55) / 1.85)
    else:
        prog = 0.62 + 0.38 * ease_in_out(min(1.0, (local - 3.40) / 2.40))
    # stepped zoom punches on month beats
    zoom = 1.12 + 0.28 * prog
    for beat, punch in ((0.0, 0.08), (1.6, 0.12), (3.4, 0.14), (5.0, 0.08)):
        if local >= beat:
            dt = local - beat
            zoom += punch * max(0.0, 1.0 - dt / 0.45) * ease_out(min(1.0, dt / 0.12 + 0.01))

    plate = blend_growth(prog, zoom)
    im = plate

    # dark bottom gradient for chips
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for i in range(420):
        a = int(200 * (i / 420) ** 1.4)
        gd.line([(0, H - 420 + i), (W, H - 420 + i)], fill=(0, 0, 0, a))
    im.alpha_composite(grad)

    apply_logo(im, 0.75, y=36, size=84)

    # Hebrew month words — no ASCII digits (avoids bidi flip + tofu)
    month_chip(im, "חודש ראשון  מתחילים", line_u(t, 3.05, 4.45), y=200)
    month_chip(im, "חודש שני  הבייבי הייר יוצא", line_u(t, 4.55, 6.35), y=200)
    month_chip(im, "חודש רביעי  צפיפות מלאה", line_u(t, 6.45, 8.55), y=200)

    caption_pop(im, "השיער חוזר בקצב של החודשים", 1500, 36, IVORY, line_u(t, 3.2, 5.0), pad=14)
    caption_pop(im, "תוצאות אמיתיות על הקרקפת", 1500, 38, YELLOW, line_u(t, 5.2, 7.2), pad=14)
    caption_pop(im, "ככה זה נראה אחרי ארבעה חודשים", 1500, 36, IVORY, line_u(t, 7.3, 9.0), pad=14)

    text_c(im, "תוצאות משתנות בין אנשים", 1840, 18, (160, 165, 175), int(140 * min(1.0, (t - 3.0) / 0.4)))
    return im


def closer_frame(t: float) -> Image.Image:
    """9–15s: packs + value scream + CTA."""
    local = t - 9.0
    im = navy_field(t)
    apply_logo(im, 0.95, y=40, size=100)

    pop = ease_out(min(1.0, local / 0.35))
    lift = ease_out(min(1.0, (local - 3.2) / 0.4)) if local > 3.2 else 0.0
    place_pack(im, max_w=int(720 - 24 * lift), y_center=int(410 - 50 * lift), pop=pop, alpha=1.0)

    # price
    pu = ease_out(min(1.0, max(0.0, (local - 0.55) / 0.28)))
    if pu > 0.04:
        text_c(im, "שתי הקופסאות יחד", 980, 32, MUTED, int(230 * pu))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        f = font(96, True, he=False)
        price = "₪765"
        tw, th, bb = text_bb(d, price, f)
        a = int(255 * pu)
        d.text(((W - tw) // 2 - bb[0] + 3, 1040 - bb[1] + 3), price, font=f, fill=(0, 0, 0, int(a * 0.45)))
        d.text(((W - tw) // 2 - bb[0], 1040 - bb[1]), price, font=f, fill=(*YELLOW, a))
        im.alpha_composite(layer)

    vu = ease_out(min(1.0, max(0.0, (local - 1.15) / 0.3)))
    if vu > 0.04:
        h1 = value_chip(im, "משלוח חינם עד הבית", 1185, vu, size=28)
        value_chip(im, "מאתיים נקודות מתנה", 1185 + h1 + 14, vu, size=28)
        text_c(im, "למצטרפים חדשים למועדון  בלי קודים", 1345, 28, GOLD_SOFT, int(230 * vu))

    cta_button(im, "להזמנה מהירה", ease_out(min(1.0, max(0.0, (local - 1.8) / 0.35))), y=1580)
    text_c(im, "תוצאות משתנות בין אנשים", 1840, 18, (120, 130, 145), int(150 * min(1.0, local / 0.4)))
    return im


def frame_at(t: float) -> Image.Image:
    if t < 3.05:
        im = hook_frame(t)
        # soft cut into growth
        if t > 2.75:
            fade = (t - 2.75) / 0.30
            g = growth_frame(3.05)
            im = Image.blend(im.convert("RGBA"), g, max(0.0, min(1.0, fade)))
        return im
    if t < 9.15:
        im = growth_frame(t)
        if t > 8.75:
            fade = (t - 8.75) / 0.40
            c = closer_frame(9.15)
            im = Image.blend(im.convert("RGBA"), c, max(0.0, min(1.0, fade)))
        return im
    return closer_frame(t)


def make_cover() -> Image.Image:
    im = navy_field(0.5)
    apply_logo(im, 0.95, y=40, size=104)
    place_pack(im, max_w=760, y_center=410, pop=1.0, alpha=1.0)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(92, True, he=False)
    price = "₪765"
    tw, th, bb = text_bb(d, price, f)
    d.text(((W - tw) // 2 - bb[0] + 2, 960 - bb[1] + 2), price, font=f, fill=(0, 0, 0, 120))
    d.text(((W - tw) // 2 - bb[0], 960 - bb[1]), price, font=f, fill=(*YELLOW, 255))
    im.alpha_composite(layer)
    caption_pop(im, "מתי הבנת שאתה מאבד את השיער", 1140, 36, YELLOW, 1.0, pad=14)
    value_chip(im, "משלוח חינם עד הבית", 1280, 1.0, size=28)
    value_chip(im, "מאתיים נקודות מתנה", 1360, 1.0, size=28)
    cta_button(im, "להזמנה מהירה", 1.0, y=1560)
    return im.convert("RGB")


def build_audio():
    """Punchy bed + swoosh hits on month beats. No soft generic bed."""
    import subprocess

    bed_src = Path("/tmp/scrubber-v5/sfx/bed_punch.wav")
    whoosh = Path("/tmp/minox-reel-v8/whoosh.wav")
    if not bed_src.exists():
        bed_src = Path("/tmp/scrubber-v4/sfx/bed_punch.wav")
    out = SFX / "bed_v4.wav"
    # loop/pad bed to 15s, slight speed-up for energy
    subprocess.check_call(
        [
            "ffmpeg",
            "-y",
            "-stream_loop",
            "2",
            "-i",
            str(bed_src),
            "-i",
            str(whoosh),
            "-filter_complex",
            (
                "[0:a]atrim=0:15,asetpts=PTS-STARTPTS,volume=0.95[bed];"
                "[1:a]volume=1.35,afade=t=out:st=0.22:d=0.12[w];"
                # swooshes at month beats + closer hit
                "[w]asplit=4[w1][w2][w3][w4];"
                "[w1]adelay=3050|3050[a1];"
                "[w2]adelay=4550|4550[a2];"
                "[w3]adelay=6450|6450[a3];"
                "[w4]adelay=9100|9100[a4];"
                "[bed][a1][a2][a3][a4]amix=inputs=5:duration=first:dropout_transition=0,volume=1.15[aout]"
            ),
            "-map",
            "[aout]",
            "-t",
            "15",
            str(out),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return out


def main():
    print(f"two-boxes v4 hook-beat {N}f @{FPS}")
    for i in range(N):
        t = i / FPS
        fr = frame_at(t).convert("RGB")
        fr.save(FRAMES / f"f_{i:04d}.jpg", quality=92, optimize=True)
        if i % 60 == 0:
            print(f"frame {i} {t:.1f}s")
        if i in (0, 30, 90, 150, 210, 300, 390, 480, 570, 660, 780, 840):
            fr.save(QA / f"qa_{i:04d}.jpg", quality=92)
    cover = make_cover()
    cover.save(EXPORTS / "MinoxShop-two-boxes_v4-COVER.jpg", quality=94, optimize=True)
    cover.save(QA / "cover.jpg", quality=94)
    print("DONE frames")


if __name__ == "__main__":
    main()
