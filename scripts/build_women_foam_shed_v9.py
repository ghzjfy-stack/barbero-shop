#!/usr/bin/env python3
"""Women Rogaine 5% foam DOUBLE v9 — gentle final polish (don't break v8).

Keep v8 Hebrew / club clarity / logo clearance. Only:
1) sharper tension beat cuts + snappier text pop
2) stagger offer: price first, club a beat later
3) light continuous float + shine on product (less catalog-static)

Beat: hand → pillow → brush → scalp → hope → double+price+club → CTA.
"""
from __future__ import annotations

import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

sys.path.insert(0, "/tmp/women-foam-v9")
from brand_logo import apply_brand_logo

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "exports" / "women-foam-double"
WORK = Path("/tmp/women-foam-v9")
FRAMES = WORK / "frames"
ASSETS = WORK / "assets"
EXPORT.mkdir(parents=True, exist_ok=True)
FRAMES.mkdir(parents=True, exist_ok=True)
(WORK / "qa").mkdir(parents=True, exist_ok=True)

W, H, FPS = 1080, 1920, 30
DURATION = 16.0
N = int(DURATION * FPS)

# Hebrew notes
# scalp: «רואים כבר את הקרקפת» — plain Israeli speech, not clinical passive
# club: spoken «עשרה אחוז» (no latin % tofu), names מועדון + נובמבר + משלוח חינם

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


def blend_rgba(a, b, t):
    t = max(0.0, min(1.0, t))
    aa = np.array(a.convert("RGBA"), dtype=np.float32)
    bb = np.array(b.convert("RGBA"), dtype=np.float32)
    out = aa * (1 - t) + bb * t
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def tension_beat(base, local, line, zoom0, zoom1, pan_y, cold=0.0):
    """One shed-tension beat — sharper cut-in than v8, same visuals/copy."""
    im = kenburns(base, local, zoom0, zoom1, pan_y)
    if cold > 0:
        arr = np.array(im).astype(np.float32)
        gray = arr.mean(axis=2, keepdims=True)
        arr = arr * (1 - 0.25 * cold) + gray * (0.25 * cold)
        arr[:, :, 2] = np.clip(arr[:, :, 2] + 8 * cold, 0, 255)
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    bottom_scrim(im, 1180, 1.0)
    # snappier white hit on cut (was 0.12 → 0.06)
    flash_cut(im, max(0.0, 1.0 - local / 0.06) * 0.7)
    shake = max(0.0, 1.0 - local / 0.16) * (1 if int(local * 60) % 2 == 0 else -1)
    # text snaps in faster (was 0.18 → 0.09)
    a = int(255 * ease_out(min(1.0, local / 0.09)))
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    text_c(layer, line, 1320 + int(shake * 5), 52, WHITE, a, shadow=8)
    im.alpha_composite(layer)
    if a > 40:
        gold_rule(im, 1410, int(170 * ease_out(min(1.0, (local - 0.08) / 0.14))), a)
    return im


