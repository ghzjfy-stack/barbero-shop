#!/usr/bin/env python3
"""Women Rogaine 5% foam DOUBLE reel v2 — rebuild (not polish).

Owner feedback on v1: Hebrew broken, images repeat, effects weak.
Path B (expert): problem hook → single reveal+ease → double slam offer → CTA.
Natural Israeli ad Hebrew · ken burns · shine · pack buildup · CapCut-safe CTA.
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
WORK = Path("/tmp/women-foam-v2")
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

NAVY = (10, 20, 42)
NAVY2 = (16, 32, 62)
GOLD = (198, 161, 91)
GOLD_SOFT = (224, 196, 140)
INK = (18, 22, 34)
WHITE = (255, 255, 255)
MUTED = (176, 186, 208)

PRICE, PRICE_WAS, PRICE_SAVE = 758, 998, 240
PRODUCT_URL = "https://www.minox-shop.co.il/shop#product-rogaine-double-woman"


def font(size: int, bold: bool = True, he: bool = True):
    if he:
        return ImageFont.truetype(HEB_B if bold else HEB_R, size)
    return ImageFont.truetype(LAT_B if bold else LAT_R, size)


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


def is_latin_glyph(ch: str) -> bool:
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


def measure_mixed(draw, text: str, size: int, bold: bool = True):
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


def gold_rule(im, y, width, alpha=255):
    if width < 4 or alpha < 8:
        return
    ImageDraw.Draw(im).rounded_rectangle([(W - width) // 2, y, (W + width) // 2, y + 3], 2, fill=GOLD + (alpha,))


def wink(im, cx, cy, phase, scale=1.0):
    pulse = math.sin(math.pi * max(0.0, min(1.0, phase)))
    if pulse < 0.05:
        return
    a = int(245 * pulse)
    sp = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sp)
    r = int(18 * scale * (0.5 + 0.5 * pulse))
    d.line([(cx - r, cy), (cx + r, cy)], fill=(255, 248, 220, a), width=max(2, int(3 * scale)))
    d.line([(cx, cy - r), (cx, cy + r)], fill=(255, 248, 220, a), width=max(2, int(3 * scale)))
    c = max(2, int(4 * scale * pulse))
    d.ellipse([cx - c, cy - c, cx + c, cy + c], fill=(255, 255, 255, a))
    im.alpha_composite(sp.filter(ImageFilter.GaussianBlur(1.5)))
    im.alpha_composite(sp)


def soft_shadow(c, box, x, y, a=130):
    sh = Image.new("RGBA", (box.size[0] + 90, 80), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([14, 22, box.size[0] + 70, 56], fill=(0, 0, 0, int(a * 0.55)))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (x - 45, y + box.size[1] - 10))


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
    band_w = max(36, int(w * 0.22))
    band = Image.new("RGBA", (band_w, h), (0, 0, 0, 0))
    px = band.load()
    for i in range(band_w):
        a = int(58 * math.sin(math.pi * i / max(1, band_w - 1)))
        for j in range(h):
            px[i, j] = (255, 250, 235, a)
    sheared = Image.new("RGBA", (w + band_w, h), (0, 0, 0, 0))
    for j in range(h):
        ox = int((j / max(1, h - 1)) * band_w * 0.55)
        sheared.alpha_composite(band.crop((0, j, band_w, j + 1)), (ox, j))
    cx = int(x - band_w + u * (w + band_w * 2))
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    layer.alpha_composite(sheared.crop((0, 0, w, h)).filter(ImageFilter.GaussianBlur(5)), (cx, y))
    im.alpha_composite(layer)


def navy_field(warm=0.0, light_y=0.3):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, H * light_y
    r = np.sqrt(((xx - cx) / (W * 0.72)) ** 2 + ((yy - cy) / (H * 0.85)) ** 2)
    mix = np.clip(1 - 0.55 * r, 0.0, 1.0)
    base = np.array(NAVY, np.float32)
    hi = np.array(NAVY2, np.float32) + np.array([20, 14, 8], np.float32) * warm
    arr = base + (hi - base) * mix[:, :, None]
    bloom = np.exp(-(((xx - cx) / (W * 0.3)) ** 2 + ((yy - cy) / (H * 0.2)) ** 2))
    arr = arr + bloom[:, :, None] * np.array([50, 42, 30], np.float32) * (0.5 + 0.3 * warm)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(wash)
    d.ellipse((160, -100, 920, 500), fill=(255, 230, 190, 26))
    d.ellipse((-140, 1300, 540, 2000), fill=(198, 161, 91, 16))
    return Image.alpha_composite(im, wash.filter(ImageFilter.GaussianBlur(60)))


def kenburns(base: Image.Image, t: float, zoom0=1.0, zoom1=1.1, pan_y=-0.2) -> Image.Image:
    z = zoom0 + (zoom1 - zoom0) * ease_in_out(t)
    nw, nh = int(W * z), int(H * z)
    im = base.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - W) // 2
    y = int((nh - H) // 2 + pan_y * (nh - H) * 0.2)
    y = max(0, min(y, nh - H))
    return im.crop((x, y, x + W, y + H)).convert("RGBA")


def particles(im, local, seed=7, n=26, rise=80):
    bub = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    db = ImageDraw.Draw(bub)
    rng = np.random.default_rng(seed)
    for _ in range(n):
        bx = int(rng.integers(40, W - 40))
        by = int((rng.random() * H + local * rise * (0.4 + rng.random())) % H)
        br = int(5 + rng.random() * 16)
        db.ellipse([bx - br, by - br, bx + br, by + br], fill=(255, 255, 255, int(12 + rng.random() * 20)))
    im.alpha_composite(bub.filter(ImageFilter.GaussianBlur(1.1)))


def brand_logo(im, t, logo):
    enter = ease_out(min(1.0, t / 0.35))
    if enter < 0.02:
        return
    pulse = 1.0 + 0.03 * math.sin(t * math.pi * 1.1) * min(1.0, max(0.0, t - 0.4))
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
    y = 44
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), (x - 8, y - 4))
    im.alpha_composite(plate, (x, y))
    if 1.0 < (t % 3.0) < 1.3:
        wink(im, x + plate_w - 6, y + 8, ((t % 3.0) - 1.0) / 0.3, 0.65)


def place_pack(im, pack, scale, alpha, y, shake=0.0):
    if alpha < 0.02:
        return None
    pw = max(1, int(pack.size[0] * scale))
    ph = max(1, int(pack.size[1] * scale))
    pp = pack.resize((pw, ph), Image.Resampling.LANCZOS)
    if alpha < 0.999:
        pp = pp.copy()
        pp.putalpha(pp.split()[-1].point(lambda a: int(a * alpha)))
    sx = int(shake * 10 * math.sin(shake * 40))
    px = (W - pw) // 2 + sx
    soft_shadow(im, pp, px, y, a=int(140 * alpha))
    if alpha > 0.55:
        ref = reflection(pp, op=0.26 * min(1, (alpha - 0.55) / 0.45), frac=0.3)
        im.alpha_composite(ref, (px, y + ph - 6))
    im.alpha_composite(pp, (px, y))
    return px, y, pw, ph


def chip(im, txt, y, alpha, style="white"):
    if alpha < 0.05:
        return
    size = 26
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw, th = measure_mixed(probe, txt, size, True)
    pw, ph = tw + 44, th + 20
    pill = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    d = ImageDraw.Draw(pill)
    if style == "gold":
        d.rounded_rectangle([0, 0, pw - 1, ph - 1], ph // 2, fill=GOLD + (int(240 * alpha),))
        fill = NAVY
    else:
        d.rounded_rectangle([0, 0, pw - 1, ph - 1], ph // 2, fill=(255, 255, 255, int(235 * alpha)))
        fill = INK
    draw_mixed_at(pill, txt, 22, 10, size, fill, int(255 * alpha), True)
    im.alpha_composite(pill, ((W - pw) // 2, y + int((1 - alpha) * 22)))


def price_block(im, y, alpha=255):
    if alpha < 8:
        return
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    price = f"₪ {PRICE}"
    was = f"₪{PRICE_WAS}"
    f_price = font(62, True, False)
    f_was = font(24, True, False)
    bb = d.textbbox((0, 0), price, font=f_price)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x = (W - tw) // 2 - bb[0]
    d.text((x, y + 3), price, font=f_price, fill=(0, 0, 0, int(110 * alpha / 255)))
    d.text((x, y), price, font=f_price, fill=(*WHITE, alpha))
    wb = d.textbbox((0, 0), was, font=f_was)
    ww = wb[2] - wb[0]
    wx = (W - ww) // 2 - wb[0]
    wy = y + th + 16
    d.text((wx, wy), was, font=f_was, fill=(155, 164, 180, int(alpha * 0.9)))
    mid = wy + (wb[3] - wb[1]) // 2 + 2
    d.line([(wx - 2, mid), (wx + ww + 2, mid)], fill=(155, 164, 180, int(alpha * 0.9)), width=3)
    im.alpha_composite(layer)

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
    ImageDraw.Draw(pill).rounded_rectangle([0, 0, pill_w - 1, pill_h - 1], pill_h // 2, fill=GOLD + (int(240 * alpha / 255),))
    ImageDraw.Draw(pill).text((pad_x - ab[0], (pill_h - ah) // 2 - ab[1]), amt, font=f_amt, fill=(*NAVY, alpha))
    ImageDraw.Draw(pill).text(
        (pad_x + aw + gap - hb[0], (pill_h - hh) // 2 - hb[1]), he, font=f_he, fill=(*NAVY, alpha), language="he"
    )
    im.alpha_composite(pill, ((W - pill_w) // 2, wy + (wb[3] - wb[1]) + 12))


def load_assets():
    return {
        "hook": Image.open(ASSETS / "hook_bg.jpg").convert("RGB"),
        "single": Image.open(ASSETS / "single_cut.png").convert("RGBA"),
        "left": Image.open(ASSETS / "left_cut.png").convert("RGBA"),
        "right": Image.open(ASSETS / "right_cut.png").convert("RGBA"),
        "double": Image.open(ASSETS / "double_cut.png").convert("RGBA"),
        "logo": Image.open(ASSETS / "logo.png").convert("RGBA"),
    }


def frame_at(i, A):
    t = i / FPS
    logo = A["logo"]

    # ---- 0–2.6 HOOK (problem) — NO gendered lifestyle face ----
    if t < 2.6:
        local = t / 2.6
        # Pure navy + window-light metaphor (scalp-in-light), never a man/woman face
        im = navy_field(warm=0.35 + 0.15 * math.sin(t * 1.5), light_y=0.22 + 0.03 * local)
        shaft = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shaft)
        for k in range(7):
            ang = -0.55 + k * 0.18
            x1 = int(W / 2 + math.sin(ang) * 980)
            y1 = int(140 + math.cos(ang) * 1250)
            sd.line([(W // 2, 120), (x1, y1)], fill=(255, 230, 190, 12 + k % 3), width=20)
        im.alpha_composite(shaft.filter(ImageFilter.GaussianBlur(18)))
        # soft vignette breathe
        particles(im, local, seed=2, n=14, rise=30)

        shake = max(0.0, 1.0 - t / 0.4) * (1 if int(t * 42) % 2 == 0 else -1)
        a = int(255 * ease_out(min(1.0, t / 0.22)))
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        text_c(layer, "הקרקפת מתחילה לבלוט", 720 + int(shake * 4), 48, WHITE, a, shadow=7)
        # Avoid tofu "?": draw HE then Latin "?" on the LEFT (Hebrew sentence end)
        if a > 8:
            probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
            he = "מבעד לשיער"
            tw, th = measure_mixed(probe, he, 48, True)
            qf = font(48, True, False)
            qb = probe.textbbox((0, 0), "?", font=qf)
            qw = qb[2] - qb[0]
            gap = 6
            total = tw + gap + qw
            x0 = (W - total) // 2
            yy = 795 + int(shake * 4)
            for ox, oy, aa in ((0, 7, 150), (0, 3, 90)):
                lyr = Image.new("RGBA", im.size, (0, 0, 0, 0))
                draw_mixed_at(lyr, he, x0 + qw + gap + ox, yy + oy, 48, (0, 0, 0), int(aa * a / 255), True)
                ImageDraw.Draw(lyr).text((x0 + ox - qb[0], yy + oy - qb[1]), "?", font=qf, fill=(0, 0, 0, int(aa * a / 255)))
                layer.alpha_composite(lyr)
            draw_mixed_at(layer, he, x0 + qw + gap, yy, 48, WHITE, a, True)
            ImageDraw.Draw(layer).text((x0 - qb[0], yy - qb[1]), "?", font=qf, fill=(*WHITE, a))
        im.alpha_composite(layer)
        if a > 40:
            gold_rule(im, 880, int(210 * ease_out(min(1.0, (t - 0.25) / 0.28))), a)
        sub = ease_out(min(1.0, max(0.0, (t - 0.7) / 0.3)))
        text_c(im, "יש דרך נוחה יותר", 920, 32, GOLD_SOFT, int(240 * sub), shadow=3)
        brand_logo(im, t, logo)
        return im

    # ---- 2.6–6.2 REVEAL (one box first + ease chips) ----
    if t < 6.2:
        local = (t - 2.6) / 3.6
        im = navy_field(warm=0.15 + 0.08 * math.sin(local * math.pi), light_y=0.28)
        particles(im, local, seed=3, n=18, rise=50)
        # Titles BELOW logo plate (~y≥200)
        ta = int(255 * ease_out(min(1.0, local / 0.16)))
        text_c(im, "קצף 5% לנשים", 230, 46, GOLD, ta, shadow=4)
        gold_rule(im, 295, int(150 * ease_out(min(1.0, (local - 0.05) / 0.2))), ta)
        text_c(im, "Rogaine", 320, 28, MUTED, int(ta * 0.95), lat=True, shadow=2)
        text_c(im, "פעם ביום בלבד", 360, 28, MUTED, int(ta * 0.92), bold=False, shadow=2)

        pop = ease_out_back(min(1.0, max(0.0, (local - 0.05) / 0.28)))
        pop_c = max(0.0, min(1.0, pop))
        drift = 1.0 + 0.04 * ease_in_out(max(0.0, (local - 0.35) / 0.65))
        y = 450 + int((1 - pop_c) * 110)
        # Use left half of official double render (real box) — not single plate collage
        placed = place_pack(im, A["left"], 1.05 * drift * (0.88 + 0.12 * pop_c), pop_c, y)
        if placed and pop_c > 0.7:
            px, py, pw, ph = placed
            diagonal_shine(im, px, py, pw, ph, (local - 0.28) / 0.55)
            wink(im, px + int(pw * 0.78), py + 30, (local - 0.35) / 0.2, 0.95)

        chips = [
            (0.42, "מריחה אחת ביום", 1185, "white"),
            (0.55, "מתייבש מהר", 1260, "white"),
            (0.68, "בלי ריח לוואי", 1335, "gold"),
        ]
        for start, txt, yy, style in chips:
            ca = ease_out(min(1.0, max(0.0, (local - start) / 0.18)))
            chip(im, txt, yy, ca, style)

        brand_logo(im, t, logo)
        return im

    # ---- 6.2–9.8 DOUBLE SLAM + PRICE ----
    if t < 9.8:
        local = (t - 6.2) / 3.6
        im = navy_field(warm=0.2, light_y=0.3)
        particles(im, local, seed=11, n=28, rise=95)

        ta = int(255 * ease_out(min(1.0, local / 0.18)))
        text_c(im, "מארז כפול", 205, 50, WHITE, ta, shadow=5)
        gold_rule(im, 272, int(140 * ease_out(min(1.0, (local - 0.06) / 0.2))), ta)
        text_c(im, "8 חודשי טיפול רציף", 300, 34, GOLD, int(ta * 0.95), shadow=3)

        # left arrives, then right slams
        left_pop = ease_out_back(min(1.0, max(0.0, (local - 0.05) / 0.28)))
        right_pop = ease_out_back(min(1.0, max(0.0, (local - 0.32) / 0.26)))
        left_c = max(0.0, min(1.0, left_pop))
        right_c = max(0.0, min(1.0, right_pop))
        shake = max(0.0, 1.0 - max(0.0, (local - 0.32) / 0.18)) * right_c

        gap = 18
        # scale packs
        ls = 0.78 * (0.9 + 0.1 * left_c)
        rs = 0.78 * (0.9 + 0.1 * right_c)
        left = A["left"].resize((max(1, int(A["left"].size[0] * ls)), max(1, int(A["left"].size[1] * ls))), Image.Resampling.LANCZOS)
        right = A["right"].resize((max(1, int(A["right"].size[0] * rs)), max(1, int(A["right"].size[1] * rs))), Image.Resampling.LANCZOS)
        if left_c < 1:
            left = left.copy()
            left.putalpha(left.split()[-1].point(lambda a: int(a * left_c)))
        if right_c < 1:
            right = right.copy()
            right.putalpha(right.split()[-1].point(lambda a: int(a * right_c)))

        total_w = left.size[0] + right.size[0] + gap
        x0 = (W - total_w) // 2 + int(shake * 8 * math.sin(local * 55))
        y0 = 400 + int((1 - left_c) * 80)
        # left slides from left
        lx = x0 - int((1 - left_c) * 80)
        rx = x0 + left.size[0] + gap + int((1 - right_c) * 120)

        soft_shadow(im, left, lx, y0, a=int(120 * left_c))
        soft_shadow(im, right, rx, y0, a=int(120 * right_c))
        im.alpha_composite(left, (lx, y0))
        im.alpha_composite(right, (rx, y0))
        if right_c > 0.7:
            diagonal_shine(im, x0, y0, total_w, left.size[1], (local - 0.4) / 0.45)
            wink(im, rx + int(right.size[0] * 0.7), y0 + 28, (local - 0.45) / 0.2, 0.9)

        if local > 0.55:
            pa = int(255 * ease_out(min(1.0, (local - 0.55) / 0.2)))
            price_block(im, 1040, pa)
            chip(im, "הכי משתלם", 1340, ease_out(min(1.0, max(0.0, (local - 0.7) / 0.18))), "gold")

        brand_logo(im, t, logo)
        return im

    # ---- 9.8–13.0 CTA ----
    local = (t - 9.8) / 3.2
    im = navy_field(warm=0.22, light_y=0.32)
    particles(im, local, seed=19, n=20, rise=60)

    ta = int(255 * ease_out(min(1.0, local / 0.18)))
    text_c(im, "משלוח חינם עד הבית", 235, 38, WHITE, ta, shadow=4)
    gold_rule(im, 292, int(170 * ease_out(min(1.0, (local - 0.06) / 0.2))), ta)
    text_c(im, "10% נקודות בונוס בנובמבר", 320, 28, GOLD_SOFT, int(ta * 0.95), shadow=2)

    pop = ease_out_back(min(1.0, max(0.0, (local - 0.08) / 0.28)))
    pop_c = max(0.0, min(1.0, pop))
    y = 360 + int((1 - pop_c) * 50)
    placed = place_pack(im, A["double"], 0.74 * (0.92 + 0.08 * pop_c), pop_c, y)
    if placed and pop_c > 0.75:
        px, py, pw, ph = placed
        diagonal_shine(im, px, py, pw, ph, (local - 0.3) / 0.5)
        wink(im, px + int(pw * 0.75), py + 26, (local - 0.35) / 0.2, 0.85)

    # pulsing CTA — well above TT/IG chrome
    cta_a = ease_out(min(1.0, max(0.0, (local - 0.28) / 0.22)))
    if cta_a > 0.05:
        pulse = 1.0 + 0.045 * math.sin(max(0, local - 0.35) * math.pi * 2.2)
        label = "הזמיני עכשיו"
        f = font(36, True, True)
        bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), label, font=f, language="he")
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        pw, ph = int((tw + 70) * pulse), int((th + 28) * pulse)
        btn = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        ImageDraw.Draw(btn).rounded_rectangle([0, 0, pw - 1, ph - 1], ph // 2, fill=GOLD + (int(245 * cta_a),))
        tx = (pw - tw) // 2 - bb[0]
        ty = (ph - th) // 2 - bb[1]
        ImageDraw.Draw(btn).text((tx, ty), label, font=f, fill=(*NAVY, int(255 * cta_a)), language="he")
        im.alpha_composite(btn, ((W - pw) // 2, 1185 + int((1 - cta_a) * 14)))
        text_c(im, "minox-shop.co.il", 1285, 26, MUTED, int(230 * cta_a), lat=True, shadow=2)
        text_c(im, "תוצאות משתנות בין אנשים", 1580, 18, (120, 130, 150), int(145 * cta_a), bold=False, shadow=1)

    brand_logo(im, t, logo)
    return im


def build_cover(A):
    im = navy_field(0.18, 0.32)
    text_c(im, "הקרקפת מתחילה לבלוט?", 220, 42, WHITE, 255, shadow=4)
    gold_rule(im, 290, 180, 255)
    text_c(im, "קצף 5% לנשים · מארז כפול", 320, 34, GOLD, 255, shadow=3)
    place_pack(im, A["double"], 0.88, 1.0, 480)
    chip(im, "8 חודשים · הכי משתלם", 1160, 1.0, "gold")
    text_c(im, f"₪ {PRICE}", 1280, 56, WHITE, 255, lat=True, shadow=3)
    text_c(im, "הזמיני עכשיו", 1420, 34, GOLD_SOFT, 255, shadow=2)
    brand_logo(im, 2.0, A["logo"])
    return im.convert("RGB")


def build_story(A):
    im = navy_field(0.2, 0.3)
    place_pack(im, A["double"], 0.95, 1.0, 260)
    text_c(im, "Rogaine", 920, 48, WHITE, 255, lat=True, shadow=3)
    text_c(im, "קצף 5% לנשים", 990, 40, GOLD, 255, shadow=3)
    text_c(im, "מארז כפול · 8 חודשים", 1055, 30, MUTED, 255, bold=False, shadow=2)
    price_block(im, 1160, 255)
    text_c(im, "minox-shop.co.il", 1680, 28, MUTED, 230, lat=True, shadow=2)
    brand_logo(im, 2.0, A["logo"])
    return im.convert("RGB")


def write_kit():
    caption = f"""הקרקפת מתחילה לבלוט מבעד לשיער?

