#!/usr/bin/env python3
"""Women Rogaine 5% foam DOUBLE v4 — shed-hand pain hook + men's cream offer bar.

Owner + experts: v3 cream was medium without proof. Build shed-hand DNA like
men's pain/proof reels, then same cream luxury product cinema.
Hook line: עוד שיער ביד?
"""
from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

sys.path.insert(0, "/tmp/women-foam-v4")
from brand_logo import apply_brand_logo

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "exports" / "women-foam-double"
WORK = Path("/tmp/women-foam-v4")
FRAMES = WORK / "frames"
ASSETS = WORK / "assets"
EXPORT.mkdir(parents=True, exist_ok=True)
FRAMES.mkdir(parents=True, exist_ok=True)
(WORK / "qa").mkdir(parents=True, exist_ok=True)

W, H, FPS = 1080, 1920, 30
DURATION = 14.0
N = int(DURATION * FPS)

HEB_B = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Bold.ttf"
HEB_R = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf"
LAT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LAT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

CREAM, CREAM2 = (245, 240, 232), (252, 248, 242)
GOLD, INK, NAVY = (196, 158, 86), (22, 26, 38), (14, 28, 52)
WHITE, MUTED = (255, 255, 255), (90, 94, 108)
PRICE, PRICE_WAS, PRICE_SAVE, MONTHLY = 758, 998, 240, 95
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
    runs, i = [], 0
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


