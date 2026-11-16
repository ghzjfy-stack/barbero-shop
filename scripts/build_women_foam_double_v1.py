#!/usr/bin/env python3
"""Women Rogaine 5% foam DOUBLE reel + afternoon story — v1.

SKU: rogaine-double-woman (8 months · ₪758 · save ₪240 · הכי משתלם)
Hook: רואה את הקרקפת באור?
Visual: navy women system (matches tipot story), not men's cream foam reel.
~13s · 30fps · soft bed · CapCut-safe margins.
"""
from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "exports" / "women-foam-double"
WORK = Path("/tmp/women-foam-v1")
FRAMES = WORK / "frames"
ASSETS = WORK / "assets"
EXPORT.mkdir(parents=True, exist_ok=True)
FRAMES.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1080, 1920, 30
DURATION = 13.0
N = int(DURATION * FPS)

HEB_B = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Bold.ttf"
HEB_R = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf"
LAT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LAT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

NAVY = (12, 24, 48)
NAVY2 = (18, 36, 68)
GOLD = (198, 161, 91)
GOLD_SOFT = (220, 190, 130)
INK = (22, 26, 38)
WHITE = (255, 255, 255)
MUTED = (180, 190, 210)

PRICE, PRICE_WAS, PRICE_SAVE = 758, 998, 240
MONTHLY = 95  # 758/8
PRODUCT_URL = "https://www.minox-shop.co.il/shop#product-rogaine-double-woman"


def font(size: int, bold: bool = True, he: bool = True):
    if he:
        return ImageFont.truetype(HEB_B if bold else HEB_R, size)
    return ImageFont.truetype(LAT_B if bold else LAT_R, size)


def font_lat(size: int, bold: bool = True):
    return font(size, bold, he=False)


def is_latin_glyph(ch: str) -> bool:
    """Digits/Latin/% — Noto Hebrew tofus these."""
    o = ord(ch)
    if ch in "?!.·|:;,/\\-+*=#%&@'\"₪$€£()[]{}<>":
        return True
    if 48 <= o <= 57:
        return True
    if 65 <= o <= 90 or 97 <= o <= 122:
        return True
    return False


def text_bb(draw, text, fnt, language=None):
    kw = {"language": language} if language else {}
    bb = draw.textbbox((0, 0), text, font=fnt, **kw)
    return bb[2] - bb[0], bb[3] - bb[1], bb


def measure_mixed(draw, text: str, size: int, bold: bool = True):
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
        tw, _, _ = text_bb(draw, chunk, fnt, None if lat else "he")
        total += tw
        i = j
    _, th, _ = text_bb(draw, "א", f_he, "he")
    return total, th


def draw_mixed_at(layer, text: str, x_left: int, y: int, size: int, fill, alpha: int = 255, bold: bool = True):
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