קצף Rogaine 5% לנשים — מריחה אחת ביום, בלי ריח לוואי.
מארז כפול ל־8 חודשים · ₪{PRICE} (חיסכון ₪{PRICE_SAVE})
בנובמבר: 10% נקודות בונוס + משלוח חינם עד הבית.

{PRODUCT_URL}

#מינוקסידיל #Rogaine #נשירתשיער #MinoxShop #קצף
"""
    (EXPORT / "CAPTION-v2.txt").write_text(caption.strip() + "\n", encoding="utf-8")
    (EXPORT / "UPLOAD-v2.txt").write_text(
        f"""ריל v2 — Rogaine קצף 5% לנשים · מארז כפול (שיקום אחרי v1)

קבצים:
- MinoxShop-WOMEN-foam-double-v2-13s.mp4
- MinoxShop-WOMEN-foam-double-v2-COVER.jpg
- MinoxShop-WOMEN-foam-double-STORY-afternoon-v2.jpg

מה השתנה מ־v1:
- עברית טבעית (בעיה → פתרון → כפול → CTA)
- תמונות לא חוזרות: הוק לייפסטייל → יחיד → סלאם כפול → כפול CTA
- אפקטים: ken burns, shine, shake, particles, pulse CTA

לינק: {PRODUCT_URL}
""".strip()
        + "\n",
        encoding="utf-8",
    )


def encode(out: Path, bed: Path | None):
    if bed and bed.exists():
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(FPS),
            "-i", str(FRAMES / "f_%04d.jpg"),
            "-i", str(bed),
            "-filter_complex",
            f"[1:a]afade=t=in:st=0:d=0.5,afade=t=out:st={DURATION-0.7}:d=0.7,volume=0.58,atrim=0:{DURATION}[a]",
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
    print(f"render {N} frames")
    qa = {0, int(1.2 * FPS), int(3.5 * FPS), int(5.2 * FPS), int(7.2 * FPS), int(8.8 * FPS), int(11.2 * FPS), N - 1}
    for i in range(N):
        fr = frame_at(i, A)
        fr.convert("RGB").save(FRAMES / f"f_{i:04d}.jpg", quality=93, optimize=True)
        if i in qa:
            fr.convert("RGB").save(WORK / "qa" / f"qa_{i:04d}.jpg", quality=92)
        if i % 60 == 0:
            print(f"  {i}/{N}")

    cover = build_cover(A)
    story = build_story(A)
    cover_p = EXPORT / "MinoxShop-WOMEN-foam-double-v2-COVER.jpg"
    story_p = EXPORT / "MinoxShop-WOMEN-foam-double-STORY-afternoon-v2.jpg"
    cover.save(cover_p, quality=94, optimize=True)
    story.save(story_p, quality=94, optimize=True)

    out = EXPORT / "MinoxShop-WOMEN-foam-double-v2-13s.mp4"
    encode(out, WORK / "bed_soft.wav")
    write_kit()
    shutil.copy(out, WORK / "recording_demo.mp4")
    print("DONE", out)


if __name__ == "__main__":
    main()