def text_c(im, txt, y, size, fill, alpha=255, bold=True, shadow=5, lat=False):
    if alpha < 8:
        return
    if lat:
        f = font(size, bold, False)
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        bb = d.textbbox((0, 0), txt, font=f)
        x = (W - (bb[2] - bb[0])) // 2 - bb[0]
        for ox, oy, a in ((0, shadow, 150), (0, max(1, shadow // 2), 90)):
            d.text((x + ox, y + oy), txt, font=f, fill=(0, 0, 0, int(a * alpha / 255)))
        d.text((x, y), txt, font=f, fill=(*fill, alpha))
        im.alpha_composite(layer)
        return
    # Special-case trailing ? (Noto HE tofus it)
    if txt.endswith("?") and any(ord(c) > 127 for c in txt[:-1]):
        he = txt[:-1]
        probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        tw, _ = measure_mixed(probe, he, size, bold)
        qf = font(size, bold, False)
        qb = probe.textbbox((0, 0), "?", font=qf)
        qw = qb[2] - qb[0]
        gap = 6
        total = tw + gap + qw
        x0 = (W - total) // 2
        if shadow:
            for ox, oy, a in ((0, shadow, 150), (0, max(1, shadow // 2), 90)):
                layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
                draw_mixed_at(layer, he, x0 + qw + gap + ox, y + oy, size, (0, 0, 0), int(a * alpha / 255), bold)
                ImageDraw.Draw(layer).text((x0 + ox - qb[0], y + oy - qb[1]), "?", font=qf, fill=(0, 0, 0, int(a * alpha / 255)))
                im.alpha_composite(layer)
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        draw_mixed_at(layer, he, x0 + qw + gap, y, size, fill, alpha, bold)
        ImageDraw.Draw(layer).text((x0 - qb[0], y - qb[1]), "?", font=qf, fill=(*fill, alpha))
        im.alpha_composite(layer)
        return
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw, _ = measure_mixed(probe, txt, size, bold)
    x = (W - tw) // 2
    if shadow:
        for ox, oy, a in ((0, shadow, 150), (0, max(1, shadow // 2), 90)):
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
    mix = np.clip(1 - 0.2 * r, 0.75, 1.0)
    arr = np.array(CREAM, np.float32) + (np.array(CREAM2, np.float32) - np.array(CREAM, np.float32)) * mix[:, :, None]
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
    c = max(2, int(5 * scale * pulse))
    d.ellipse([cx - c, cy - c, cx + c, cy + c], fill=(255, 255, 255, a))
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


def kenburns(base, t, zoom0=1.0, zoom1=1.14, pan_y=0.15):
    z = zoom0 + (zoom1 - zoom0) * ease_in_out(t)
    nw, nh = int(W * z), int(H * z)
    im = base.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - W) // 2
    y = int((nh - H) // 2 + pan_y * (nh - H) * 0.25)
    y = max(0, min(y, nh - H))
    return im.crop((x, y, x + W, y + H)).convert("RGBA")


def bottom_scrim(im, top_y=1180, strength=1.0):
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = band.load()
    for y in range(top_y, H):
        u = (y - top_y) / max(1, H - top_y)
        a = int((0.08 + 0.78 * (u ** 1.5)) * 255 * strength)
        for x in range(W):
            px[x, y] = (8, 6, 5, a)
    im.alpha_composite(band.filter(ImageFilter.GaussianBlur(16)))


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
    im.alpha_composite(pill, ((W - pw) // 2, y + int((1 - alpha) * 24)))


def price_block(im, y, alpha=255, large=True):
    if alpha < 8:
        return
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    price, was = f"₪ {PRICE}", f"₪{PRICE_WAS}"
    f_price = font(68 if large else 52, True, False)
    f_was = font(26 if large else 22, True, False)
    bb = d.textbbox((0, 0), price, font=f_price)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x = (W - tw) // 2 - bb[0]
    d.text((x, y + 3), price, font=f_price, fill=(0, 0, 0, int(100 * alpha / 255)))
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
    hook = Image.open(ASSETS / "hook_bg.jpg").convert("RGB")
    hook_z = Image.open(ASSETS / "hook_zoom.jpg").convert("RGB")
    solo = Image.open(ASSETS / "women_solo.png").convert("RGBA")
    bb = solo.getbbox()
    solo = solo.crop(bb) if bb else solo
    sh = 520
    solo = solo.resize((max(1, int(solo.size[0] * sh / solo.size[1])), sh), Image.Resampling.LANCZOS)
    return {
        "hook": hook,
        "hook_z": hook_z,
        "solo": solo,
        "dbl": Image.open(ASSETS / "double_cut.png").convert("RGBA"),
        "left": Image.open(ASSETS / "left_cut.png").convert("RGBA"),
        "right": Image.open(ASSETS / "right_cut.png").convert("RGBA"),
    }


def frame_at(i, A):
    t = i / FPS

    # ---- 0–4.2 SHED-HAND HOOK ----
    if t < 4.2:
        local = t / 4.2
        # crossfade wide → tight zoom into palm
        a = kenburns(A["hook"], min(1.0, local / 0.85), 1.02, 1.12, pan_y=0.12)
        b = kenburns(A["hook_z"], min(1.0, local), 1.0, 1.08, pan_y=0.05)
        mix = ease_in_out(max(0.0, (local - 0.35) / 0.55))
        im = Image.blend(a, b, mix)
        bottom_scrim(im, 1100, 0.95)

        # micro shake on entrance
        shake = max(0.0, 1.0 - t / 0.35) * (1 if int(t * 48) % 2 == 0 else -1)
        ta = int(255 * ease_out(min(1.0, t / 0.22)))
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        text_c(layer, "עוד שיער ביד?", 1280 + int(shake * 3), 56, WHITE, ta, shadow=8)
        im.alpha_composite(layer)
        if ta > 40:
            gold_rule(im, 1370, int(190 * ease_out(min(1.0, (t - 0.2) / 0.25))), ta)

        if t >= 2.4:
            sub = ease_out(min(1.0, (t - 2.4) / 0.28))
            text_c(im, "זה לא סתם", 1420, 36, (250, 240, 220), int(245 * sub), shadow=5)

        if t >= 3.55:
            # Hard cream wipe — clear hand before new copy (no muddy overlap)
            vb = ease_out(min(1.0, (t - 3.55) / 0.22))
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(overlay).rectangle([0, 0, W, H], fill=(245, 240, 232, int(255 * vb)))
            im.alpha_composite(overlay)
            if vb > 0.55:
                text_c(im, "יש קצף שנוח לנשים", 880, 42, INK, int(255 * ((vb - 0.55) / 0.45)), shadow=3)
        return im

    # ---- 4.2–8.0 PRODUCT (solo → double slam) ----
    if t < 8.0:
        local = (t - 4.2) / 3.8
        im = cream_field(0.05 + 0.04 * math.sin(local * math.pi))
        ta = int(255 * ease_out(min(1.0, local / 0.16)))
        text_c(im, "קצף 5% לנשים", 200, 46, INK, ta, shadow=3)
        gold_rule(im, 270, int(150 * ease_out(min(1.0, (local - 0.05) / 0.2))), ta)
        text_c(im, "מריחה אחת ביום · מקורי מארה״ב", 298, 28, MUTED, int(ta * 0.92), bold=False, shadow=2)

        if local < 0.32:
            pop = ease_out_back(min(1.0, max(0.0, local / 0.22)))
            pop_c = max(0.0, min(1.0, pop))
            drift = 1.0 + 0.03 * ease_in_out(max(0, (local - 0.14) / 0.18))
            pack = A["solo"]
            ps = 0.9 + 0.1 * pop_c
            pw = max(1, int(pack.size[0] * ps * drift))
            ph = max(1, int(pack.size[1] * ps * drift))
            pp = pack.resize((pw, ph), Image.Resampling.LANCZOS)
            if pop_c < 1:
                pp = pp.copy()
                pp.putalpha(pp.split()[-1].point(lambda a: int(a * pop_c)))
            px, py = (W - pw) // 2, 420 + int((1 - pop_c) * 90)
            soft_shadow(im, pp, px, py, int(130 * pop_c))
            if pop_c > 0.5:
                im.alpha_composite(reflection(pp, 0.28 * min(1, (pop_c - 0.5) / 0.5)), (px, py + ph - 6))
            im.alpha_composite(pp, (px, py))
            if pop_c > 0.8:
                diagonal_shine(im, px, py, pw, ph, (local - 0.1) / 0.25)
                wink(im, px + int(pw * 0.72), py + 28, (local - 0.14) / 0.18, 1.0)
            # solo-only chips — never claim double here
            chip(im, "פעם ביום", 1180, ease_out(min(1.0, max(0.0, (local - 0.18) / 0.14))), "navy")
            chip(im, "בלי ריח לוואי", 1255, ease_out(min(1.0, max(0.0, (local - 0.24) / 0.14))), "gold")
        else:
            u = (local - 0.32) / 0.68
            left_c = max(0.0, min(1.0, ease_out_back(min(1.0, u / 0.28))))
            right_c = max(0.0, min(1.0, ease_out_back(min(1.0, max(0.0, (u - 0.08) / 0.28)))))
            shake = max(0.0, 1.0 - max(0.0, (u - 0.08) / 0.14)) * right_c
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
            y0 = 390
            lx = x0 - int((1 - left_c) * 70)
            rx = x0 + left.size[0] + gap + int((1 - right_c) * 110)
            soft_shadow(im, left, lx, y0, int(120 * left_c))
            soft_shadow(im, right, rx, y0, int(120 * right_c))
            im.alpha_composite(left, (lx, y0))
            im.alpha_composite(right, (rx, y0))
            if right_c > 0.75:
                diagonal_shine(im, x0, y0, total_w, left.size[1], (u - 0.2) / 0.45)
                wink(im, rx + int(right.size[0] * 0.65), y0 + 24, (u - 0.25) / 0.2, 0.9)

            # double claim ONLY after both boxes landed
            if right_c > 0.85:
                chip(im, "מארז כפול · 8 חודשים", 1120, ease_out(min(1.0, (right_c - 0.85) / 0.15)), "navy")
                chip(im, "מתייבש מהר", 1195, ease_out(min(1.0, max(0.0, (u - 0.45) / 0.15))), "white")
                chip(im, "הכי משתלם", 1270, ease_out(min(1.0, max(0.0, (u - 0.55) / 0.15))), "gold")

        if local > 0.72:
            price_block(im, 1405, int(255 * ease_out(min(1.0, (local - 0.72) / 0.16))), True)

        im = apply_brand_logo(im, t - 4.2, y=36, size=96)
        return im

    # ---- 8.0–11.0 DEDICATED BONUS ----
    if t < 11.0:
        local = (t - 8.0) / 3.0
        im = cream_field(0.08)
        rng = np.random.default_rng(9)
        bub = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        db = ImageDraw.Draw(bub)
        for _ in range(24):
            bx = int(rng.integers(40, W - 40))
            by = int((rng.random() * H + local * 85 * (0.5 + rng.random())) % H)
            br = int(7 + rng.random() * 24)
            db.ellipse([bx - br, by - br, bx + br, by + br], fill=(255, 255, 255, int(14 + rng.random() * 18)))
        im.alpha_composite(bub.filter(ImageFilter.GaussianBlur(1.2)))

        ta = int(255 * ease_out(min(1.0, local / 0.18)))
        text_c(im, "עשרה אחוז נקודות בונוס", 200, 46, INK, ta, shadow=3)
        gold_rule(im, 270, int(180 * ease_out(min(1.0, (local - 0.08) / 0.2))), ta)
        text_c(im, "בנובמבר על כל קנייה", 298, 28, INK, int(ta * 0.95), shadow=2)
        text_c(im, "משלוח חינם עד הבית", 348, 26, MUTED, int(ta * 0.9), bold=False, shadow=2)

        pop = max(0.0, min(1.0, ease_out_back(min(1.0, max(0.0, (local - 0.1) / 0.28)))))
        dbl = A["dbl"]
        ps = 0.78 + 0.12 * pop
        drift = 1.0 + 0.03 * ease_in_out(max(0, (local - 0.4) / 0.6))
        pw = max(1, int(dbl.size[0] * ps * drift))
        ph = max(1, int(dbl.size[1] * ps * drift))
        pp = dbl.resize((pw, ph), Image.Resampling.LANCZOS)
        if pop < 1:
            pp = pp.copy()
            pp.putalpha(pp.split()[-1].point(lambda a: int(a * pop)))
        px, py = (W - pw) // 2, 470 + int((1 - pop) * 80)
        soft_shadow(im, pp, px, py, int(135 * pop))
        if pop > 0.5:
            im.alpha_composite(reflection(pp, 0.3 * min(1, (pop - 0.5) / 0.5)), (px, py + ph - 6))
        im.alpha_composite(pp, (px, py))
        if pop > 0.85:
            diagonal_shine(im, px, py, pw, ph, (local - 0.35) / 0.5)

        if local > 0.4:
            price_block(im, 1220, int(255 * ease_out(min(1.0, (local - 0.4) / 0.18))), False)

        im = apply_brand_logo(im, t - 4.2, y=36, size=96)
        return im

    # ---- 11.0–14.0 CTA ----
    local = (t - 11.0) / 3.0
    im = cream_field(0.07)
    ta = int(255 * ease_out(min(1.0, local / 0.2)))
    text_c(im, "מארז כפול לנשים", 210, 46, INK, ta, shadow=3)
    gold_rule(im, 278, int(150 * ease_out(min(1.0, (local - 0.08) / 0.2))), ta)
    text_c(im, "קצף 5% · 8 חודשים", 305, 30, MUTED, int(ta * 0.95), shadow=2)

    pop = max(0.0, min(1.0, ease_out_back(min(1.0, max(0.0, (local - 0.08) / 0.28)))))
    dbl = A["dbl"]
    ps = 0.78 * (0.92 + 0.08 * pop)
    pw = max(1, int(dbl.size[0] * ps))
    ph = max(1, int(dbl.size[1] * ps))
    pp = dbl.resize((pw, ph), Image.Resampling.LANCZOS)
    if pop < 1:
        pp = pp.copy()
        pp.putalpha(pp.split()[-1].point(lambda a: int(a * pop)))
    px, py = (W - pw) // 2, 390 + int((1 - pop) * 50)
    soft_shadow(im, pp, px, py, int(130 * pop))
    im.alpha_composite(pp, (px, py))
    if pop > 0.8:
        diagonal_shine(im, px, py, pw, ph, (local - 0.25) / 0.5)

    cta_a = ease_out(min(1.0, max(0.0, (local - 0.28) / 0.22)))
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

    im = apply_brand_logo(im, t - 4.2, y=36, size=96)
    return im


def build_cover(A):
    im = kenburns(A["hook"], 0.55, 1.05, 1.05, 0.1)
    bottom_scrim(im, 1050, 1.0)
    text_c(im, "עוד שיער ביד?", 1180, 52, WHITE, 255, shadow=8)
    gold_rule(im, 1270, 180, 255)
    text_c(im, "קצף 5% לנשים · מארז כפול", 1310, 30, (250, 240, 220), 255, shadow=3)
    return im.convert("RGB")


def build_story(A):
    # story = cream product still (afternoon) matching tipot system shift to cream
    im = cream_field(0.1)
    dbl = A["dbl"]
    ps = 0.95
    pw = max(1, int(dbl.size[0] * ps))
    ph = max(1, int(dbl.size[1] * ps))
    pp = dbl.resize((pw, ph), Image.Resampling.LANCZOS)
    px = (W - pw) // 2
    soft_shadow(im, pp, px, 260, 140)
    im.alpha_composite(pp, (px, 260))
    text_c(im, "עוד שיער ביד?", 920, 40, INK, 255, shadow=3)
    text_c(im, "קצף 5% לנשים · מארז כפול", 985, 32, (140, 70, 70), 255, shadow=2)
    price_block(im, 1100, 255, False)
    text_c(im, "minox-shop.co.il", 1680, 26, MUTED, 230, lat=True, shadow=2)
    im = apply_brand_logo(im, 2.0, y=36, size=96)
    return im.convert("RGB")


def write_kit(video_url="", cover_url="", story_url=""):
    (EXPORT / "CAPTION-v4.txt").write_text(
        f"""עוד שיער ביד?

קצף Rogaine 5% לנשים — מריחה אחת ביום, בלי ריח לוואי.
מארז כפול ל־8 חודשים · ₪{PRICE} (חיסכון ₪{PRICE_SAVE})
בנובמבר: 10% נקודות בונוס + משלוח חינם עד הבית.

{PRODUCT_URL}

#מינוקסידיל #Rogaine #נשירתשיער #MinoxShop #קצף
""".strip()
        + "\n",
        encoding="utf-8",
    )
    links = ""
    if video_url:
        links = f"\nהורדות:\n- Video: {video_url}\n- Cover: {cover_url}\n- Story: {story_url}\n"
    (EXPORT / "UPLOAD-v4.txt").write_text(
        f"""ריל v4 — shed-hand hook + cream men-level offer
{links}
קבצים:
- MinoxShop-WOMEN-foam-double-v4-14s.mp4
- MinoxShop-WOMEN-foam-double-v4-COVER.jpg
- MinoxShop-WOMEN-foam-double-STORY-afternoon-v4.jpg

קו: עוד שיער ביד? → זה לא סתם → קצף 5% לנשים → כפול 8 חודשים → הזמיני עכשיו
לינק: {PRODUCT_URL}
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
            f"[1:a]afade=t=in:st=0:d=0.45,afade=t=out:st={DURATION-0.7}:d=0.7,volume=0.52,atrim=0:{DURATION}[a]",
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
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
            "-an", "-movflags", "+faststart", str(out),
        ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main():
    A = load_assets()
    print(f"render {N}")
    qa = {0, int(1.2 * FPS), int(2.8 * FPS), int(5.0 * FPS), int(7.0 * FPS), int(9.0 * FPS), int(12.0 * FPS), N - 1}
    for i in range(N):
        fr = frame_at(i, A)
        fr.convert("RGB").save(FRAMES / f"f_{i:04d}.jpg", quality=93, optimize=True)
        if i in qa:
            fr.convert("RGB").save(WORK / "qa" / f"qa_{i:04d}.jpg", quality=92)
        if i % 60 == 0:
            print(f"  {i}/{N}")

    cover = build_cover(A)
    story = build_story(A)
    cover.save(EXPORT / "MinoxShop-WOMEN-foam-double-v4-COVER.jpg", quality=94, optimize=True)
    story.save(EXPORT / "MinoxShop-WOMEN-foam-double-STORY-afternoon-v4.jpg", quality=94, optimize=True)
    out = EXPORT / "MinoxShop-WOMEN-foam-double-v4-14s.mp4"
    encode(out)
    write_kit()
    shutil.copy(out, WORK / "recording_demo.mp4")
    # keep hook asset in exports for reuse
    shutil.copy(ASSETS / "shed_hand.jpg", EXPORT / "women-shed-hand-hook.jpg")
    print("DONE", out)


if __name__ == "__main__":
    main()