def draw_mixed_centered(im: Image.Image, text: str, y: int, size: int, fill, alpha: int = 255, bold: bool = True, shadow: int = 4):
    if alpha < 8:
        return
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw, _ = measure_mixed(probe, text, size, bold)
    x = (W - tw) // 2
    if shadow:
        for ox, oy, a in ((0, shadow, 140), (0, max(1, shadow // 2), 90)):
            layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
            draw_mixed_at(layer, text, x + ox, y + oy, size, (0, 0, 0), int(a * alpha / 255), bold)
            im.alpha_composite(layer)
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw_mixed_at(layer, text, x, y, size, fill, alpha, bold)
    im.alpha_composite(layer)


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 3 * t * t - 2 * t * t * t


def ease_out_back(t: float) -> float:
    t = max(0.0, min(1.0, t))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def navy_field(warm: float = 0.0, light_y: float = 0.28) -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, H * light_y
    r = np.sqrt(((xx - cx) / (W * 0.72)) ** 2 + ((yy - cy) / (H * 0.85)) ** 2)
    mix = np.clip(1 - 0.55 * r, 0.0, 1.0)
    base = np.array(NAVY, dtype=np.float32)
    hi = np.array(NAVY2, dtype=np.float32) + np.array([18, 14, 8], dtype=np.float32) * warm
    arr = base + (hi - base) * mix[:, :, None]
    # soft window light bloom (scalp-in-light metaphor)
    bloom = np.exp(-(((xx - cx) / (W * 0.28)) ** 2 + ((yy - cy) / (H * 0.18)) ** 2))
    arr = arr + bloom[:, :, None] * np.array([55, 48, 35], dtype=np.float32) * (0.55 + 0.25 * warm)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(wash)
    d.ellipse((180, -80, 900, 520), fill=(255, 230, 190, 28))
    d.ellipse((-120, 1280, 520, 1980), fill=(198, 161, 91, 18))
    return Image.alpha_composite(im, wash.filter(ImageFilter.GaussianBlur(55)))


def text_c(im: Image.Image, txt: str, y: int, size: int, fill, alpha: int = 255, bold: bool = True, shadow: int = 4, lat: bool = False):
    if alpha < 8:
        return
    if lat:
        f = font_lat(size, bold)
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        bb = d.textbbox((0, 0), txt, font=f)
        x = (W - (bb[2] - bb[0])) // 2 - bb[0]
        for ox, oy, a in ((0, shadow, 140), (0, max(1, shadow // 2), 90)):
            d.text((x + ox, y + oy), txt, font=f, fill=(0, 0, 0, int(a * alpha / 255)))
        d.text((x, y), txt, font=f, fill=(*fill, alpha))
        im.alpha_composite(layer)
        return
    # Mixed HE + digits/% so Noto Hebrew never tofus Latin glyphs
    if any(is_latin_glyph(ch) for ch in txt):
        draw_mixed_centered(im, txt, y, size, fill, alpha, bold, shadow)
        return
    f = font(size, bold, he=True)
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bb = d.textbbox((0, 0), txt, font=f, language="he")
    x = (W - (bb[2] - bb[0])) // 2 - bb[0]
    for ox, oy, a in ((0, shadow, 140), (0, max(1, shadow // 2), 90)):
        d.text((x + ox, y + oy), txt, font=f, fill=(0, 0, 0, int(a * alpha / 255)), language="he")
    d.text((x, y), txt, font=f, fill=(*fill, alpha), language="he")
    im.alpha_composite(layer)


def gold_rule(im: Image.Image, y: int, width: int, alpha: int = 255):
    if width < 4 or alpha < 8:
        return
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([(W - width) // 2, y, (W + width) // 2, y + 3], 2, fill=GOLD + (alpha,))


def wink(im: Image.Image, cx: int, cy: int, phase: float, scale: float = 1.0):
    pulse = math.sin(math.pi * max(0.0, min(1.0, phase)))
    if pulse < 0.05:
        return
    a = int(240 * pulse)
    sp = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sp)
    r = int(18 * scale * (0.5 + 0.5 * pulse))
    d.line([(cx - r, cy), (cx + r, cy)], fill=(255, 248, 220, a), width=max(2, int(3 * scale)))
    d.line([(cx, cy - r), (cx, cy + r)], fill=(255, 248, 220, a), width=max(2, int(3 * scale)))
    c = max(2, int(4 * scale * pulse))
    d.ellipse([cx - c, cy - c, cx + c, cy + c], fill=(255, 255, 255, a))
    im.alpha_composite(sp.filter(ImageFilter.GaussianBlur(1.6)))
    im.alpha_composite(sp)


def soft_shadow(c: Image.Image, box: Image.Image, x: int, y: int, a: int = 120):
    sh = Image.new("RGBA", (box.size[0] + 80, 70), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([12, 18, box.size[0] + 60, 50], fill=(0, 0, 0, int(a * 0.55)))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (x - 40, y + box.size[1] - 8))


def reflection(p: Image.Image, op: float = 0.28, frac: float = 0.32) -> Image.Image:
    f = p.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    f = ImageEnhance.Brightness(f).enhance(0.45)
    w, h = f.size
    h2 = max(8, int(h * frac))
    f = f.crop((0, 0, w, h2))
    fade = Image.new("L", (w, h2), 0)
    d = ImageDraw.Draw(fade)
    for i in range(h2):
        d.line([(0, i), (w, i)], fill=int(255 * op * max(0.0, 1 - i / (h2 * 0.92))))
    f.putalpha(fade)
    return f.filter(ImageFilter.GaussianBlur(3.2))


def diagonal_shine(im: Image.Image, x: int, y: int, w: int, h: int, phase: float):
    u = max(0.0, min(1.0, phase))
    if u <= 0.02 or u >= 0.98:
        return
    band_w = max(40, int(w * 0.2))
    band = Image.new("RGBA", (band_w, h), (0, 0, 0, 0))
    px = band.load()
    for i in range(band_w):
        a = int(50 * math.sin(math.pi * i / max(1, band_w - 1)))
        for j in range(h):
            px[i, j] = (255, 250, 235, a)
    sheared = Image.new("RGBA", (w + band_w, h), (0, 0, 0, 0))
    for j in range(h):
        ox = int((j / max(1, h - 1)) * band_w * 0.5)
        sheared.alpha_composite(band.crop((0, j, band_w, j + 1)), (ox, j))
    cx = int(x - band_w + u * (w + band_w * 2))
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    layer.alpha_composite(sheared.crop((0, 0, w, h)).filter(ImageFilter.GaussianBlur(5)), (cx, y))
    im.alpha_composite(layer)


def cut_white_bg(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    rgb = np.array(im.convert("RGB")).astype(np.float32)
    dist = np.linalg.norm(rgb - np.array([255, 255, 255], np.float32), axis=2)
    a = np.where(dist < 16, 0, 255).astype(np.uint8)
    edge = (dist >= 16) & (dist < 38)
    a = np.where(edge, np.clip(((dist - 16) / 22.0) * 255, 0, 255).astype(np.uint8), a)
    im.putalpha(Image.fromarray(a, "L").filter(ImageFilter.GaussianBlur(0.5)))
    bb = im.getbbox()
    return im.crop(bb) if bb else im


def load_pack() -> Image.Image:
    src = ASSETS / "rogaine-double-woman.png"
    if not src.exists():
        raise SystemExit(f"missing pack asset: {src}")
    dbl = cut_white_bg(src)
    # target width for 9:16 hero
    tw = 860
    sc = tw / dbl.size[0]
    return dbl.resize((tw, max(1, int(dbl.size[1] * sc))), Image.Resampling.LANCZOS)


def load_logo() -> Image.Image:
    for p in (ASSETS / "logo.png", ASSETS / "main-logo.png"):
        if p.exists():
            im = Image.open(p).convert("RGBA")
            im.thumbnail((110, 110), Image.Resampling.LANCZOS)
            return im
    raise SystemExit("missing logo")


def brand_logo(im: Image.Image, t: float, logo: Image.Image):
    enter = ease_out(min(1.0, t / 0.4))
    if enter < 0.02:
        return
    pulse = 1.0 + 0.035 * math.sin(t * math.pi * 1.1) * min(1.0, max(0.0, t - 0.45))
    lw = max(1, int(logo.size[0] * pulse))
    lh = max(1, int(logo.size[1] * pulse))
    lg = logo.resize((lw, lh), Image.Resampling.LANCZOS)
    pad = 12
    plate_w, plate_h = lw + pad * 2, lh + pad * 2
    plate = Image.new("RGBA", (plate_w, plate_h), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle([0, 0, plate_w - 1, plate_h - 1], 16, fill=(255, 255, 255, int(230 * enter)))
    plate.alpha_composite(lg, (pad, pad))
    sh = Image.new("RGBA", (plate_w + 28, plate_h + 28), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([6, 8, plate_w + 14, plate_h + 14], 18, fill=(0, 0, 0, int(55 * enter)))
    x = (W - plate_w) // 2
    y = 48
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (x - 8, y - 4))
    im.alpha_composite(plate, (x, y))
    if 1.1 < (t % 3.2) < 1.45:
        wink(im, x + plate_w - 8, y + 10, ((t % 3.2) - 1.1) / 0.35, 0.7)


def product_frame(pack: Image.Image, scale: float, alpha: float) -> Image.Image:
    pw = max(1, int(pack.size[0] * scale))
    ph = max(1, int(pack.size[1] * scale))
    pp = pack.resize((pw, ph), Image.Resampling.LANCZOS)
    if alpha < 0.999:
        pp = pp.copy()
        pp.putalpha(pp.split()[-1].point(lambda a: int(a * alpha)))
    inset = 28
    fw, fh = pw + inset * 2, ph + inset * 2
    card = Image.new("RGBA", (fw + 40, fh + 48), (0, 0, 0, 0))
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([16, 20, fw + 28, fh + 32], 28, fill=(0, 0, 0, int(90 * alpha)))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    plate = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle([0, 0, fw - 1, fh - 1], 24, fill=(255, 255, 255, int(245 * alpha)))
    ImageDraw.Draw(plate).rounded_rectangle([2, 2, fw - 3, fh - 3], 22, outline=GOLD + (int(180 * alpha),), width=2)
    plate.alpha_composite(pp, (inset, inset))
    card.alpha_composite(plate, (18, 8))
    return card


def chip(im: Image.Image, txt: str, y: int, alpha: float, style: str = "navy"):
    if alpha < 0.05:
        return
    size = 28 if style == "navy" else 26
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw, th = measure_mixed(probe, txt, size, True)
    pw, ph = tw + 48, th + 22
    pill = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(pill)
    if style == "navy":
        d.rounded_rectangle([0, 0, pw - 1, ph - 1], ph // 2, fill=(255, 255, 255, int(235 * alpha)))
        fill = INK
    elif style == "gold":
        d.rounded_rectangle([0, 0, pw - 1, ph - 1], ph // 2, fill=GOLD + (int(235 * alpha),))
        fill = NAVY
    else:
        d.rounded_rectangle([0, 0, pw - 1, ph - 1], ph // 2, fill=(255, 255, 255, int(220 * alpha)))
        d.rounded_rectangle([1, 1, pw - 2, ph - 2], ph // 2, outline=GOLD + (int(200 * alpha),), width=2)
        fill = WHITE
    draw_mixed_at(pill, txt, 24, 11, size, fill, int(255 * alpha), True)
    im.alpha_composite(pill, ((W - pw) // 2, y + int((1 - alpha) * 24)))


def price_block(im: Image.Image, y: int, alpha: int = 255):
    if alpha < 8:
        return
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    price = f"₪ {PRICE}"
    was = f"₪{PRICE_WAS}"
    f_price = font_lat(64, True)
    f_was = font_lat(24, True)
    bb = d.textbbox((0, 0), price, font=f_price)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x = (W - tw) // 2 - bb[0]
    d.text((x, y + 3), price, font=f_price, fill=(0, 0, 0, int(100 * alpha / 255)))
    d.text((x, y), price, font=f_price, fill=(*WHITE, alpha))
    wb = d.textbbox((0, 0), was, font=f_was)
    ww = wb[2] - wb[0]
    wx = (W - ww) // 2 - wb[0]
    wy = y + th + 18
    d.text((wx, wy), was, font=f_was, fill=(160, 168, 185, int(alpha * 0.9)))
    mid = wy + (wb[3] - wb[1]) // 2 + 2
    d.line([(wx - 2, mid), (wx + ww + 2, mid)], fill=(160, 168, 185, int(alpha * 0.9)), width=3)
    im.alpha_composite(layer)

    # savings pill: ₪240 חיסכון
    he, amt = "חיסכון", f"₪{PRICE_SAVE}"
    f_he = font(22, True)
    f_amt = font_lat(22, True)
    hb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), he, font=f_he, language="he")
    ab = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), amt, font=f_amt)
    hw, hh = hb[2] - hb[0], hb[3] - hb[1]
    aw, ah = ab[2] - ab[0], ab[3] - ab[1]
    pad_x, pad_y, gap = 20, 10, 10
    pill_w = aw + gap + hw + pad_x * 2
    pill_h = max(hh, ah) + pad_y * 2
    pill = Image.new("RGBA", (pill_w, pill_h), (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle([0, 0, pill_w - 1, pill_h - 1], pill_h // 2, fill=GOLD + (int(235 * alpha / 255),))
    ImageDraw.Draw(pill).text((pad_x - ab[0], (pill_h - ah) // 2 - ab[1]), amt, font=f_amt, fill=(*NAVY, alpha))
    ImageDraw.Draw(pill).text(
        (pad_x + aw + gap - hb[0], (pill_h - hh) // 2 - hb[1]), he, font=f_he, fill=(*NAVY, alpha), language="he"
    )
    sy = wy + (wb[3] - wb[1]) + 14
    im.alpha_composite(pill, ((W - pill_w) // 2, sy))

    # monthly
    my = sy + pill_h + 10
    text_c(im, f"₪{MONTHLY}", my, 24, MUTED, int(alpha * 0.95), lat=True, shadow=1)
    text_c(im, "לחודש", my + 30, 22, MUTED, int(alpha * 0.85), bold=False, shadow=1)


def frame_at(i: int, pack: Image.Image, logo: Image.Image) -> Image.Image:
    t = i / FPS

    # ---- 0–2.8 HOOK ----
    if t < 2.8:
        local = t / 2.8
        im = navy_field(warm=0.25 + 0.2 * math.sin(t * 1.4), light_y=0.26 + 0.02 * math.sin(t))
        # soft light rays
        rays = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        rd = ImageDraw.Draw(rays)
        for k in range(7):
            ang = -0.55 + k * 0.18
            x0, y0 = W // 2, 220
            x1 = int(x0 + math.sin(ang) * 900)
            y1 = int(y0 + math.cos(ang) * 1100)
            rd.line([(x0, y0), (x1, y1)], fill=(255, 235, 200, 16 + k % 3), width=18)
        im.alpha_composite(rays.filter(ImageFilter.GaussianBlur(18)))

        a = int(255 * ease_out(min(1.0, t / 0.28)))
        text_c(im, "רואה את הקרקפת באור?", 780, 52, WHITE, a, shadow=6)
        if a > 40:
            gold_rule(im, 870, int(200 * ease_out(min(1.0, (t - 0.2) / 0.3))), a)
        sub = ease_out(min(1.0, max(0.0, (t - 0.55) / 0.35)))
        text_c(im, "יש קצף 5% שנוח לנשים", 910, 34, GOLD_SOFT, int(245 * sub), shadow=3)
        if t > 1.9:
            tease = ease_out(min(1.0, (t - 1.9) / 0.35))
            text_c(im, "מארז כפול · 8 חודשים", 1180, 36, WHITE, int(240 * tease), shadow=4)
        brand_logo(im, t, logo)
        return im

    # ---- 2.8–7.2 PRODUCT ----
    if t < 7.2:
        local = (t - 2.8) / 4.4
        im = navy_field(warm=0.12 + 0.05 * math.sin(local * math.pi), light_y=0.32)
        ta = int(255 * ease_out(min(1.0, local / 0.18)))
        text_c(im, "Rogaine", 200, 42, WHITE, ta, lat=True, shadow=3)
        gold_rule(im, 262, int(140 * ease_out(min(1.0, (local - 0.05) / 0.2))), ta)
        text_c(im, "קצף 5% לנשים", 285, 44, GOLD, ta, shadow=3)
        text_c(im, "מארז כפול ל־8 חודשים", 350, 30, MUTED, int(ta * 0.92), bold=False, shadow=2)

        pop = ease_out_back(min(1.0, max(0.0, (local - 0.08) / 0.3)))
        pop_c = max(0.0, min(1.0, pop))
        drift = 1.0 + 0.03 * ease_in_out(max(0.0, (local - 0.4) / 0.6))
        card = product_frame(pack, 0.92 * drift * (0.9 + 0.1 * pop_c), pop_c)
        px = (W - card.size[0]) // 2
        py = 430 + int((1 - pop_c) * 90)
        im.alpha_composite(card, (px, py))
        if pop_c > 0.75:
            diagonal_shine(im, px + 40, py + 30, card.size[0] - 80, card.size[1] - 70, (local - 0.35) / 0.55)
            wink(im, px + card.size[0] - 70, py + 50, (local - 0.4) / 0.22, 0.9)

        chip_a = ease_out(min(1.0, max(0.0, (local - 0.42) / 0.2)))
        chip(im, "פעם ביום · בלי ריח", 1180, chip_a, "navy")
        chip(im, "הכי משתלם", 1255, chip_a * ease_out(min(1.0, max(0.0, (local - 0.52) / 0.18))), "gold")

        if local > 0.62:
            pa = int(255 * ease_out(min(1.0, (local - 0.62) / 0.2)))
            price_block(im, 1385, pa)

        brand_logo(im, t, logo)
        return im

    # ---- 7.2–10.4 OFFER ----
    if t < 10.4:
        local = (t - 7.2) / 3.2
        im = navy_field(warm=0.18, light_y=0.3)
        # soft rising particles
        bub = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        db = ImageDraw.Draw(bub)
        rng = np.random.default_rng(11)
        for k in range(22):
            bx = int(rng.integers(50, W - 50))
            by = int((rng.random() * H + local * 70 * (0.4 + rng.random())) % H)
            br = int(6 + rng.random() * 18)
            db.ellipse([bx - br, by - br, bx + br, by + br], fill=(255, 255, 255, int(14 + rng.random() * 18)))
        im.alpha_composite(bub.filter(ImageFilter.GaussianBlur(1.2)))

        ta = int(255 * ease_out(min(1.0, local / 0.2)))
        text_c(im, "10% נקודות בונוס", 200, 46, WHITE, ta, shadow=4)
        gold_rule(im, 268, int(170 * ease_out(min(1.0, (local - 0.08) / 0.22))), ta)
        text_c(im, "בנובמבר · על הקנייה", 295, 28, GOLD_SOFT, int(ta * 0.95), bold=False, shadow=2)
        text_c(im, "משלוח חינם עד הבית", 345, 28, MUTED, int(ta * 0.9), bold=False, shadow=2)

        pop = ease_out_back(min(1.0, max(0.0, (local - 0.1) / 0.28)))
        pop_c = max(0.0, min(1.0, pop))
        card = product_frame(pack, 0.78 * (0.92 + 0.08 * pop_c), pop_c)
        px = (W - card.size[0]) // 2
        py = 430 + int((1 - pop_c) * 70)
        soft_shadow(im, card, px, py, a=int(100 * pop_c))
        if pop_c > 0.55:
            ref = reflection(card, op=0.22 * min(1, (pop_c - 0.55) / 0.45), frac=0.28)
            im.alpha_composite(ref, (px, py + card.size[1] - 10))
        im.alpha_composite(card, (px, py))
        if pop_c > 0.8:
            wink(im, px + int(card.size[0] * 0.78), py + 40, (local - 0.4) / 0.2, 0.85)

        if local > 0.38:
            price_block(im, 1280, int(255 * ease_out(min(1.0, (local - 0.38) / 0.2))))
        brand_logo(im, t, logo)
        return im

    # ---- 10.4–13.0 CTA ----
    local = (t - 10.4) / 2.6
    im = navy_field(warm=0.22, light_y=0.34)
    ta = int(255 * ease_out(min(1.0, local / 0.22)))
    text_c(im, "מארז כפול לנשים", 220, 44, WHITE, ta, shadow=4)
    gold_rule(im, 285, int(160 * ease_out(min(1.0, (local - 0.08) / 0.22))), ta)
    text_c(im, "קצף 5% · 8 חודשים", 310, 32, GOLD, int(ta * 0.95), shadow=3)

    pop = ease_out_back(min(1.0, max(0.0, (local - 0.1) / 0.3)))
    pop_c = max(0.0, min(1.0, pop))
    # Slightly smaller hero so raised CTA has clear air
    card = product_frame(pack, 0.78 * (0.94 + 0.06 * pop_c), pop_c)
    px = (W - card.size[0]) // 2
    py = 360 + int((1 - pop_c) * 50)
    im.alpha_composite(card, (px, py))

    cta_a = ease_out(min(1.0, max(0.0, (local - 0.35) / 0.25)))
    if cta_a > 0.05:
        # CapCut/TT safe: CTA must sit ABOVE username + caption chrome (~y≤1420)
        label = "הזמיני באתר"
        f = font(36, True)
        bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), label, font=f, language="he")
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        pw, ph = tw + 72, th + 30
        btn = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        ImageDraw.Draw(btn).rounded_rectangle([0, 0, pw - 1, ph - 1], ph // 2, fill=GOLD + (int(245 * cta_a),))
        ImageDraw.Draw(btn).text((36 - bb[0], 15 - bb[1]), label, font=f, fill=(*NAVY, int(255 * cta_a)), language="he")
        im.alpha_composite(btn, ((W - pw) // 2, 1360 + int((1 - cta_a) * 18)))
        text_c(im, "minox-shop.co.il", 1455, 28, MUTED, int(230 * cta_a), lat=True, shadow=2)
        text_c(im, "תוצאות משתנות בין אנשים", 1680, 18, (120, 130, 150), int(150 * cta_a), bold=False, shadow=1)

    brand_logo(im, t, logo)
    return im


def build_story(pack: Image.Image, logo: Image.Image) -> Image.Image:
    """Afternoon IG/FB story still — navy women system."""
    im = navy_field(warm=0.2, light_y=0.3)
    # logo plate is the brand mark (matches tipot story hierarchy without duplicate wordmark)

    card = product_frame(pack, 0.95, 1.0)
    px = (W - card.size[0]) // 2
    im.alpha_composite(card, (px, 240))

    text_c(im, "Rogaine", 980, 54, WHITE, 255, lat=True, shadow=4)
    text_c(im, "קצף 5% לנשים", 1060, 40, GOLD, 255, shadow=3)
    text_c(im, "מארז כפול ל־8 חודשים", 1130, 30, MUTED, 255, bold=False, shadow=2)

    # price strip
    price_block(im, 1240, 255)
    text_c(im, "minox-shop.co.il", 1680, 28, MUTED, 230, lat=True, shadow=2)

    # small logo plate bottom-safe
    brand_logo(im, 2.0, logo)
    return im.convert("RGB")


def build_cover(pack: Image.Image) -> Image.Image:
    im = navy_field(warm=0.18, light_y=0.34)
    text_c(im, "Rogaine", 240, 44, WHITE, 255, lat=True, shadow=3)
    gold_rule(im, 300, 150, 255)
    text_c(im, "קצף 5% לנשים", 330, 48, GOLD, 255, shadow=3)
    text_c(im, "מארז כפול · 8 חודשים", 400, 32, MUTED, 255, bold=False, shadow=2)
    card = product_frame(pack, 0.9, 1.0)
    px = (W - card.size[0]) // 2
    im.alpha_composite(card, (px, 500))
    chip(im, "הכי משתלם", 1180, 1.0, "gold")
    text_c(im, f"₪ {PRICE}", 1320, 56, WHITE, 255, lat=True, shadow=3)
    text_c(im, "הזמיני באתר", 1480, 34, GOLD_SOFT, 255, shadow=2)
    return im.convert("RGB")


def write_kit():
    caption = f"""רואה את הקרקפת באור?

Rogaine קצף 5% לנשים — מארז כפול ל־8 חודשים.
הכי משתלם · חיסכון ₪{PRICE_SAVE} · ₪{PRICE}
בנובמבר: 10% נקודות בונוס ומשלוח חינם עד הבית.

{PRODUCT_URL}

#מינוקסידיל #Rogaine #נשירתשיער #MinoxShop #קצף
"""
    (EXPORT / "CAPTION.txt").write_text(caption.strip() + "\n", encoding="utf-8")
    upload = f"""ריל + סטורי — Rogaine קצף 5% לנשים · מארז כפול

SKU: rogaine-double-woman
לינק: {PRODUCT_URL}

קבצים:
- MinoxShop-WOMEN-foam-double-v1-13s.mp4
- MinoxShop-WOMEN-foam-double-v1-COVER.jpg
- MinoxShop-WOMEN-foam-double-STORY-afternoon.jpg

מלל סטורי (על התמונה כבר מוטמע):
Rogaine
קצף 5% לנשים
מארז כפול ל־8 חודשים

סטיקר לינק סטורי:
{PRODUCT_URL}

קאפשן ריל: ראי CAPTION.txt

הערות:
- הנוזל 2% לנשים כבר הוצג — זה הריל הבא (קצף כפול)
- אל תכתוב 10% הנחה — זה נקודות בונוס
"""
    (EXPORT / "UPLOAD.txt").write_text(upload.strip() + "\n", encoding="utf-8")


def encode(silent: Path, out: Path, bed: Path | None):
    if bed and bed.exists():
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", str(FRAMES / "f_%04d.jpg"),
            "-i", str(bed),
            "-filter_complex",
            f"[1:a]afade=t=in:st=0:d=0.6,afade=t=out:st={DURATION-0.8}:d=0.8,volume=0.55,atrim=0:{DURATION}[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
            "-c:a", "aac", "-b:a", "160k",
            "-shortest", "-movflags", "+faststart",
            str(out),
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", str(FRAMES / "f_%04d.jpg"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
            "-movflags", "+faststart",
            str(out),
        ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # also silent for review
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", str(FRAMES / "f_%04d.jpg"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "veryfast",
            "-an", "-movflags", "+faststart",
            str(silent),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    # ensure pack downloaded
    pack_src = ASSETS / "rogaine-double-woman.png"
    if not pack_src.exists():
        subprocess.run(
            ["curl", "-sL", "https://www.minox-shop.co.il/rogaine-double-woman.png", "-o", str(pack_src)],
            check=True,
        )
    if not (ASSETS / "main-logo.png").exists():
        subprocess.run(
            ["curl", "-sL", "https://www.minox-shop.co.il/main-logo.png", "-o", str(ASSETS / "main-logo.png")],
            check=True,
        )
    if not (ASSETS / "logo.png").exists() and Path("/tmp/foam-v39/logo.png").exists():
        shutil.copy(Path("/tmp/foam-v39/logo.png"), ASSETS / "logo.png")

    pack = load_pack()
    logo = load_logo()
    pack.save(ASSETS / "double_cut.png")

    print(f"rendering {N} frames @ {FPS}fps")
    qa_idxs = {0, int(1.2 * FPS), int(3.5 * FPS), int(5.5 * FPS), int(8.5 * FPS), int(11.5 * FPS), N - 1}
    for i in range(N):
        fr = frame_at(i, pack, logo)
        fr.convert("RGB").save(FRAMES / f"f_{i:04d}.jpg", quality=93, optimize=True)
        if i in qa_idxs:
            fr.convert("RGB").save(WORK / f"qa_{i:04d}.jpg", quality=92)
        if i % 60 == 0:
            print(f"  frame {i}/{N} ({i/FPS:.1f}s)")

    story = build_story(pack, logo)
    cover = build_cover(pack)
    story_path = EXPORT / "MinoxShop-WOMEN-foam-double-STORY-afternoon.jpg"
    cover_path = EXPORT / "MinoxShop-WOMEN-foam-double-v1-COVER.jpg"
    story.save(story_path, quality=94, optimize=True)
    cover.save(cover_path, quality=94, optimize=True)

    bed = WORK / "bed_soft.wav"
    if not bed.exists():
        bed = WORK / "bed_fun.wav"
    out = EXPORT / "MinoxShop-WOMEN-foam-double-v1-13s.mp4"
    silent = WORK / "silent.mp4"
    encode(silent, out, bed if bed.exists() else None)
    write_kit()

    # demo copy for review
    demo = WORK / "recording_demo.mp4"
    shutil.copy(out, demo)
    print("DONE")
    print("video:", out)
    print("cover:", cover_path)
    print("story:", story_path)


if __name__ == "__main__":
    main()
