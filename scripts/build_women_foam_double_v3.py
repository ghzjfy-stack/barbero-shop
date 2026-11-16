#!/usr/bin/env python3
"""Women Rogaine 5% foam DOUBLE v3 — same bar as men's foam v39 (or higher).

Owner: v2 felt cute/shortchanged vs men. Women must not feel lesser; must convert.
Production: cream luxury field, men-level shine/shadow/reflection/price, dedicated
bonus screen, feminine natural Hebrew, pack cinema (solo → double), NO navy catalog.
"""
from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

sys.path.insert(0, "/tmp/women-foam-v3")
from brand_logo import apply_brand_logo

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "exports" / "women-foam-double"
WORK = Path("/tmp/women-foam-v3")
FRAMES = WORK / "frames"
ASSETS = WORK / "assets"
EXPORT.mkdir(parents=True, exist_ok=True)
FRAMES.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1080, 1920, 30
DURATION = 14.0
N = int(DURATION * FPS)

HEB_B = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Bold.ttf"
HEB_R = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf"
LAT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LAT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

CREAM = (245, 240, 232)
CREAM2 = (252, 248, 242)
GOLD = (196, 158, 86)
INK = (22, 26, 38)
NAVY = (14, 28, 52)
WHITE = (255, 255, 255)
MUTED = (90, 94, 108)

PRICE, PRICE_WAS, PRICE_SAVE = 758, 998, 240
MONTHLY = 95
PRODUCT_URL = "https://www.minox-shop.co.il/shop#product-rogaine-double-woman"


def font(size, bold=True, he=True):
    if he:
        return ImageFont.truetype(HEB_B if bold else HEB_R, size)
    return ImageFont.truetype(LAT_B if bold else LAT_R, size)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return 3 * t * t - 2 * t * t * t


def ease_out_back(t):
    t = max(0.0, min(1.0, t))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def is_latin_glyph(ch):
    o = ord(ch)
    if ch in "?!.·|:;,/\\-+*=#%&@'\"₪$€£()[]{}<>":
        return True
    if 48 <= o <= 57 or 65 <= o <= 90 or 97 <= o <= 122:
        return True
    return False


def text_bb(draw, text, fnt, language=None):
    kw = {"language": language} if language else {}
    bb = draw.textbbox((0, 0), text, font=fnt, **kw)
    return bb[2] - bb[0], bb[3] - bb[1], bb


def measure_mixed(draw, text, size, bold=True):
    f_he, f_lat = font(size, bold, True), font(size, bold, False)
    total = i = 0
    while i < len(text):
        lat = is_latin_glyph(text[i])
        j = i + 1
        while j < len(text) and is_latin_glyph(text[j]) == lat:
            j += 1
        tw, _, _ = text_bb(draw, text[i:j], f_lat if lat else f_he, None if lat else "he")
        total += tw
        i = j
    _, th, _ = text_bb(draw, "א", f_he, "he")
    return total, th


def draw_mixed_at(layer, text, x_left, y, size, fill, alpha=255, bold=True):
    if alpha < 8:
        return 0
    d = ImageDraw.Draw(layer)
    f_he, f_lat = font(size, bold, True), font(size, bold, False)
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
    color = (*fill[:3], int(alpha))
    for chunk, lat, fnt, tw, th, bb in widths:
        xy = (x - bb[0], y - bb[1])
        if lat:
            d.text(xy, chunk, font=fnt, fill=color)
        else:
            d.text(xy, chunk, font=fnt, fill=color, language="he")
        x += tw
    return sum(w[3] for w in widths)


