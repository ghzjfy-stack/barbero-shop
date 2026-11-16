#!/usr/bin/env python3
"""Women Rogaine 5% foam DOUBLE v5 — shed tension ladder + product ONCE.

Owner: loved shed-hand only; rest repeating/boring. Needs tense scary
escalation + image variety so people don't drop after first frame.
Beat: hand → pillow → brush → parting → double pack once → CTA.
"""
from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

sys.path.insert(0, "/tmp/women-foam-v5")
from brand_logo import apply_brand_logo

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "exports" / "women-foam-double"
WORK = Path("/tmp/women-foam-v5")
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
PRICE, PRICE_WAS, PRICE_SAVE = 758, 998, 240
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


def text_c(im, txt, y, size, fill, alpha=255, bold=True, shadow=6, lat=False):
    if alpha < 8:
        return
    if lat:
        f = font(size, bold, False)
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        bb = d.textbbox((0, 0), txt, font=f)
        x = (W - (bb[2] - bb[0])) // 2 - bb[0]
        for ox, oy, a in ((0, shadow, 160), (0, max(1, shadow // 2), 100)):
            d.text((x + ox, y + oy), txt, font=f, fill=(0, 0, 0, int(a * alpha / 255)))
        d.text((x, y), txt, font=f, fill=(*fill, alpha))
        im.alpha_composite(layer)
        return
    if txt.endswith("?") and any(ord(c) > 127 for c in txt[:-1]):
        # Keep "?" glued on the visual left of Hebrew (no gap that reads as " ביד ?")
        he = txt[:-1].rstrip()
        probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        tw, _ = measure_mixed(probe, he, size, bold)
        qf = font(size, bold, False)
        qb = probe.textbbox((0, 0), "?", font=qf)
        qw = qb[2] - qb[0]
        gap = 0
        total = tw + gap + qw
        x0 = (W - total) // 2
        if shadow:
            for ox, oy, a in ((0, shadow, 160), (0, max(1, shadow // 2), 100)):
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
        for ox, oy, a in ((0, shadow, 160), (0, max(1, shadow // 2), 100)):
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
    d.ellipse((-200, 1000, 560, 1800), fill=(255, 220, 180, 22))
    return Image.alpha_composite(im, wash.filter(ImageFilter.GaussianBlur(70)))


def gold_rule(im, y, width, alpha=255):
    if width < 4 or alpha < 8:
        return
    ImageDraw.Draw(im).rounded_rectangle([(W - width) // 2, y, (W + width) // 2, y + 4], 2, fill=GOLD + (alpha,))


def soft_shadow(c, box, x, y, a=120):
    sh = Image.new("RGBA", (box.size[0] + 70, 64), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([10, 16, box.size[0] + 55, 46], fill=(30, 22, 14, int(a * 0.55)))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (x - 35, y + box.size[1] - 10))


def reflection(p, op=0.28, frac=0.3):
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
    return f.filter(ImageFilter.GaussianBlur(3.2))


def diagonal_shine(im, x, y, w, h, phase):
    u = max(0.0, min(1.0, phase))
    if u <= 0.02 or u >= 0.98:
        return
    band_w = max(40, int(w * 0.2))
    band = Image.new("RGBA", (band_w, h), (0, 0, 0, 0))
    px = band.load()
    for i in range(band_w):
        a = int(55 * math.sin(math.pi * i / max(1, band_w - 1)))
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


def kenburns(base, t, zoom0=1.0, zoom1=1.16, pan_y=0.1):
    z = zoom0 + (zoom1 - zoom0) * ease_in_out(max(0.0, min(1.0, t)))
    nw, nh = int(W * z), int(H * z)
    im = base.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - W) // 2
    y = int((nh - H) // 2 + pan_y * (nh - H) * 0.3)
    y = max(0, min(y, nh - H))
    return im.crop((x, y, x + W, y + H)).convert("RGBA")


def bottom_scrim(im, top_y=1200, strength=1.0):
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = band.load()
    for y in range(top_y, H):
        u = (y - top_y) / max(1, H - top_y)
        a = int((0.1 + 0.82 * (u ** 1.45)) * 255 * strength)
        for x in range(W):
            px[x, y] = (6, 4, 4, a)
    im.alpha_composite(band.filter(ImageFilter.GaussianBlur(14)))


def flash_cut(im, amount):
    if amount < 0.02:
        return
    flash = Image.new("RGBA", (W, H), (255, 255, 255, int(210 * amount)))
    im.alpha_composite(flash)


def tension_beat(base, local, line, zoom0, zoom1, pan_y, cold=0.0):
    """One shed-tension beat with hard text pop + ken burns."""
    im = kenburns(base, local, zoom0, zoom1, pan_y)
    if cold > 0:
        # slight cool desat for dread
        arr = np.array(im).astype(np.float32)
        gray = arr.mean(axis=2, keepdims=True)
        arr = arr * (1 - 0.25 * cold) + gray * (0.25 * cold)
        arr[:, :, 2] = np.clip(arr[:, :, 2] + 8 * cold, 0, 255)
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    bottom_scrim(im, 1180, 1.0)
    # entrance flash
    flash_cut(im, max(0.0, 1.0 - local / 0.12) * 0.55)
    shake = max(0.0, 1.0 - local / 0.28) * (1 if int(local * 50) % 2 == 0 else -1)
    a = int(255 * ease_out(min(1.0, local / 0.18)))
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    text_c(layer, line, 1320 + int(shake * 4), 52, WHITE, a, shadow=8)
    im.alpha_composite(layer)
    if a > 40:
        gold_rule(im, 1410, int(170 * ease_out(min(1.0, (local - 0.15) / 0.22))), a)
    return im


def load_assets():
    return {
        "hand": Image.open(ASSETS / "b0_hand.jpg").convert("RGB"),
        "pillow": Image.open(ASSETS / "b1_pillow.jpg").convert("RGB"),
        "brush": Image.open(ASSETS / "b2_brush.jpg").convert("RGB"),
        "part": Image.open(ASSETS / "b3_part.jpg").convert("RGB"),
        "dbl": Image.open(ASSETS / "double_cut.png").convert("RGBA"),
    }


def frame_at(i, A):
    t = i / FPS

    # ---- TENSION LADDER (majority of runtime) ----
    # 0.0–2.4 hand
    if t < 2.4:
        return tension_beat(A["hand"], t / 2.4, "עוד שיער ביד?", 1.02, 1.14, 0.12, cold=0.05)
    # 2.4–4.6 pillow
    if t < 4.6:
        return tension_beat(A["pillow"], (t - 2.4) / 2.2, "גם על הכרית", 1.04, 1.18, -0.08, cold=0.18)
    # 4.6–6.8 brush
    if t < 6.8:
        return tension_beat(A["brush"], (t - 4.6) / 2.2, "כל יום יותר", 1.06, 1.2, 0.05, cold=0.28)
    # 6.8–9.2 parting / scalp
    if t < 9.2:
        return tension_beat(A["part"], (t - 6.8) / 2.4, "הקרקפת כבר נראית", 1.05, 1.22, -0.1, cold=0.35)

    # ---- 9.2–12.2 PRODUCT ONCE (double only) ----
    if t < 12.2:
        local = (t - 9.2) / 3.0
        # whip into cream
        im = cream_field(0.06 + 0.03 * math.sin(local * math.pi))
        if local < 0.12:
            flash_cut(im, 1.0 - local / 0.12)

        ta = int(255 * ease_out(min(1.0, max(0.0, (local - 0.08) / 0.18))))
        text_c(im, "קצף 5% לנשים", 200, 46, INK, ta, shadow=3)
        gold_rule(im, 270, int(150 * ease_out(min(1.0, max(0.0, (local - 0.12) / 0.2)))), ta)
        text_c(im, "מארז כפול · 8 חודשים", 300, 30, MUTED, int(ta * 0.95), shadow=2)

        pop = max(0.0, min(1.0, ease_out_back(min(1.0, max(0.0, (local - 0.12) / 0.3)))))
        dbl = A["dbl"]
        drift = 1.0 + 0.035 * ease_in_out(max(0, (local - 0.4) / 0.6))
        ps = (0.88 + 0.12 * pop) * drift
        pw = max(1, int(dbl.size[0] * ps))
        ph = max(1, int(dbl.size[1] * ps))
        pp = dbl.resize((pw, ph), Image.Resampling.LANCZOS)
        if pop < 1:
            pp = pp.copy()
            pp.putalpha(pp.split()[-1].point(lambda a: int(a * pop)))
        px = (W - pw) // 2
        py = 430 + int((1 - pop) * 90)
        soft_shadow(im, pp, px, py, int(140 * pop))
        if pop > 0.5:
            im.alpha_composite(reflection(pp, 0.3 * min(1, (pop - 0.5) / 0.5)), (px, py + ph - 6))
        im.alpha_composite(pp, (px, py))
        if pop > 0.8:
            diagonal_shine(im, px, py, pw, ph, (local - 0.35) / 0.5)

        # one price hit late — still same screen, not a new pack shot
        if local > 0.55:
            pa = int(255 * ease_out(min(1.0, (local - 0.55) / 0.18)))
            # compact price
            layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            price = f"₪ {PRICE}"
            was = f"₪{PRICE_WAS}"
            f_price = font(58, True, False)
            f_was = font(24, True, False)
            bb = d.textbbox((0, 0), price, font=f_price)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            x = (W - tw) // 2 - bb[0]
            d.text((x, 1260 + 3), price, font=f_price, fill=(0, 0, 0, int(90 * pa / 255)))
            d.text((x, 1260), price, font=f_price, fill=(*INK, pa))
            wb = d.textbbox((0, 0), was, font=f_was)
            ww = wb[2] - wb[0]
            wx = (W - ww) // 2 - wb[0]
            d.text((wx, 1260 + th + 14), was, font=f_was, fill=(120, 124, 136, int(pa * 0.85)))
            mid = 1260 + th + 14 + (wb[3] - wb[1]) // 2 + 2
            d.line([(wx - 2, mid), (wx + ww + 2, mid)], fill=(120, 124, 136, int(pa * 0.9)), width=3)
            im.alpha_composite(layer)
            # save pill
            he, amt = "חיסכון", f"₪{PRICE_SAVE}"
            f_he, f_amt = font(22, True, True), font(22, True, False)
            hb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), he, font=f_he, language="he")
            ab = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), amt, font=f_amt)
            hw, hh = hb[2] - hb[0], hb[3] - hb[1]
            aw, ah = ab[2] - ab[0], ab[3] - ab[1]
            pad_x, pad_y, gap = 18, 10, 10
            pill_w = aw + gap + hw + pad_x * 2
            pill_h = max(hh, ah) + pad_y * 2
            pill = Image.new("RGBA", (pill_w, pill_h), (0, 0, 0, 0))
            ImageDraw.Draw(pill).rounded_rectangle([0, 0, pill_w - 1, pill_h - 1], pill_h // 2, fill=NAVY + (int(235 * pa / 255),))
            ImageDraw.Draw(pill).text((pad_x - ab[0], (pill_h - ah) // 2 - ab[1]), amt, font=f_amt, fill=(255, 255, 255, pa))
            ImageDraw.Draw(pill).text(
                (pad_x + aw + gap - hb[0], (pill_h - hh) // 2 - hb[1]), he, font=f_he, fill=(255, 255, 255, pa), language="he"
            )
            im.alpha_composite(pill, ((W - pill_w) // 2, 1260 + th + 44))

        im = apply_brand_logo(im, t - 9.2, y=36, size=96)
        return im

    # ---- 12.2–14.0 CTA (same double hold, no new pack collage) ----
    local = (t - 12.2) / 1.8
    im = cream_field(0.07)
    ta = int(255 * ease_out(min(1.0, local / 0.2)))
    text_c(im, "די לנשירה הזאת", 220, 42, INK, ta, shadow=3)
    gold_rule(im, 285, int(160 * ease_out(min(1.0, (local - 0.08) / 0.2))), ta)

    dbl = A["dbl"]
    ps = 0.72
    pw = max(1, int(dbl.size[0] * ps))
    ph = max(1, int(dbl.size[1] * ps))
    pp = dbl.resize((pw, ph), Image.Resampling.LANCZOS)
    px, py = (W - pw) // 2, 380
    soft_shadow(im, pp, px, py, 120)
    im.alpha_composite(pp, (px, py))

    cta_a = ease_out(min(1.0, max(0.0, (local - 0.15) / 0.22)))
    if cta_a > 0.05:
        pulse = 1.0 + 0.045 * math.sin(max(0, local - 0.2) * math.pi * 2.2)
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
        im.alpha_composite(btn, ((W - pw2) // 2, 1120 + int((1 - cta_a) * 12)))
        text_c(im, "minox-shop.co.il", 1220, 26, MUTED, int(230 * cta_a), lat=True, shadow=2)
        text_c(im, "תוצאות משתנות בין אנשים", 1500, 18, (120, 124, 136), int(145 * cta_a), bold=False, shadow=1)

    im = apply_brand_logo(im, t - 9.2, y=36, size=96)
    return im


def build_cover(A):
    im = kenburns(A["hand"], 0.5, 1.08, 1.08, 0.1)
    bottom_scrim(im, 1100, 1.0)
    text_c(im, "עוד שיער ביד?", 1220, 52, WHITE, 255, shadow=8)
    gold_rule(im, 1310, 180, 255)
    text_c(im, "קצף 5% לנשים", 1350, 30, (250, 240, 220), 255, shadow=3)
    return im.convert("RGB")


def build_story(A):
    # afternoon story uses tension cover energy + product once
    im = cream_field(0.1)
    dbl = A["dbl"]
    ps = 0.92
    pw = max(1, int(dbl.size[0] * ps))
    ph = max(1, int(dbl.size[1] * ps))
    pp = dbl.resize((pw, ph), Image.Resampling.LANCZOS)
    px = (W - pw) // 2
    soft_shadow(im, pp, px, 280, 140)
    im.alpha_composite(pp, (px, 280))
    text_c(im, "עוד שיער ביד?", 960, 42, INK, 255, shadow=3)
    text_c(im, "קצף 5% לנשים · מארז כפול", 1030, 30, (140, 70, 70), 255, shadow=2)
    text_c(im, f"₪ {PRICE}", 1120, 52, INK, 255, lat=True, shadow=2)
    text_c(im, "minox-shop.co.il", 1680, 26, MUTED, 230, lat=True, shadow=2)
    im = apply_brand_logo(im, 2.0, y=36, size=96)
    return im.convert("RGB")


def write_kit(v="", c="", s=""):
    links = f"\nהורדות:\n- Video: {v}\n- Cover: {c}\n- Story: {s}\n" if v else "\n"
    (EXPORT / "CAPTION-v5.txt").write_text(
        f"""עוד שיער ביד?
גם על הכרית.
כל יום יותר.
הקרקפת כבר נראית.

קצף Rogaine 5% לנשים · מארז כפול ל־8 חודשים · ₪{PRICE}
הזמיני עכשיו
{PRODUCT_URL}

#מינוקסידיל #Rogaine #נשירתשיער #MinoxShop #קצף
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (EXPORT / "UPLOAD-v5.txt").write_text(
        f"""ריל v5 — סולם נשירה מותח + מוצר פעם אחת
{links}
קו:
יד → כרית → מברשת → קרקפת → כפול פעם אחת → הזמיני עכשיו

קבצים:
- MinoxShop-WOMEN-foam-double-v5-14s.mp4
- MinoxShop-WOMEN-foam-double-v5-COVER.jpg
- MinoxShop-WOMEN-foam-double-STORY-afternoon-v5.jpg
""".strip()
        + "\n",
        encoding="utf-8",
    )


def encode(out: Path):
    bed = WORK / "bed_fun.wav"
    if not bed.exists():
        bed = WORK / "bed_soft.wav"
    # slightly darker/lower bed under tension
    if bed.exists():
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", str(FRAMES / "f_%04d.jpg"),
            "-i", str(bed),
            "-filter_complex",
            f"[1:a]afade=t=in:st=0:d=0.4,afade=t=out:st={DURATION-0.7}:d=0.7,volume=0.48,atrim=0:{DURATION},asetrate=44100*0.97,aresample=44100[a]",
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
    qa = {0, int(1.2 * FPS), int(3.5 * FPS), int(5.5 * FPS), int(7.8 * FPS), int(10.5 * FPS), int(13.0 * FPS), N - 1}
    for i in range(N):
        fr = frame_at(i, A)
        fr.convert("RGB").save(FRAMES / f"f_{i:04d}.jpg", quality=93, optimize=True)
        if i in qa:
            fr.convert("RGB").save(WORK / "qa" / f"qa_{i:04d}.jpg", quality=92)
        if i % 60 == 0:
            print(f"  {i}/{N}")

    cover = build_cover(A)
    story = build_story(A)
    cover.save(EXPORT / "MinoxShop-WOMEN-foam-double-v5-COVER.jpg", quality=94, optimize=True)
    story.save(EXPORT / "MinoxShop-WOMEN-foam-double-STORY-afternoon-v5.jpg", quality=94, optimize=True)
    out = EXPORT / "MinoxShop-WOMEN-foam-double-v5-14s.mp4"
    encode(out)
    write_kit()
    shutil.copy(out, WORK / "recording_demo.mp4")
    for name in ("shed_hand.jpg", "pillow.jpg", "brush.jpg", "part.jpg"):
        src = ASSETS / name
        if src.exists():
            shutil.copy(src, EXPORT / f"women-v5-{name}")
    print("DONE", out)


if __name__ == "__main__":
    main()
