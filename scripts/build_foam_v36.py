#!/usr/bin/env python3
"""v36 — premium CapCut before/after opener for MinoxShop foam reel.

Opener redesign:
- Cream luxury field (matches body)
- Twin polished cards: לפני | אחרי ארבעה חודשים
- Gold rule + sharp labels + soft shadows
- Harder, cleaner transitions (no muddy full-bleed scalp dissolve)
- Then lifestyle + double-pack promise → product/price/offer
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

sys.path.insert(0, "/tmp/foam-v36")
from brand_logo import apply_brand_logo

OUT = Path("/tmp/foam-v36/frames")
OUT.mkdir(parents=True, exist_ok=True)
PACKS = Path("/tmp/foam-v36/packs")
W, H, FPS = 1080, 1920, 60
BODY_SEC = 10.2
N_BODY = int(BODY_SEC * FPS)

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
PRICE, PRICE_WAS, PRICE_SAVE = 758, 998, 240


def font(size: int, bold: bool = True):
    return ImageFont.truetype(HEB_B if bold else HEB_R, size)


def font_lat(size: int, bold: bool = True):
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


def cream_field(warm: float = 0.0) -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, H * 0.42
    r = np.sqrt(((xx - cx) / (W * 0.75)) ** 2 + ((yy - cy) / (H * 0.9)) ** 2)
    mix = np.clip(1 - 0.20 * r, 0.75, 1.0)
    base = np.array(CREAM, dtype=np.float32)
    hi = np.array(CREAM2, dtype=np.float32)
    arr = base + (hi - base) * mix[:, :, None]
    arr[:, :, 0] = np.clip(arr[:, :, 0] + 6 * warm, 0, 255)
    arr[:, :, 1] = np.clip(arr[:, :, 1] + 3 * warm, 0, 255)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(wash)
    d.ellipse((-200, 1000, 560, 1800), fill=(255, 220, 180, 26))
    d.ellipse((620, -160, 1300, 560), fill=(255, 235, 210, 20))
    return Image.alpha_composite(im, wash.filter(ImageFilter.GaussianBlur(70)))


def reflection(p: Image.Image, op: float = 0.28, frac: float = 0.32) -> Image.Image:
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


def soft_shadow(c: Image.Image, box: Image.Image, x: int, y: int, a: int = 110):
    sh = Image.new("RGBA", (box.size[0] + 70, 64), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([10, 16, box.size[0] + 55, 46], fill=(30, 22, 14, int(a * 0.55)))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (x - 35, y + box.size[1] - 10))


def wink_sparkle(layer: Image.Image, cx: int, cy: int, phase: float, scale: float = 1.0):
    pulse = math.sin(math.pi * max(0.0, min(1.0, phase)))
    if pulse < 0.05:
        return
    a = int(255 * pulse)
    sp = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sp)
    r = int(20 * scale * (0.55 + 0.45 * pulse))
    d.line([(cx - r, cy), (cx + r, cy)], fill=(255, 250, 230, a), width=max(2, int(3 * scale)))
    d.line([(cx, cy - r), (cx, cy + r)], fill=(255, 250, 230, a), width=max(2, int(3 * scale)))
    core = max(2, int(5 * scale * pulse))
    d.ellipse([cx - core, cy - core, cx + core, cy + core], fill=(255, 255, 255, a))
    layer.alpha_composite(sp.filter(ImageFilter.GaussianBlur(2)))
    layer.alpha_composite(sp)


def bottom_readability_band(im: Image.Image, top_y: int = 1180, strength: float = 1.0):
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = band.load()
    for y in range(top_y, H):
        u = (y - top_y) / max(1, H - top_y)
        a = int((0.05 + 0.82 * (u ** 1.65)) * 255 * strength)
        for x in range(W):
            px[x, y] = (10, 8, 6, a)
    im.alpha_composite(band.filter(ImageFilter.GaussianBlur(18)))


def draw_text_shadowed(im, text, y, size, fill, alpha=255, bold=True, shadow=6):
    f = font(size, bold)
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bb = d.textbbox((0, 0), text, font=f, language="he")
    x = (W - (bb[2] - bb[0])) // 2 - bb[0]
    for ox, oy, a in ((0, shadow, 160), (0, shadow // 2, 120), (2, 2, 90)):
        d.text((x + ox, y + oy), text, font=f, fill=(0, 0, 0, int(a * alpha / 255)), language="he")
    d.text((x, y), text, font=f, fill=(*fill, alpha), language="he")
    im.alpha_composite(layer)
    return bb[3] - bb[1]


def gold_rule(im, y, w, alpha=255):
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([(W - w) // 2, y, (W + w) // 2, y + 4], 2, fill=GOLD + (alpha,))


def draw_price_block(im: Image.Image, y: int, alpha: int = 255, large: bool = True):
    if alpha < 8:
        return
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    price = f"₪ {PRICE}"
    was = f"₪{PRICE_WAS}"
    f_price = font_lat(68 if large else 52, True)
    f_was = font_lat(26 if large else 22, True)
    f_save_he = font(26 if large else 22, True)
    f_save_lat = font_lat(26 if large else 22, True)
    bb = d.textbbox((0, 0), price, font=f_price)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x = (W - tw) // 2 - bb[0]
    for ox, oy, a in ((0, 4, 110), (0, 2, 80)):
        d.text((x + ox, y + oy), price, font=f_price, fill=(0, 0, 0, int(a * alpha / 255)))
    d.text((x, y), price, font=f_price, fill=(*INK, alpha))
    wb = d.textbbox((0, 0), was, font=f_was)
    ww = wb[2] - wb[0]
    wx = (W - ww) // 2 - wb[0]
    wy = y + th + 22
    d.text((wx, wy), was, font=f_was, fill=(120, 124, 136, int(alpha * 0.85)))
    mid = wy + (wb[3] - wb[1]) // 2 + 2
    d.line([(wx - 2, mid), (wx + ww + 2, mid)], fill=(120, 124, 136, int(alpha * 0.9)), width=3)
    im.alpha_composite(layer)
    sy = wy + (wb[3] - wb[1]) + 18
    he, amt = "חיסכון ", f"{PRICE_SAVE}₪"
    tmp = Image.new("RGBA", (W, 80), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    hb = td.textbbox((0, 0), he, font=f_save_he, language="he")
    ab = td.textbbox((0, 0), amt, font=f_save_lat)
    hw, hh = hb[2] - hb[0], hb[3] - hb[1]
    aw, ah = ab[2] - ab[0], ab[3] - ab[1]
    sx = (W - (hw + 10 + aw)) // 2
    layer2 = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d2 = ImageDraw.Draw(layer2)
    d2.text((sx - hb[0], sy - hb[1]), he, font=f_save_he, fill=(70, 74, 88, int(alpha * 0.95)), language="he")
    d2.text((sx + hw + 10 - ab[0], sy - ab[1] + max(0, (hh - ah) // 2)), amt, font=f_save_lat, fill=(70, 74, 88, int(alpha * 0.95)))
    im.alpha_composite(layer2)


def kenburns(base: Image.Image, t: float, zoom0=1.0, zoom1=1.12, pan_y=-0.35) -> Image.Image:
    z = zoom0 + (zoom1 - zoom0) * ease_in_out(t)
    nw, nh = int(W * z), int(H * z)
    im = base.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - W) // 2
    y = int((nh - H) // 2 + pan_y * (nh - H) * 0.18)
    y = max(0, min(y, nh - H))
    return im.crop((x, y, x + W, y + H)).convert("RGBA")


def make_ba_card(photo: Image.Image, he_label: str, accent, scale: float, alpha: float) -> Image.Image:
    """Photo-dominant card: label overlaid on image (no empty white belly)."""
    cw = int(460 * scale)
    inset = 14
    pw = cw - inset * 2
    pic = photo.resize((pw, pw), Image.Resampling.LANCZOS)
    ch = inset + pw + inset  # tight to photo
    card = Image.new("RGBA", (cw + 36, ch + 50), (0, 0, 0, 0))
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([14, 18, cw + 24, ch + 28], 26, fill=(20, 16, 12, int(100 * alpha)))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    plate = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle([0, 0, cw - 1, ch - 1], 24, fill=(255, 255, 255, int(255 * alpha)))
    mask = Image.new("L", pic.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, pic.size[0] - 1, pic.size[1] - 1], 16, fill=255)
    photo_layer = Image.new("RGBA", pic.size)
    photo_layer.paste(pic.convert("RGB"), (0, 0))
    photo_layer.putalpha(mask.point(lambda v: int(v * alpha)))
    plate.alpha_composite(photo_layer, (inset, inset))
    # bottom gradient scrim on photo for label
    scrim = Image.new("RGBA", pic.size, (0, 0, 0, 0))
    spx = scrim.load()
    for yy in range(pic.size[1] - 110, pic.size[1]):
        u = (yy - (pic.size[1] - 110)) / 110
        aa = int(200 * (u ** 1.2) * alpha)
        for xx in range(pic.size[0]):
            spx[xx, yy] = (8, 6, 5, aa)
    scrim.putalpha(Image.composite(scrim.split()[-1], Image.new("L", pic.size, 0), mask))
    plate.alpha_composite(scrim, (inset, inset))
    rim = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    ImageDraw.Draw(rim).rounded_rectangle([2, 2, cw - 3, ch - 3], 24, outline=GOLD + (int(200 * alpha),), width=3)
    plate.alpha_composite(rim)
    f = font(28 if len(he_label) < 10 else 22, True)
    bb_probe = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), he_label, font=f, language="he")
    tw, th = bb_probe[2] - bb_probe[0], bb_probe[3] - bb_probe[1]
    pill_w, pill_h = tw + 40, th + 18
    pill = Image.new("RGBA", (pill_w, pill_h), (0, 0, 0, 0))
    ImageDraw.Draw(pill).rounded_rectangle([0, 0, pill_w - 1, pill_h - 1], pill_h // 2, fill=accent + (int(245 * alpha),))
    ImageDraw.Draw(pill).text(
        (20 - bb_probe[0], 9 - bb_probe[1]), he_label, font=f, fill=(255, 255, 255, int(255 * alpha)), language="he"
    )
    plate.alpha_composite(pill, ((cw - pill_w) // 2, ch - pill_h - 22))
    card.alpha_composite(plate, (18, 8))
    return card


def load_assets():
    life = Image.open("/tmp/minox-brand/hero-home-lifestyle-bg.png").convert("RGB")
    life = ImageEnhance.Color(life).enhance(1.06)
    life = ImageEnhance.Contrast(life).enhance(1.06)

    def cover(im: Image.Image) -> Image.Image:
        s = max(W / im.size[0], H / im.size[1])
        nw, nh = int(im.size[0] * s) + 1, int(im.size[1] * s) + 1
        im = im.resize((nw, nh), Image.Resampling.LANCZOS)
        x = max(0, (nw - W) // 2 - 90)
        y = max(0, (nh - H) // 2 - 60)
        return im.crop((x, y, x + W, y + H))

    life = cover(life)
    before = Image.open("/tmp/foam-v36/plates/before_sq.png").convert("RGB")
    after = Image.open("/tmp/foam-v36/plates/after_sq.png").convert("RGB")

    dbl = Image.open("/tmp/foam-v20/double_on_cream.png").convert("RGBA")
    rgb = np.array(dbl.convert("RGB"))
    cream = np.array([248, 242, 230], np.float32)
    dist = np.linalg.norm(rgb.astype(np.float32) - cream, axis=2)
    a = np.where(dist < 26, 0, 255).astype(np.uint8)
    a = np.where(a > 40, 255, a).astype(np.uint8)
    dbl.putalpha(Image.fromarray(a, "L").filter(ImageFilter.GaussianBlur(0.5)))
    bb = dbl.getbbox()
    dbl = dbl.crop(bb) if bb else dbl
    h_target = 620
    sc = h_target / dbl.size[1]
    dbl = dbl.resize((max(1, int(dbl.size[0] * sc)), h_target), Image.Resampling.LANCZOS)

    single = Image.open(PACKS / "rogaine_men.png").convert("RGBA")
    sh = 500
    single = single.resize((max(1, int(single.size[0] * sh / single.size[1])), sh), Image.Resampling.LANCZOS)
    return {"life": life, "before": before, "after": after, "dbl": dbl, "single": single}


def frame_body(i: int, assets: dict) -> Image.Image:
    t = i / FPS

    # ---- PREMIUM BA OPENER 0–3.5s ----
    if t < 3.5:
        im = cream_field(0.06 + 0.03 * math.sin(t * 1.2))

        # title entrance
        title_a = ease_out(min(1.0, t / 0.25))
        if title_a > 0.05:
            draw_text_shadowed(im, "תוצאות אמיתיות", 210, 42, INK, int(255 * title_a), shadow=3)
            if title_a > 0.4:
                rw = int(160 * ease_out(min(1, (t - 0.15) / 0.25)))
                gold_rule(im, 275, rw, int(255 * title_a))
            draw_text_shadowed(im, "לפני ואחרי", 300, 56, INK, int(255 * title_a), shadow=3)

        # cards pop
        pop = ease_out_back(min(1.0, max(0.0, (t - 0.18) / 0.35)))
        pop_c = max(0.0, min(1.0, pop))
        scale = 0.88 + 0.12 * pop_c
        # slow breathe
        breathe = 1.0 + 0.012 * math.sin(max(0, t - 0.5) * 1.6)
        scale *= breathe

        left = make_ba_card(assets["before"], "לפני", NAVY, scale, pop_c)
        right = make_ba_card(assets["after"], "אחרי ארבעה חודשים", (140, 70, 70), scale, pop_c)

        # positions — perfect centered pair with gold gap
        gap = 28
        total_w = left.size[0] + right.size[0] + gap
        x0 = (W - total_w) // 2
        y0 = 400 + int((1 - pop_c) * 80)
        # slight opposing slide for luxury entrance
        slide = int((1 - pop_c) * 50)
        im.alpha_composite(left, (x0 - slide, y0))
        im.alpha_composite(right, (x0 + left.size[0] + gap + slide, y0))

        # center gold diamond / sparkle after settle
        if pop_c > 0.85:
            wink_sparkle(im, W // 2, y0 + left.size[1] // 2 - 20, (t - 0.7) / 0.25, scale=0.9)

        # supporting line — sit under tighter cards
        sub_a = ease_out(min(1.0, max(0.0, (t - 0.55) / 0.25)))
        if sub_a > 0.05:
            draw_text_shadowed(im, "צפיפות שיער משופרת", 1120, 30, (70, 74, 88), int(230 * sub_a), bold=False, shadow=2)

        # late: slam value line before product
        if t >= 2.55:
            vb = ease_out(min(1.0, (t - 2.55) / 0.28))
            # darken band for readability of next beat tease
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(overlay).rectangle([0, 1280, W, H], fill=(12, 10, 8, int(150 * vb)))
            im.alpha_composite(overlay.filter(ImageFilter.GaussianBlur(10)))
            draw_text_shadowed(im, "מארז כפול לחצי שנה", 1420, 58, WHITE, int(255 * vb), shadow=9)
            if vb > 0.4:
                gold_rule(im, 1510, int(180 * vb), int(255 * vb))
            draw_text_shadowed(im, "המארז המקורי מארה״ב", 1535, 34, (250, 246, 238), int(245 * vb), shadow=5)
        return im

    # ---- PRODUCT 3.5–7.0s ----
    if t < 7.0:
        local = (t - 3.5) / 3.5
        im = cream_field(0.05 + 0.04 * math.sin(local * math.pi))
        ta = int(255 * ease_out(min(1, local / 0.16)))
        draw_text_shadowed(im, "מארז כפול לחצי שנה", 210, 48, INK, ta, shadow=3)
        if ta > 50:
            gold_rule(im, 285, int(130 * ease_out(min(1, (local - 0.06) / 0.22))), ta)
        draw_text_shadowed(im, "מקורי מארה״ב", 305, 30, (70, 74, 88), int(ta * 0.92), bold=False, shadow=2)

        pop = ease_out_back(min(1.0, max(0.0, (local - 0.06) / 0.26)))
        pop_c = max(0.0, min(1.0, pop))
        dbl = assets["dbl"]
        ps = 0.84 + 0.16 * pop_c
        drift = 1.0 + 0.035 * ease_in_out(max(0, (local - 0.38) / 0.62))
        pw = max(1, int(dbl.size[0] * ps * drift))
        ph = max(1, int(dbl.size[1] * ps * drift))
        pp = dbl.resize((pw, ph), Image.Resampling.LANCZOS)
        if pop_c < 1:
            pp = pp.copy()
            pp.putalpha(pp.split()[-1].point(lambda a: int(a * pop_c)))
        dy = int((1 - pop_c) * 110)
        px = (W - pw) // 2
        py = 420 + dy
        soft_shadow(im, pp, px, py, a=int(130 * pop_c))
        if pop_c > 0.5:
            ref = reflection(pp, op=0.30 * min(1, (pop_c - 0.5) / 0.5), frac=0.34)
            im.alpha_composite(ref, (px, py + ph - 6))
        im.alpha_composite(pp, (px, py))
        wink_sparkle(im, px + int(pw * 0.72), py + 36, (local - 0.32) / 0.2, scale=1.0)

        chip_t = ease_out_back(min(1.0, max(0.0, (local - 0.28) / 0.18)))
        chip_c = max(0.0, min(1.0, chip_t))
        if chip_c > 0.05:
            for idx, (txt, yy) in enumerate([("קצף רוגיין לגברים", 1180), ("שש פחיות לחצי שנה", 1265)]):
                a = int(255 * chip_c)
                f = font(30 if idx == 0 else 26, True)
                bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), txt, font=f, language="he")
                tw, th = bb[2] - bb[0], bb[3] - bb[1]
                pw2, ph2 = tw + 52, th + 24
                pill = Image.new("RGBA", (pw2, ph2), (0, 0, 0, 0))
                fill = NAVY + (int(235 * chip_c),) if idx == 0 else (255, 255, 255, int(240 * chip_c))
                fg = (255, 255, 255, a) if idx == 0 else INK + (a,)
                ImageDraw.Draw(pill).rounded_rectangle([0, 0, pw2 - 1, ph2 - 1], ph2 // 2, fill=fill)
                if idx == 1:
                    ImageDraw.Draw(pill).rounded_rectangle(
                        [1, 1, pw2 - 2, ph2 - 2], ph2 // 2, outline=NAVY + (int(160 * chip_c),), width=2
                    )
                ImageDraw.Draw(pill).text((26 - bb[0], 12 - bb[1]), txt, font=f, fill=fg, language="he")
                ox = int((1 - chip_c) * 36)
                im.alpha_composite(pill, ((W - pw2) // 2, yy + ox))

        price_t = ease_out(min(1.0, max(0.0, (local - 0.48) / 0.22)))
        if price_t > 0.05:
            draw_price_block(im, 1385, alpha=int(255 * price_t), large=True)

        im = apply_brand_logo(im, t - 3.5, y=36, size=96)
        return im

    # ---- OFFER 7.0–10.2s ----
    local = (t - 7.0) / 3.2
    im = cream_field(0.08)
    rng = np.random.default_rng(7)
    bub = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    db = ImageDraw.Draw(bub)
    for k in range(28):
        bx = int(rng.integers(40, W - 40))
        by = int((rng.random() * H + local * 90 * (0.5 + rng.random())) % H)
        br = int(8 + rng.random() * 28)
        ba = int(18 + rng.random() * 22)
        db.ellipse([bx - br, by - br, bx + br, by + br], fill=(255, 255, 255, ba))
    im.alpha_composite(bub.filter(ImageFilter.GaussianBlur(1.2)))

    ta = int(255 * ease_out(min(1, local / 0.18)))
    draw_text_shadowed(im, "עשרה אחוז נקודות בונוס", 200, 48, INK, ta, shadow=3)
    if ta > 40:
        rw = int(180 * ease_out(min(1, (local - 0.08) / 0.22)))
        gold_rule(im, 275, rw, ta)
        wink_sparkle(im, (W + rw) // 2 - 4, 277, (local - 0.22) / 0.18, scale=0.85)
    draw_text_shadowed(im, "בנוסף לצבירת נקודות על כל קנייה", 300, 30, INK, int(ta * 0.95), shadow=2)
    draw_text_shadowed(im, "משלוח חינם עד הבית", 355, 28, (70, 74, 88), int(ta * 0.9), bold=False, shadow=2)

    pop = ease_out_back(min(1.0, max(0.0, (local - 0.12) / 0.28)))
    pop_c = max(0.0, min(1.0, pop))
    single = assets["single"]
    ps = 0.86 + 0.14 * pop_c
    drift = 1.0 + 0.03 * ease_in_out(max(0, (local - 0.42) / 0.58))
    pw = max(1, int(single.size[0] * ps * drift))
    ph = max(1, int(single.size[1] * ps * drift))
    pp = single.resize((pw, ph), Image.Resampling.LANCZOS)
    if pop_c < 1:
        pp = pp.copy()
        pp.putalpha(pp.split()[-1].point(lambda a: int(a * pop_c)))
    dy = int((1 - pop_c) * 95)
    px = (W - pw) // 2
    py = 740 + dy
    soft_shadow(im, pp, px, py, a=int(120 * pop_c))
    if pop_c > 0.5:
        ref = reflection(pp, op=0.28 * min(1, (pop_c - 0.5) / 0.5), frac=0.32)
        im.alpha_composite(ref, (px, py + ph - 6))
    im.alpha_composite(pp, (px, py))
    wink_sparkle(im, px + pw // 2 + 28, py + 28, (local - 0.38) / 0.2, scale=0.95)

    price_t = ease_out(min(1.0, max(0.0, (local - 0.35) / 0.2)))
    if price_t > 0.05:
        draw_price_block(im, 1480, alpha=int(255 * price_t), large=False)

    im = apply_brand_logo(im, t - 3.5, y=36, size=96)
    return im


def main():
    assets = load_assets()
    print("assets ok fps", FPS, "frames", N_BODY)
    for i in range(N_BODY):
        fr = frame_body(i, assets)
        fr.convert("RGB").save(OUT / f"b_{i:04d}.jpg", quality=94, optimize=True)
        if i % 120 == 0:
            print("frame", i, f"{i/FPS:.2f}s")
    for qi in (10, 40, 90, 150, 210, 360, 500):
        Image.open(OUT / f"b_{qi:04d}.jpg").save(f"/tmp/foam-v36/qa/body_{qi}.jpg", quality=92)
    print("DONE body", N_BODY)


if __name__ == "__main__":
    main()