def text_c(im, txt, y, size, fill, alpha=255, bold=True, shadow=4, lat=False):
    if alpha < 8:
        return
    if lat:
        f = font(size, bold, False)
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        bb = d.textbbox((0, 0), txt, font=f)
        x = (W - (bb[2] - bb[0])) // 2 - bb[0]
        for ox, oy, a in ((0, shadow, 140), (0, max(1, shadow // 2), 90)):
            d.text((x + ox, y + oy), txt, font=f, fill=(0, 0, 0, int(a * alpha / 255)))
        d.text((x, y), txt, font=f, fill=(*fill, alpha))
        im.alpha_composite(layer)
        return
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw, _ = measure_mixed(probe, txt, size, bold)
    x = (W - tw) // 2
    if shadow:
        for ox, oy, a in ((0, shadow, 140), (0, max(1, shadow // 2), 90)):
            layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
            draw_mixed_at(layer, txt, x + ox, y + oy, size, (0, 0, 0), int(a * alpha / 255), bold)
            im.alpha_composite(layer)
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw_mixed_at(layer, txt, x, y, size, fill, alpha, bold)
    im.alpha_composite(layer)


def cream_field(warm=0.0):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, H * 0.42
    r = np.sqrt(((xx - cx) / (W * 0.75)) ** 2 + ((yy - cy) / (H * 0.9)) ** 2)
    mix = np.clip(1 - 0.20 * r, 0.75, 1.0)
    base = np.array(CREAM, np.float32)
    hi = np.array(CREAM2, np.float32)
    arr = base + (hi - base) * mix[:, :, None]
    arr[:, :, 0] = np.clip(arr[:, :, 0] + 6 * warm, 0, 255)
    arr[:, :, 1] = np.clip(arr[:, :, 1] + 3 * warm, 0, 255)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(wash)
    d.ellipse((-200, 1000, 560, 1800), fill=(255, 220, 180, 26))
    d.ellipse((620, -160, 1300, 560), fill=(255, 235, 210, 20))
    return Image.alpha_composite(im, wash.filter(ImageFilter.GaussianBlur(70)))


def gold_rule(im, y, width, alpha=255):
    if width < 4 or alpha < 8:
        return
    ImageDraw.Draw(im).rounded_rectangle([(W - width) // 2, y, (W + width) // 2, y + 4], 2, fill=GOLD + (alpha,))


def wink(im, cx, cy, phase, scale=1.0):
    pulse = math.sin(math.pi * max(0.0, min(1.0, phase)))
    if pulse < 0.05:
        return
    a = int(255 * pulse)
    sp = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sp)
    r = int(20 * scale * (0.55 + 0.45 * pulse))
    d.line([(cx - r, cy), (cx + r, cy)], fill=(255, 250, 230, a), width=max(2, int(3 * scale)))
    d.line([(cx, cy - r), (cx, cy + r)], fill=(255, 250, 230, a), width=max(2, int(3 * scale)))
    core = max(2, int(5 * scale * pulse))
    d.ellipse([cx - core, cy - core, cx + core, cy + core], fill=(255, 255, 255, a))
    im.alpha_composite(sp.filter(ImageFilter.GaussianBlur(2)))
    im.alpha_composite(sp)


def soft_shadow(c, box, x, y, a=110):
    sh = Image.new("RGBA", (box.size[0] + 70, 64), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([10, 16, box.size[0] + 55, 46], fill=(30, 22, 14, int(a * 0.55)))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (x - 35, y + box.size[1] - 10))


def reflection(p, op=0.28, frac=0.32):
    f = p.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    f = ImageEnhance.Brightness(f).enhance(0.42)
    w, h = f.size
    h2 = max(8, int(h * frac))
    f = f.crop((0, 0, w, h2))
    fade = Image.new("L", (w, h2), 0)
    d = ImageDraw.Draw(fade)
    for i in range(h2):
        d.line([(0, i), (w, i)], fill=int(255 * op * max(0.0, 1 - i / (h2 * 0.92))))
    f.putalpha(fade)
    return f.filter(ImageFilter.GaussianBlur(3.5))


def diagonal_shine(im, x, y, w, h, phase):
    u = max(0.0, min(1.0, phase))
    if u <= 0.02 or u >= 0.98:
        return
    band_w = max(40, int(w * 0.22))
    band = Image.new("RGBA", (band_w, h), (0, 0, 0, 0))
    px = band.load()
    for i in range(band_w):
        a = int(55 * math.sin(math.pi * i / max(1, band_w - 1)))
        for j in range(h):
            px[i, j] = (255, 250, 235, a)
    sheared = Image.new("RGBA", (w + band_w, h), (0, 0, 0, 0))
    for j in range(h):
        ox = int((j / max(1, h - 1)) * band_w * 0.55)
        sheared.alpha_composite(band.crop((0, j, band_w, j + 1)), (ox, j))
    cx = int(x - band_w + u * (w + band_w * 2))
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    layer.alpha_composite(sheared.crop((0, 0, w, h)).filter(ImageFilter.GaussianBlur(6)), (cx, y))
    im.alpha_composite(layer)


def benefit_card(title, sub, accent, scale, alpha):
    """Premium cream card — text-forward proof (no fake BA photos)."""
    cw = int(460 * scale)
    ch = int(420 * scale)
    card = Image.new("RGBA", (cw + 36, ch + 50), (0, 0, 0, 0))
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([14, 18, cw + 24, ch + 28], 26, fill=(20, 16, 12, int(90 * alpha)))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    plate = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle([0, 0, cw - 1, ch - 1], 24, fill=(255, 255, 255, int(250 * alpha)))
    ImageDraw.Draw(plate).rounded_rectangle([2, 2, cw - 3, ch - 3], 22, outline=GOLD + (int(180 * alpha),), width=3)
    # accent blot
    blot = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(blot).ellipse([cw // 2 - 90, 40, cw // 2 + 90, 220], fill=accent + (int(40 * alpha),))
    plate.alpha_composite(blot.filter(ImageFilter.GaussianBlur(18)))
    # titles
    tmp = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw, th = measure_mixed(probe, title, 34, True)
    draw_mixed_at(tmp, title, (cw - tw) // 2, 150, 34, INK, int(255 * alpha), True)
    tw2, _ = measure_mixed(probe, sub, 24, False)
    draw_mixed_at(tmp, sub, (cw - tw2) // 2, 220, 24, MUTED, int(240 * alpha), False)
    plate.alpha_composite(tmp)
    card.alpha_composite(plate, (18, 8))
    return card


def chip(im, txt, y, alpha, style="white"):
    if alpha < 0.05:
        return
    size = 28 if style != "gold" else 26
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw, th = measure_mixed(probe, txt, size, True)
    pw, ph = tw + 52, th + 24
    pill = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(pill)
    if style == "navy":
        d.rounded_rectangle([0, 0, pw - 1, ph - 1], ph // 2, fill=NAVY + (int(235 * alpha),))
        fill = WHITE
    elif style == "gold":
        d.rounded_rectangle([0, 0, pw - 1, ph - 1], ph // 2, fill=GOLD + (int(235 * alpha),))
        fill = NAVY
    else:
        d.rounded_rectangle([0, 0, pw - 1, ph - 1], ph // 2, fill=(255, 255, 255, int(242 * alpha)))
        d.rounded_rectangle([1, 1, pw - 2, ph - 2], ph // 2, outline=NAVY + (int(140 * alpha),), width=2)
        fill = INK
    draw_mixed_at(pill, txt, 26, 12, size, fill, int(255 * alpha), True)
    im.alpha_composite(pill, ((W - pw) // 2, y + int((1 - alpha) * 28)))


def price_block(im, y, alpha=255, large=True):
    if alpha < 8:
        return
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    price = f"₪ {PRICE}"
    was = f"₪{PRICE_WAS}"
    f_price = font(68 if large else 52, True, False)
    f_was = font(26 if large else 22, True, False)
    bb = d.textbbox((0, 0), price, font=f_price)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x = (W - tw) // 2 - bb[0]
    for ox, oy, a in ((0, 4, 110), (0, 2, 80)):
        d.text((x + ox, y + oy), price, font=f_price, fill=(0, 0, 0, int(a * alpha / 255)))
    d.text((x, y), price, font=f_price, fill=(*INK, alpha))
    wb = d.textbbox((0, 0), was, font=f_was)
    ww = wb[2] - wb[0]
    wx = (W - ww) // 2 - wb[0]
    wy = y + th + 20
    d.text((wx, wy), was, font=f_was, fill=(120, 124, 136, int(alpha * 0.85)))
    mid = wy + (wb[3] - wb[1]) // 2 + 2
    d.line([(wx - 2, mid), (wx + ww + 2, mid)], fill=(120, 124, 136, int(alpha * 0.9)), width=3)
    im.alpha_composite(layer)

    he, amt = "חיסכון", f"₪{PRICE_SAVE}"
    f_he, f_amt = font(24, True, True), font(24, True, False)
    hb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), he, font=f_he, language="he")
    ab = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), amt, font=f_amt)
    hw, hh = hb[2] - hb[0], hb[3] - hb[1]
    aw, ah = ab[2] - ab[0], ab[3] - ab[1]
    pad_x, pad_y, gap = 22, 12, 12
    pill_w = aw + gap + hw + pad_x * 2
    pill_h = max(hh, ah) + pad_y * 2
    pill = Image.new("RGBA", (pill_w, pill_h), (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle([0, 0, pill_w - 1, pill_h - 1], pill_h // 2, fill=NAVY + (int(235 * alpha / 255),))
    ImageDraw.Draw(pill).text((pad_x - ab[0], (pill_h - ah) // 2 - ab[1]), amt, font=f_amt, fill=(255, 255, 255, alpha))
    ImageDraw.Draw(pill).text(
        (pad_x + aw + gap - hb[0], (pill_h - hh) // 2 - hb[1]), he, font=f_he, fill=(255, 255, 255, alpha), language="he"
    )
    sy = wy + (wb[3] - wb[1]) + 16
    im.alpha_composite(pill, ((W - pill_w) // 2, sy))

    my = sy + pill_h + 12
    text_c(im, f"₪{MONTHLY}", my, 24, MUTED, int(alpha * 0.95), lat=True, shadow=1)
    text_c(im, "לחודש", my + 30, 22, (120, 124, 136), int(alpha * 0.9), bold=False, shadow=1)


def load_assets():
    solo = Image.open(ASSETS / "women_solo.png").convert("RGBA")
    bb = solo.getbbox()
    solo = solo.crop(bb) if bb else solo
    sh = 520
    solo = solo.resize((max(1, int(solo.size[0] * sh / solo.size[1])), sh), Image.Resampling.LANCZOS)

    dbl = Image.open(ASSETS / "double_cut.png").convert("RGBA")
    left = Image.open(ASSETS / "left_cut.png").convert("RGBA")
    right = Image.open(ASSETS / "right_cut.png").convert("RGBA")
    return {"solo": solo, "dbl": dbl, "left": left, "right": right}


def frame_at(i, A):
    t = i / FPS

    # ---- 0–3.2 PROOF / PROMISE (cream twin cards — no fake scalp photos) ----
    if t < 3.2:
        im = cream_field(0.06 + 0.03 * math.sin(t * 1.2))
        ta = int(255 * ease_out(min(1.0, t / 0.25)))
        text_c(im, "לנשים שרואות קרקפת", 200, 44, INK, ta, shadow=3)
        if ta > 40:
            gold_rule(im, 268, int(170 * ease_out(min(1.0, (t - 0.12) / 0.25))), ta)
        text_c(im, "יש קצף שנוח באמת", 295, 36, MUTED, int(ta * 0.95), bold=False, shadow=2)

        pop = ease_out_back(min(1.0, max(0.0, (t - 0.2) / 0.35)))
        pop_c = max(0.0, min(1.0, pop))
        scale = 0.9 + 0.1 * pop_c
        left = benefit_card("פעם ביום", "לא פעמיים", NAVY, scale, pop_c)
        right = benefit_card("בלי ריח לוואי", "נוח לשגרה", (140, 70, 70), scale, pop_c)
        gap = 28
        total = left.size[0] + right.size[0] + gap
        x0 = (W - total) // 2
        y0 = 420 + int((1 - pop_c) * 70)
        slide = int((1 - pop_c) * 40)
        im.alpha_composite(left, (x0 - slide, y0))
        im.alpha_composite(right, (x0 + left.size[0] + gap + slide, y0))
        if pop_c > 0.85:
            wink(im, W // 2, y0 + left.size[1] // 2 - 10, (t - 0.7) / 0.25, 0.85)

        if t >= 2.35:
            vb = ease_out(min(1.0, (t - 2.35) / 0.28))
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(overlay).rectangle([0, 1280, W, H], fill=(12, 10, 8, int(145 * vb)))
            im.alpha_composite(overlay.filter(ImageFilter.GaussianBlur(10)))
            text_c(im, "מארז כפול ל־8 חודשים", 1420, 48, WHITE, int(255 * vb), shadow=8)
            text_c(im, "המארז המקורי מארה״ב", 1505, 30, (250, 246, 238), int(240 * vb), shadow=4)
        return im

    # ---- 3.2–7.2 PRODUCT CINEMA ----
    if t < 7.2:
        local = (t - 3.2) / 4.0
        im = cream_field(0.05 + 0.04 * math.sin(local * math.pi))
        ta = int(255 * ease_out(min(1.0, local / 0.16)))
        text_c(im, "מארז כפול ל־8 חודשים", 200, 46, INK, ta, shadow=3)
        gold_rule(im, 272, int(150 * ease_out(min(1.0, (local - 0.05) / 0.22))), ta)
        text_c(im, "קצף 5% לנשים · מקורי מארה״ב", 300, 28, MUTED, int(ta * 0.92), bold=False, shadow=2)

        # first solo, then double replaces with slam feel
        if local < 0.42:
            pop = ease_out_back(min(1.0, max(0.0, local / 0.28)))
            pop_c = max(0.0, min(1.0, pop))
            drift = 1.0 + 0.03 * ease_in_out(max(0, (local - 0.2) / 0.22))
            pack = A["solo"]
            ps = 0.9 + 0.1 * pop_c
            pw = max(1, int(pack.size[0] * ps * drift))
            ph = max(1, int(pack.size[1] * ps * drift))
            pp = pack.resize((pw, ph), Image.Resampling.LANCZOS)
            if pop_c < 1:
                pp = pp.copy()
                pp.putalpha(pp.split()[-1].point(lambda a: int(a * pop_c)))
            px = (W - pw) // 2
            py = 430 + int((1 - pop_c) * 100)
            soft_shadow(im, pp, px, py, a=int(130 * pop_c))
            if pop_c > 0.5:
                im.alpha_composite(reflection(pp, 0.28 * min(1, (pop_c - 0.5) / 0.5), 0.32), (px, py + ph - 6))
            im.alpha_composite(pp, (px, py))
            if pop_c > 0.8:
                diagonal_shine(im, px, py, pw, ph, (local - 0.15) / 0.35)
                wink(im, px + int(pw * 0.72), py + 30, (local - 0.2) / 0.2, 1.0)
        else:
            # double slam from left/right
            u = (local - 0.42) / 0.58
            left_c = ease_out_back(min(1.0, u / 0.35))
            right_c = ease_out_back(min(1.0, max(0.0, (u - 0.12) / 0.32)))
            left_c = max(0.0, min(1.0, left_c))
            right_c = max(0.0, min(1.0, right_c))
            shake = max(0.0, 1.0 - max(0.0, (u - 0.12) / 0.15)) * right_c
            ls = 0.82 * (0.9 + 0.1 * left_c)
            rs = 0.82 * (0.9 + 0.1 * right_c)
            left = A["left"].resize((max(1, int(A["left"].size[0] * ls)), max(1, int(A["left"].size[1] * ls))), Image.Resampling.LANCZOS)
            right = A["right"].resize((max(1, int(A["right"].size[0] * rs)), max(1, int(A["right"].size[1] * rs))), Image.Resampling.LANCZOS)
            if left_c < 1:
                left = left.copy()
                left.putalpha(left.split()[-1].point(lambda a: int(a * left_c)))
            if right_c < 1:
                right = right.copy()
                right.putalpha(right.split()[-1].point(lambda a: int(a * right_c)))
            gap = 16
            total_w = left.size[0] + right.size[0] + gap
            x0 = (W - total_w) // 2 + int(shake * 7 * math.sin(u * 50))
            y0 = 400
            lx = x0 - int((1 - left_c) * 70)
            rx = x0 + left.size[0] + gap + int((1 - right_c) * 110)
            soft_shadow(im, left, lx, y0, a=int(120 * left_c))
            soft_shadow(im, right, rx, y0, a=int(120 * right_c))
            im.alpha_composite(left, (lx, y0))
            im.alpha_composite(right, (rx, y0))
            if right_c > 0.75:
                diagonal_shine(im, x0, y0, total_w, left.size[1], (u - 0.25) / 0.45)
                wink(im, rx + int(right.size[0] * 0.65), y0 + 26, (u - 0.3) / 0.2, 0.9)

        chips = [
            (0.48, "מריחה אחת ביום", 1125, "navy"),
            (0.58, "מתייבש מהר", 1200, "white"),
            (0.68, "הכי משתלם", 1275, "gold"),
        ]
        for start, txt, yy, style in chips:
            ca = ease_out(min(1.0, max(0.0, (local - start) / 0.16)))
            chip(im, txt, yy, ca, style)

        if local > 0.72:
            price_block(im, 1420, int(255 * ease_out(min(1.0, (local - 0.72) / 0.18))), large=True)

        im = apply_brand_logo(im, t - 3.2, y=36, size=96)
        return im

    # ---- 7.2–10.4 DEDICATED OFFER (like men) ----
    if t < 10.4:
        local = (t - 7.2) / 3.2
        im = cream_field(0.08)
        rng = np.random.default_rng(7)
        bub = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        db = ImageDraw.Draw(bub)
        for _ in range(26):
            bx = int(rng.integers(40, W - 40))
            by = int((rng.random() * H + local * 90 * (0.5 + rng.random())) % H)
            br = int(8 + rng.random() * 26)
            db.ellipse([bx - br, by - br, bx + br, by + br], fill=(255, 255, 255, int(16 + rng.random() * 20)))
        im.alpha_composite(bub.filter(ImageFilter.GaussianBlur(1.2)))

        ta = int(255 * ease_out(min(1.0, local / 0.18)))
        text_c(im, "עשרה אחוז נקודות בונוס", 200, 46, INK, ta, shadow=3)
        gold_rule(im, 272, int(180 * ease_out(min(1.0, (local - 0.08) / 0.22))), ta)
        text_c(im, "בנובמבר על כל קנייה", 300, 28, INK, int(ta * 0.95), shadow=2)
        text_c(im, "משלוח חינם עד הבית", 350, 26, MUTED, int(ta * 0.9), bold=False, shadow=2)

        pop = ease_out_back(min(1.0, max(0.0, (local - 0.12) / 0.28)))
        pop_c = max(0.0, min(1.0, pop))
        dbl = A["dbl"]
        ps = 0.78 + 0.12 * pop_c
        drift = 1.0 + 0.03 * ease_in_out(max(0, (local - 0.42) / 0.58))
        pw = max(1, int(dbl.size[0] * ps * drift))
        ph = max(1, int(dbl.size[1] * ps * drift))
        pp = dbl.resize((pw, ph), Image.Resampling.LANCZOS)
        if pop_c < 1:
            pp = pp.copy()
            pp.putalpha(pp.split()[-1].point(lambda a: int(a * pop_c)))
        px = (W - pw) // 2
        py = 470 + int((1 - pop_c) * 90)
        soft_shadow(im, pp, px, py, a=int(135 * pop_c))
        if pop_c > 0.5:
            im.alpha_composite(reflection(pp, 0.32 * min(1, (pop_c - 0.5) / 0.5), 0.34), (px, py + ph - 6))
        im.alpha_composite(pp, (px, py))
        if pop_c > 0.85:
            diagonal_shine(im, px, py, pw, ph, (local - 0.4) / 0.5)
            wink(im, px + int(pw * 0.72), py + 34, (local - 0.4) / 0.2, 1.0)

        if local > 0.4:
            price_block(im, 1240, int(255 * ease_out(min(1.0, (local - 0.4) / 0.2))), large=False)

        im = apply_brand_logo(im, t - 3.2, y=36, size=96)
        return im

    # ---- 10.4–14.0 CTA ----
    local = (t - 10.4) / 3.6
    im = cream_field(0.07)
    ta = int(255 * ease_out(min(1.0, local / 0.2)))
    text_c(im, "מארז כפול לנשים", 210, 46, INK, ta, shadow=3)
    gold_rule(im, 278, int(150 * ease_out(min(1.0, (local - 0.08) / 0.22))), ta)
    text_c(im, "קצף 5% · 8 חודשים", 305, 30, MUTED, int(ta * 0.95), shadow=2)

    pop = ease_out_back(min(1.0, max(0.0, (local - 0.1) / 0.3)))
    pop_c = max(0.0, min(1.0, pop))
    dbl = A["dbl"]
    ps = 0.8 * (0.92 + 0.08 * pop_c)
    pw = max(1, int(dbl.size[0] * ps))
    ph = max(1, int(dbl.size[1] * ps))
    pp = dbl.resize((pw, ph), Image.Resampling.LANCZOS)
    if pop_c < 1:
        pp = pp.copy()
        pp.putalpha(pp.split()[-1].point(lambda a: int(a * pop_c)))
    px = (W - pw) // 2
    py = 400 + int((1 - pop_c) * 55)
    soft_shadow(im, pp, px, py, a=int(130 * pop_c))
    im.alpha_composite(pp, (px, py))
    if pop_c > 0.8:
        diagonal_shine(im, px, py, pw, ph, (local - 0.28) / 0.5)

    cta_a = ease_out(min(1.0, max(0.0, (local - 0.3) / 0.22)))
    if cta_a > 0.05:
        pulse = 1.0 + 0.04 * math.sin(max(0, local - 0.35) * math.pi * 2.1)
        label = "הזמיני עכשיו"
        f = font(36, True, True)
        bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), label, font=f, language="he")
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        pw2, ph2 = int((tw + 72) * pulse), int((th + 30) * pulse)
        btn = Image.new("RGBA", (pw2, ph2), (0, 0, 0, 0))
        ImageDraw.Draw(btn).rounded_rectangle([0, 0, pw2 - 1, ph2 - 1], ph2 // 2, fill=NAVY + (int(245 * cta_a),))
        ImageDraw.Draw(btn).text(
            ((pw2 - tw) // 2 - bb[0], (ph2 - th) // 2 - bb[1]),
            label,
            font=f,
            fill=(255, 255, 255, int(255 * cta_a)),
            language="he",
        )
        im.alpha_composite(btn, ((W - pw2) // 2, 1140 + int((1 - cta_a) * 14)))
        text_c(im, "minox-shop.co.il", 1240, 26, MUTED, int(230 * cta_a), lat=True, shadow=2)
        text_c(im, "תוצאות משתנות בין אנשים", 1520, 18, (120, 124, 136), int(150 * cta_a), bold=False, shadow=1)

    im = apply_brand_logo(im, t - 3.2, y=36, size=96)
    return im


def build_cover(A):
    im = cream_field(0.08)
    text_c(im, "קצף 5% לנשים", 220, 48, INK, 255, shadow=3)
    gold_rule(im, 290, 160, 255)
    text_c(im, "מארז כפול · 8 חודשים", 320, 32, MUTED, 255, shadow=2)
    dbl = A["dbl"]
    ps = 0.88
    pw = max(1, int(dbl.size[0] * ps))
    ph = max(1, int(dbl.size[1] * ps))
    pp = dbl.resize((pw, ph), Image.Resampling.LANCZOS)
    px = (W - pw) // 2
    soft_shadow(im, pp, px, 470, 130)
    im.alpha_composite(pp, (px, 470))
    chip(im, "הכי משתלם", 1160, 1.0, "gold")
    text_c(im, f"₪ {PRICE}", 1280, 58, INK, 255, lat=True, shadow=3)
    text_c(im, "הזמיני עכשיו", 1420, 34, NAVY, 255, shadow=2)
    im = apply_brand_logo(im, 2.0, y=36, size=96)
    return im.convert("RGB")


def build_story(A):
    im = cream_field(0.1)
    dbl = A["dbl"]
    ps = 0.95
    pw = max(1, int(dbl.size[0] * ps))
    ph = max(1, int(dbl.size[1] * ps))
    pp = dbl.resize((pw, ph), Image.Resampling.LANCZOS)
    px = (W - pw) // 2
    soft_shadow(im, pp, px, 280, 140)
    im.alpha_composite(pp, (px, 280))
    text_c(im, "Rogaine", 980, 48, INK, 255, lat=True, shadow=3)
    text_c(im, "קצף 5% לנשים", 1050, 40, (140, 70, 70), 255, shadow=3)
    text_c(im, "מארז כפול · 8 חודשים", 1115, 28, MUTED, 255, bold=False, shadow=2)
    price_block(im, 1200, 255, large=False)
    text_c(im, "minox-shop.co.il", 1680, 26, MUTED, 230, lat=True, shadow=2)
    im = apply_brand_logo(im, 2.0, y=36, size=96)
    return im.convert("RGB")


def write_kit():
    (EXPORT / "CAPTION-v3.txt").write_text(
        f"""לנשים שרואות קרקפת — יש קצף שנוח באמת.

Rogaine קצף 5% לנשים · מארז כפול ל־8 חודשים.
מריחה אחת ביום · בלי ריח לוואי · ₪{PRICE} (חיסכון ₪{PRICE_SAVE})
בנובמבר: 10% נקודות בונוס + משלוח חינם עד הבית.

{PRODUCT_URL}

#מינוקסידיל #Rogaine #נשירתשיער #MinoxShop #קצף
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (EXPORT / "UPLOAD-v3.txt").write_text(
        """ריל v3 — אותה רמה כמו ריל הגברים (קרם לוקשר) · קצף 5% לנשים כפול

קבצים:
- MinoxShop-WOMEN-foam-double-v3-14s.mp4
- MinoxShop-WOMEN-foam-double-v3-COVER.jpg
- MinoxShop-WOMEN-foam-double-STORY-afternoon-v3.jpg

למה v3:
- לא נייבי-חמוד — קרם לוקשר כמו foam גברים v39
- מסך בונוס נפרד (לא דחוס בסוף)
- סולו → סלאם כפול · shine/reflection/price כמו לגברים
- עברית נשית טבעית · הזמיני עכשיו
""".strip()
        + "\n",
        encoding="utf-8",
    )


def encode(out: Path):
    bed = WORK / "bed_fun.wav"
    if not bed.exists():
        bed = WORK / "bed_soft.wav"
    if bed.exists():
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", str(FRAMES / "f_%04d.jpg"),
            "-i", str(bed),
            "-filter_complex",
            f"[1:a]afade=t=in:st=0:d=0.5,afade=t=out:st={DURATION-0.7}:d=0.7,volume=0.55,atrim=0:{DURATION}[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
            "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
            str(out),
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", str(FRAMES / "f_%04d.jpg"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
            "-an", "-movflags", "+faststart", str(out),
        ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main():
    A = load_assets()
    print(f"render {N} @ {FPS}fps")
    qa = {0, int(1.5 * FPS), int(3.8 * FPS), int(5.5 * FPS), int(8.5 * FPS), int(11.5 * FPS), N - 1}
    for i in range(N):
        fr = frame_at(i, A)
        fr.convert("RGB").save(FRAMES / f"f_{i:04d}.jpg", quality=93, optimize=True)
        if i in qa:
            fr.convert("RGB").save(WORK / "qa" / f"qa_{i:04d}.jpg", quality=92)
        if i % 60 == 0:
            print(f"  {i}/{N}")

    cover = build_cover(A)
    story = build_story(A)
    cover.save(EXPORT / "MinoxShop-WOMEN-foam-double-v3-COVER.jpg", quality=94, optimize=True)
    story.save(EXPORT / "MinoxShop-WOMEN-foam-double-STORY-afternoon-v3.jpg", quality=94, optimize=True)
    out = EXPORT / "MinoxShop-WOMEN-foam-double-v3-14s.mp4"
    encode(out)
    write_kit()
    shutil.copy(out, WORK / "recording_demo.mp4")
    print("DONE", out)


if __name__ == "__main__":
    main()