def soft_chip(im, txt, y, alpha, fill_bg, fill_txt, size=24):
    if alpha < 0.05:
        return
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw, th = measure_mixed(probe, txt, size, True)
    pw, ph = tw + 48, th + 22
    pill = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle([0, 0, pw - 1, ph - 1], ph // 2, fill=fill_bg + (int(235 * alpha),))
    draw_mixed_at(pill, txt, 24, 11, size, fill_txt, int(255 * alpha), True)
    im.alpha_composite(pill, ((W - pw) // 2, y + int((1 - alpha) * 18)))


def pretty_price(im, y, alpha=255):
    """Bigger price + was on one visual row + save pill with breathing room."""
    if alpha < 8:
        return y
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    price, was = f"₪{PRICE}", f"₪{PRICE_WAS}"
    f_price = font(72, True, False)
    f_was = font(28, True, False)
    bb = d.textbbox((0, 0), price, font=f_price)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    wb = d.textbbox((0, 0), was, font=f_was)
    ww, wh = wb[2] - wb[0], wb[3] - wb[1]
    gap = 28
    total = tw + gap + ww
    x0 = (W - total) // 2
    # current
    d.text((x0 - bb[0], y + 4), price, font=f_price, fill=(0, 0, 0, int(90 * alpha / 255)))
    d.text((x0 - bb[0], y), price, font=f_price, fill=(*INK, alpha))
    # was — vertically centered to price baseline
    wx = x0 + tw + gap - wb[0]
    wy = y + max(0, (th - wh) // 2 + 8)
    d.text((wx, wy), was, font=f_was, fill=(130, 134, 146, int(alpha * 0.88)))
    mid = wy + wh // 2 + 2
    d.line([(wx - 2, mid), (wx + ww + 2, mid)], fill=(130, 134, 146, int(alpha * 0.92)), width=3)
    im.alpha_composite(layer)

    he, amt = "חיסכון", f"₪{PRICE_SAVE}"
    f_he, f_amt = font(24, True, True), font(24, True, False)
    hb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), he, font=f_he, language="he")
    ab = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), amt, font=f_amt)
    hw, hh = hb[2] - hb[0], hb[3] - hb[1]
    aw, ah = ab[2] - ab[0], ab[3] - ab[1]
    pad_x, pad_y, gap2 = 22, 12, 12
    pill_w = aw + gap2 + hw + pad_x * 2
    pill_h = max(hh, ah) + pad_y * 2
    pill = Image.new("RGBA", (pill_w, pill_h), (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle([0, 0, pill_w - 1, pill_h - 1], pill_h // 2, fill=NAVY + (int(240 * alpha / 255),))
    ImageDraw.Draw(pill).text((pad_x - ab[0], (pill_h - ah) // 2 - ab[1]), amt, font=f_amt, fill=(255, 255, 255, alpha))
    ImageDraw.Draw(pill).text(
        (pad_x + aw + gap2 - hb[0], (pill_h - hh) // 2 - hb[1]), he, font=f_he, fill=(255, 255, 255, alpha), language="he"
    )
    sy = y + th + 28
    im.alpha_composite(pill, ((W - pill_w) // 2, sy))
    return sy + pill_h


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

    # ---- TENSION ----
    if t < 2.2:
        return tension_beat(A["hand"], t / 2.2, "עוד שיער ביד?", 1.02, 1.14, 0.12, cold=0.05)
    if t < 4.2:
        return tension_beat(A["pillow"], (t - 2.2) / 2.0, "גם בבוקר על הכרית", 1.04, 1.18, -0.08, cold=0.18)
    if t < 6.2:
        return tension_beat(A["brush"], (t - 4.2) / 2.0, "כל סירוק יותר", 1.06, 1.2, 0.05, cold=0.28)
    # plain speech — not clinical passive
    if t < 8.3:
        return tension_beat(A["part"], (t - 6.2) / 2.1, "רואים כבר את הקרקפת", 1.05, 1.22, -0.1, cold=0.35)

    # ---- hope bridge ----
    if t < 9.2:
        local = (t - 8.3) / 0.9
        dark = kenburns(A["part"], 0.95, 1.05, 1.22, -0.1)
        arr = np.array(dark).astype(np.float32)
        gray = arr.mean(axis=2, keepdims=True)
        arr = arr * 0.65 + gray * 0.35
        arr[:, :, 2] = np.clip(arr[:, :, 2] + 12, 0, 255)
        dark = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
        bottom_scrim(dark, 1100, 1.0)
        cream = cream_field(0.05)
        im = blend_rgba(dark, cream, ease_in_out(local))
        ba = int(255 * ease_out(min(1.0, max(0.0, (local - 0.1) / 0.3))))
        if ba > 20:
            pill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(pill).rounded_rectangle(
                [140, 1220, W - 140, 1420], 28, fill=(12, 16, 24, int(110 * ba / 255))
            )
            im.alpha_composite(pill)
        text_c(im, "אפשר לעצור את זה", 1280, 48, WHITE, ba, shadow=6)
        if ba > 40:
            gold_rule(im, 1370, int(190 * ease_out(min(1.0, (local - 0.18) / 0.3))), ba)
        return im

    # ---- PRODUCT ONCE + staggered price then club ----
    if t < 13.3:
        local = (t - 9.2) / 4.1
        im = cream_field(0.06 + 0.025 * math.sin(local * math.pi))
        if local < 0.06:
            flash_cut(im, (1.0 - local / 0.06) * 0.22)

        ta = int(255 * ease_out(min(1.0, max(0.0, (local - 0.03) / 0.14))))
        text_c(im, "קצף 5% לנשים", 210, 46, INK, ta, shadow=3)
        gold_rule(im, 278, int(160 * ease_out(min(1.0, max(0.0, (local - 0.06) / 0.16)))), ta)
        text_c(im, "מארז כפול ל־8 חודשים", 308, 30, MUTED, int(ta * 0.95), shadow=2)
        # trust chips stagger slightly so screen doesn't dump all at once
        tr1 = ease_out(min(1.0, max(0.0, (local - 0.12) / 0.14)))
        tr2 = ease_out(min(1.0, max(0.0, (local - 0.22) / 0.14)))
        soft_chip(im, "מריחה אחת ביום", 352, tr1, (255, 255, 255), (120, 70, 70), 24)
        soft_chip(im, "בלי ריח לוואי", 410, tr2, (255, 252, 246), (120, 70, 70), 22)

        pop = max(0.0, min(1.0, ease_out_back(min(1.0, max(0.0, (local - 0.1) / 0.26)))))
        dbl = A["dbl"]
        # gentle continuous float — alive, not catalog-stuck
        float_y = int(7 * math.sin(max(0.0, local - 0.25) * math.pi * 2.0))
        breathe = 1.0 + 0.018 * math.sin(max(0.0, local - 0.3) * math.pi * 1.6)
        ps = (0.82 + 0.1 * pop) * breathe
        pw = max(1, int(dbl.size[0] * ps))
        ph = max(1, int(dbl.size[1] * ps))
        pp = dbl.resize((pw, ph), Image.Resampling.LANCZOS)
        if pop < 1:
            pp = pp.copy()
            pp.putalpha(pp.split()[-1].point(lambda a: int(a * pop)))
        px = (W - pw) // 2
        py = 460 + int((1 - pop) * 60) + float_y
        soft_shadow(im, pp, px, py, int(150 * pop))
        if pop > 0.5:
            im.alpha_composite(reflection(pp, 0.3 * min(1, (pop - 0.5) / 0.5)), (px, py + ph - 6))
        im.alpha_composite(pp, (px, py))
        if pop > 0.75:
            # looping soft shine instead of one-shot
            shine_phase = (local * 1.15) % 1.0
            diagonal_shine(im, px, py, pw, ph, shine_phase)

        # PRICE first (hold a beat alone) — then club
        if local > 0.38:
            pa = int(255 * ease_out(min(1.0, (local - 0.38) / 0.14)))
            bottom = pretty_price(im, 1160, pa)
            if local > 0.62:
                ca = ease_out(min(1.0, (local - 0.62) / 0.14))
                cy = bottom + 28
                text_c(im, "עשרה אחוז בונוס בנוסף", cy, 28, INK, int(255 * ca), shadow=2)
                # line-by-line stagger so it doesn't feel like a slide dump
                if local > 0.70:
                    c2 = ease_out(min(1.0, (local - 0.70) / 0.12))
                    text_c(im, "לנקודות על הקנייה", cy + 40, 26, INK, int(245 * c2), shadow=2)
                if local > 0.78:
                    c3 = ease_out(min(1.0, (local - 0.78) / 0.12))
                    text_c(im, "במועדון בנובמבר", cy + 80, 26, (140, 100, 55), int(245 * c3), shadow=2)
                if local > 0.86:
                    c4 = ease_out(min(1.0, (local - 0.86) / 0.12))
                    text_c(im, "משלוח חינם עד הבית", cy + 120, 24, MUTED, int(230 * c4), bold=False, shadow=1)

        im = apply_brand_logo(im, t - 9.2, y=28, size=72)
        return im

    # ---- CTA ----
    local = (t - 13.3) / 2.7
    im = cream_field(0.07)
    ta = int(255 * ease_out(min(1.0, local / 0.16)))
    text_c(im, "זה לא חייב להמשיך", 220, 44, INK, ta, shadow=3)
    gold_rule(im, 288, int(180 * ease_out(min(1.0, (local - 0.05) / 0.16))), ta)
    text_c(im, "בונוס בנוסף לנקודות על הקנייה", 320, 26, (140, 100, 55), int(ta * 0.95), shadow=2)

    dbl = A["dbl"]
    ps = 0.68
    pw = max(1, int(dbl.size[0] * ps))
    ph = max(1, int(dbl.size[1] * ps))
    pp = dbl.resize((pw, ph), Image.Resampling.LANCZOS)
    # tiny float on CTA pack too
    float_y = int(5 * math.sin(local * math.pi * 2.0))
    px, py = (W - pw) // 2, 370 + float_y
    soft_shadow(im, pp, px, py, 120)
    im.alpha_composite(pp, (px, py))
    if local > 0.1:
        diagonal_shine(im, px, py, pw, ph, (local * 0.9) % 1.0)

    cta_a = ease_out(min(1.0, max(0.0, (local - 0.18) / 0.2)))
    if cta_a > 0.05:
        pulse = 1.0 + 0.04 * math.sin(max(0, local - 0.22) * math.pi * 2.1)
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
        text_c(im, "תוצאות משתנות מאישה לאישה", 1520, 18, (120, 124, 136), int(145 * cta_a), bold=False, shadow=1)

    im = apply_brand_logo(im, t - 9.2, y=28, size=72)
    return im


def build_cover(A):
    im = kenburns(A["hand"], 0.5, 1.08, 1.08, 0.1)
    bottom_scrim(im, 1100, 1.0)
    text_c(im, "עוד שיער ביד?", 1220, 52, WHITE, 255, shadow=8)
    gold_rule(im, 1310, 180, 255)
    text_c(im, "קצף 5% לנשים", 1350, 30, (250, 240, 220), 255, shadow=3)
    return im.convert("RGB")


def build_story(A):
    im = cream_field(0.1)
    dbl = A["dbl"]
    ps = 0.88
    pw = max(1, int(dbl.size[0] * ps))
    ph = max(1, int(dbl.size[1] * ps))
    pp = dbl.resize((pw, ph), Image.Resampling.LANCZOS)
    px = (W - pw) // 2
    soft_shadow(im, pp, px, 280, 140)
    im.alpha_composite(pp, (px, 280))
    text_c(im, "עוד שיער ביד?", 940, 42, INK, 255, shadow=3)
    text_c(im, "עשרה אחוז בונוס בנוסף לנקודות", 1010, 26, (140, 100, 55), 255, shadow=2)
    text_c(im, f"₪{PRICE}", 1100, 56, INK, 255, lat=True, shadow=2)
    text_c(im, "minox-shop.co.il", 1680, 26, MUTED, 230, lat=True, shadow=2)
    im = apply_brand_logo(im, 2.0, y=28, size=72)
    return im.convert("RGB")


def write_kit(v="", c="", s=""):
    links = f"\nהורדות:\n- Video: {v}\n- Cover: {c}\n- Story: {s}\n" if v else "\n"
    (EXPORT / "CAPTION-v9.txt").write_text(
        f"""עוד שיער ביד?
גם בבוקר על הכרית.
כל סירוק יותר.
רואים כבר את הקרקפת.

אפשר לעצור את זה.
קצף Rogaine 5% לנשים — מריחה אחת ביום ובלי ריח לוואי.
מארז כפול ל־8 חודשים · ₪{PRICE} (חיסכון ₪{PRICE_SAVE})
בנובמבר במועדון: עשרה אחוז בונוס בנוסף לנקודות על הקנייה + משלוח חינם עד הבית.

זה לא חייב להמשיך.
הזמיני עכשיו
{PRODUCT_URL}

#מינוקסידיל #Rogaine #נשירתשיער #MinoxShop #קצף #מועדון
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (EXPORT / "UPLOAD-v9.txt").write_text(
        f"""ריל v9 — ליטוש עדין: חיתוכים חדים + מחיר לפני מועדון + float על מוצר
{links}
קו:
אותו סיפור כמו v8 — בלי לשבור עברית/מועדון/לוגו

קבצים:
- MinoxShop-WOMEN-foam-double-v9-16s.mp4
- MinoxShop-WOMEN-foam-double-v9-COVER.jpg
- MinoxShop-WOMEN-foam-double-STORY-afternoon-v9.jpg
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
    qa = {
        0,
        int(1.1 * FPS),
        int(3.2 * FPS),
        int(5.2 * FPS),
        int(7.2 * FPS),
        int(8.7 * FPS),
        int(11.2 * FPS),
        int(12.5 * FPS),
        int(14.5 * FPS),
        N - 1,
    }
    for i in range(N):
        fr = frame_at(i, A)
        fr.convert("RGB").save(FRAMES / f"f_{i:04d}.jpg", quality=93, optimize=True)
        if i in qa:
            fr.convert("RGB").save(WORK / "qa" / f"qa_{i:04d}.jpg", quality=92)
        if i % 60 == 0:
            print(f"  {i}/{N}")

    cover = build_cover(A)
    story = build_story(A)
    cover.save(EXPORT / "MinoxShop-WOMEN-foam-double-v9-COVER.jpg", quality=94, optimize=True)
    story.save(EXPORT / "MinoxShop-WOMEN-foam-double-STORY-afternoon-v9.jpg", quality=94, optimize=True)
    out = EXPORT / "MinoxShop-WOMEN-foam-double-v9-16s.mp4"
    encode(out)
    write_kit()
    shutil.copy(out, WORK / "recording_demo.mp4")
    mapping = {
        "b0_hand.jpg": "women-v9-shed_hand.jpg",
        "b1_pillow.jpg": "women-v9-pillow.jpg",
        "b2_brush.jpg": "women-v9-brush.jpg",
        "b3_part.jpg": "women-v9-part.jpg",
    }
    for src_name, dst_name in mapping.items():
        src = ASSETS / src_name
        if src.exists():
            shutil.copy(src, EXPORT / dst_name)
    print("DONE", out)


if __name__ == "__main__":
    main()
