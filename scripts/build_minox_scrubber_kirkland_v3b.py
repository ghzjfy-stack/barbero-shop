#!/usr/bin/env python3
"""MinoxShop scrubber v3 — dramatic hook FX + locked house cream outro (Kirkland)."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/tmp/scrubber-v3b")
ASSETS = ROOT / "assets"
FRAMES = ROOT / "frames"
QA = ROOT / "qa"
FRAMES.mkdir(exist_ok=True)
QA.mkdir(exist_ok=True)

W, H = 1080, 1920
FPS = 60
DURATION = 13.0
N = int(DURATION * FPS)

# House palette (locked with foam reels)
CREAM, CREAM2 = (245, 240, 232), (252, 248, 242)
NAVY = (14, 28, 52)
NAVY_DEEP = (10, 22, 40)
GOLD = (196, 158, 86)
GOLD_SOFT = (226, 199, 135)
INK = (22, 26, 38)
IVORY = (243, 245, 248)

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


BEFORE = ImageEnhance.Contrast(Image.open(ASSETS / "ba-before.jpg").convert("RGB")).enhance(1.1)
AFTER = ImageEnhance.Contrast(Image.open(ASSETS / "ba-after.jpg").convert("RGB")).enhance(1.14)
LOGO = Image.open(ASSETS / "main-logo.png").convert("RGBA")
PACK = Image.open(ASSETS / "kirkland-double-composed.png").convert("RGBA")


def fit_cover(im, tw, th, zoom=1.0, y_bias=0.40):
    w, h = im.size
    scale = max(tw / w, th / h) * zoom
    nw, nh = int(w * scale + 0.5), int(h * scale + 0.5)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - tw) // 2
    y = max(0, min(nh - th, int((nh - th) * y_bias)))
    return im.crop((x, y, x + tw, y + th))


def months_to_progress(m):
    return max(0.0, min(1.0, m / 6.0)) ** 0.82


def journey_months(t):
    # scrubber body starts after hook (~2.0s), ends ~8.6
    t0, t1 = 2.05, 8.55
    if t <= t0:
        return 0.0
    u = ease_in_out(min(1.0, (t - t0) / (t1 - t0)))
    keys = [(0.0, 0.0), (0.22, 2.0), (0.28, 2.0), (0.55, 4.0), (0.62, 4.0), (1.0, 6.0)]
    for (u0, m0), (u1, m1) in zip(keys, keys[1:]):
        if u <= u1:
            local = 0 if u1 == u0 else (u - u0) / (u1 - u0)
            return m0 + (m1 - m0) * local
    return 6.0


def milestone(m):
    if m < 1.0:
        return "0", "התחלה"
    if m < 3.0:
        return "2", "חודשיים"
    if m < 5.2:
        return "4", "צפיפות ניכרת"
    return "6", "תוצאה מלאה יותר"


def cream_field():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.42) / (H * 0.9)) ** 2)
    mix = np.clip(1 - 0.2 * r, 0.75, 1.0)
    arr = np.array(CREAM, np.float32) + (np.array(CREAM2, np.float32) - np.array(CREAM, np.float32)) * mix[:, :, None]
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(wash).ellipse((-200, 1000, 560, 1800), fill=(255, 220, 180, 26))
    return Image.alpha_composite(im, wash.filter(ImageFilter.GaussianBlur(70)))


def navy_field(spotlight=1.0):
    arr = np.zeros((H, W, 3), dtype=np.float32)
    arr[:] = NAVY_DEEP
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W * 0.5) / (W * 0.5)) ** 2 + ((yy - H * 0.34) / (H * 0.36)) ** 2)
    spot = (np.clip(1.0 - r, 0, 1)[..., None] ** 1.3) * spotlight
    arr = arr + np.array((34, 62, 110), np.float32) * spot
    noise = np.random.default_rng(9).normal(0, 5, arr.shape)
    return Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8)).convert("RGBA")


def wink_sparkle(im, x, y, phase, scale=1.0):
    u = max(0.0, min(1.0, phase))
    if u <= 0.02 or u >= 0.98:
        return
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = int(255 * math.sin(math.pi * u))
    s = int(18 * scale * (0.7 + 0.6 * math.sin(math.pi * u)))
    # 4-point star
    pts = [
        (x, y - s),
        (x + int(s * 0.22), y - int(s * 0.22)),
        (x + s, y),
        (x + int(s * 0.22), y + int(s * 0.22)),
        (x, y + s),
        (x - int(s * 0.22), y + int(s * 0.22)),
        (x - s, y),
        (x - int(s * 0.22), y - int(s * 0.22)),
    ]
    d.polygon(pts, fill=(255, 245, 210, a))
    d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 255, 255, a))
    im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(0.6)))


def light_streak(im, phase, y0=520):
    """Diagonal cinematic light sweep."""
    u = max(0.0, min(1.0, phase))
    if u <= 0.02 or u >= 0.98:
        return
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    band_w = 120
    cx = int(-band_w + u * (W + band_w * 2))
    band = Image.new("RGBA", (band_w, H), (0, 0, 0, 0))
    px = band.load()
    for i in range(band_w):
        a = int(70 * math.sin(math.pi * i / max(1, band_w - 1)) * math.sin(math.pi * u))
        for j in range(H):
            # fade mid-frame emphasis
            fall = 1.0 - abs(j - y0) / (H * 0.55)
            aa = max(0, int(a * max(0, fall)))
            px[i, j] = (255, 248, 230, aa)
    band = band.rotate(-18, expand=True, resample=Image.Resampling.BILINEAR)
    im.alpha_composite(band, (cx - 40, -80))


def shockwave(im, cx, cy, phase):
    u = max(0.0, min(1.0, phase))
    if u <= 0.02 or u >= 0.95:
        return
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r = int(40 + u * 420)
    a = int(160 * (1 - u))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 230, 180, a), width=max(2, int(6 * (1 - u))))
    im.alpha_composite(layer)


def reflection(p, op=0.3, frac=0.34):
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


def soft_shadow(c, box, x, y, a=120):
    sh = Image.new("RGBA", (box.size[0] + 70, 64), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([10, 16, box.size[0] + 55, 46], fill=(30, 22, 14, int(a * 0.55)))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (x - 35, y + box.size[1] - 10))


def apply_logo(im, alpha, y=36, size=88):
    if alpha < 0.05:
        return
    logo = LOGO.copy()
    logo.thumbnail((size, size), Image.Resampling.LANCZOS)
    if alpha < 0.99:
        logo.putalpha(logo.split()[-1].point(lambda a: int(a * alpha)))
    im.alpha_composite(logo, ((W - logo.size[0]) // 2, y))


def text_c(im, txt, y, size, fill, alpha=255, lat=False):
    f = font(size, True, he=not lat)
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if lat:
        bb = d.textbbox((0, 0), txt, font=f)
        x = (W - (bb[2] - bb[0])) // 2 - bb[0]
        d.text((x + 2, y + 3), txt, font=f, fill=(0, 0, 0, int(80 * alpha / 255)))
        d.text((x, y), txt, font=f, fill=(*fill, alpha))
    else:
        bb = d.textbbox((0, 0), txt, font=f, language="he")
        x = (W - (bb[2] - bb[0])) // 2 - bb[0]
        d.text((x + 2, y + 3), txt, font=f, fill=(0, 0, 0, int(80 * alpha / 255)), language="he")
        d.text((x, y), txt, font=f, fill=(*fill, alpha), language="he")
    im.alpha_composite(layer)


def draw_scrubber(im, progress, months, t, alpha, zoom):
    plane_y0, plane_y1 = 210, 1380
    pw, ph = W, plane_y1 - plane_y0
    before = fit_cover(BEFORE, pw, ph, zoom=zoom).convert("RGBA")
    after = fit_cover(AFTER, pw, ph, zoom=zoom * 0.995).convert("RGBA")
    px = int(progress * pw)
    feather = 40
    xs = np.arange(pw, dtype=np.float32)
    mask_1d = np.clip((px + feather - xs) / (2.0 * feather), 0.0, 1.0)
    mask = Image.fromarray(np.tile(mask_1d * 255, (ph, 1)).astype(np.uint8), "L")
    plane = before.copy()
    plane.paste(after, (0, 0), mask)

    ov = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for i in range(150):
        a = int(165 * (1 - i / 150))
        od.line([(0, i), (pw, i)], fill=(4, 10, 20, a))
    for i in range(240):
        a = int(200 * (i / 240))
        od.line([(0, ph - 240 + i), (pw, ph - 240 + i)], fill=(4, 10, 20, a))
    plane.alpha_composite(ov)

    d = ImageDraw.Draw(plane)
    f_tag = font(24, True)
    for txt, left, bg, fg in (
        ("אחרי", True, (*GOLD, 235), (18, 14, 6, 255)),
        ("לפני", False, (8, 14, 26, 195), (*IVORY, 255)),
    ):
        tw, th, bb = text_bb(d, txt, f_tag, "he")
        pad_x, pad_y = 14, 8
        bw, bh = tw + pad_x * 2, th + pad_y * 2
        x0 = 32 if left else pw - 32 - bw
        d.rounded_rectangle([x0, 28, x0 + bw, 28 + bh], 18, fill=bg)
        draw_he(d, (x0 + pad_x - bb[0], 28 + pad_y - bb[1]), txt, f_tag, fg)

    hx = max(3, min(pw - 3, px))
    d.line([(hx, 30), (hx, ph - 30)], fill=(255, 255, 255, 240), width=3)
    kr = 34
    d.ellipse([hx - kr, ph // 2 - kr, hx + kr, ph // 2 + kr], fill=(255, 255, 255, 255), outline=(*GOLD, 255), width=4)
    cy = ph // 2
    d.polygon([(hx - 12, cy), (hx - 3, cy - 9), (hx - 3, cy + 9)], fill=(*NAVY, 255))
    d.polygon([(hx + 12, cy), (hx + 3, cy - 9), (hx + 3, cy + 9)], fill=(*NAVY, 255))

    digit, word = milestone(months)
    f_num = font(86, True, he=False)
    f_word = font(34, True)
    nw, nh, nbb = text_bb(d, digit, f_num)
    ww, wh, wbb = text_bb(d, word, f_word, "he")
    sy = ph - 200
    d.text(((pw - nw) // 2 - nbb[0], sy - nbb[1]), digit, font=f_num, fill=(*GOLD_SOFT, 255))
    draw_he(d, ((pw - ww) // 2 - wbb[0], sy + nh - 2 - wbb[1]), word, f_word, (*IVORY, 245))

    rail_y = ph - 44
    d.line([(64, rail_y), (pw - 64, rail_y)], fill=(255, 255, 255, 55), width=2)
    for mark in (0, 2, 4, 6):
        tx = int(64 + months_to_progress(mark) * (pw - 128))
        active = abs(months - mark) < 0.55 or (mark == 6 and months > 5.4)
        r = 6 if active else 3
        d.ellipse([tx - r, rail_y - r, tx + r, rail_y + r], fill=(*GOLD, 255) if active else (255, 255, 255, 120))

    if alpha < 0.99:
        plane.putalpha(plane.split()[-1].point(lambda a: int(a * alpha)))
    im.alpha_composite(plane, (0, plane_y0))


def house_outro(t_out: float) -> Image.Image:
    """Locked cream outro — same CTA geometry as foam house reels."""
    im = cream_field()
    ta = int(255 * ease_out(min(1, t_out / 0.25)))
    text_c(im, "מארז כפול קירקלנד", 200, 48, INK, ta)
    if ta > 40:
        d = ImageDraw.Draw(im)
        rw = int(150 * ease_out(min(1, (t_out - 0.1) / 0.25)))
        d.rounded_rectangle([(W - rw) // 2, 275, (W + rw) // 2, 279], 2, fill=GOLD + (ta,))
    text_c(im, "שנה של טיפול", 300, 28, (70, 74, 88), int(ta * 0.92))
    text_c(im, "מקורי מארה״ב", 340, 26, (90, 94, 108), int(ta * 0.85))

    pop = ease_out_back(min(1.0, max(0.0, (t_out - 0.15) / 0.35)))
    pop_c = max(0.0, min(1.0, pop))
    pack = PACK.copy()
    pack = ImageEnhance.Brightness(pack).enhance(1.1)
    pack = ImageEnhance.Contrast(pack).enhance(1.08)
    pack.thumbnail((700, 560), Image.Resampling.LANCZOS)
    drift = 1.0 + 0.025 * min(1, max(0, (t_out - 0.6) / 3.0))
    pw = max(1, int(pack.size[0] * (0.88 + 0.12 * pop_c) * drift))
    ph = max(1, int(pack.size[1] * (0.88 + 0.12 * pop_c) * drift))
    pp = pack.resize((pw, ph), Image.Resampling.LANCZOS)
    if pop_c < 1:
        pp.putalpha(pp.split()[-1].point(lambda a: int(a * pop_c)))
    px = (W - pw) // 2
    py = 400 + int((1 - pop_c) * 90)
    soft_shadow(im, pp, px, py, a=int(140 * pop_c))
    if pop_c > 0.5:
        im.alpha_composite(reflection(pp, op=0.30 * min(1, (pop_c - 0.5) / 0.5)), (px, py + ph - 6))
    im.alpha_composite(pp, (px, py))

    # Price chip — dual font, house style
    price_a = ease_out(min(1.0, max(0.0, (t_out - 0.45) / 0.3)))
    if price_a > 0.05:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        f_p = font(44, True, he=False)
        f_w = font(22, True, he=False)
        a = int(255 * price_a)
        price, was = "₪ 765", "₪1050"
        pw2, ph2, pbb = text_bb(d, price, f_p)
        d.text(((W - pw2) // 2 - pbb[0], 1020 - pbb[1]), price, font=f_p, fill=(*INK, a))
        ww, wh, wbb = text_bb(d, was, f_w)
        wx = (W - ww) // 2 - wbb[0]
        wy = 1020 + ph2 + 6
        d.text((wx, wy - wbb[1]), was, font=f_w, fill=(120, 124, 136, int(a * 0.85)))
        d.line([(wx - 2, wy + wh // 2), (wx + ww + 2, wy + wh // 2)], fill=(120, 124, 136, int(a * 0.9)), width=3)
        # best value
        f_b = font(22, True)
        btxt = "הכי משתלם"
        bw, bh, bbb = text_bb(d, btxt, f_b, "he")
        draw_he(d, ((W - bw) // 2 - bbb[0], wy + wh + 14), btxt, f_b, (*GOLD, a))
        im.alpha_composite(layer)

    # LOCKED CTA geometry (foam house)
    cta_a = ease_out(min(1.0, max(0.0, (t_out - 0.7) / 0.3)))
    if cta_a > 0.05:
        for idx, (txt, yy, navy) in enumerate(
            [("להזמנה עכשיו", 1380, True), ("משלוח חינם עד הבית", 1485, False)]
        ):
            f = font(34 if idx == 0 else 28)
            bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), txt, font=f, language="he")
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            pw2, ph2 = tw + 64, th + 28
            pill = Image.new("RGBA", (pw2, ph2), (0, 0, 0, 0))
            fill = NAVY + (int(245 * cta_a),) if navy else (255, 255, 255, int(245 * cta_a))
            fg = (255, 255, 255, int(255 * cta_a)) if navy else INK + (int(255 * cta_a),)
            ImageDraw.Draw(pill).rounded_rectangle([0, 0, pw2 - 1, ph2 - 1], ph2 // 2, fill=fill)
            if not navy:
                ImageDraw.Draw(pill).rounded_rectangle(
                    [1, 1, pw2 - 2, ph2 - 2], ph2 // 2, outline=NAVY + (int(160 * cta_a),), width=2
                )
            ImageDraw.Draw(pill).text((32 - bb[0], 14 - bb[1]), txt, font=f, fill=fg, language="he")
            pulse = 1.0 + (0.03 * math.sin(t_out * 6) if idx == 0 and t_out > 1.2 else 0)
            if abs(pulse - 1.0) > 0.001:
                nw, nh = int(pw2 * pulse), int(ph2 * pulse)
                pill = pill.resize((nw, nh), Image.Resampling.LANCZOS)
                pw2, ph2 = nw, nh
            im.alpha_composite(pill, ((W - pw2) // 2, yy + int((1 - cta_a) * 30)))

    # Loyalty — small, under shipping; must not fight CTA (expert-approved)
    bonus_a = ease_out(min(1.0, max(0.0, (t_out - 0.95) / 0.28)))
    if bonus_a > 0.05:
        ba = int(210 * bonus_a)
        text_c(im, "נקודות על כל קנייה", 1565, 22, (70, 74, 88), ba)
        text_c(im, "עשרה אחוז בונוס לצבירה בנובמבר", 1605, 22, GOLD, ba)

    # disclaimer
    disc_a = int(180 * cta_a)
    if disc_a > 10:
        text_c(im, "תוצאות משתנות בין אנשים", 1788, 18, (120, 124, 136), disc_a)

    apply_logo(im, 0.95 * min(1, t_out / 0.3), y=36, size=96)
    return im


def frame_at(t: float) -> Image.Image:
    # ---- HOUSE OUTRO from 9.0s ----
    if t >= 9.0:
        return house_outro(t - 9.0)

    # Crossfade into cream near end of scrubber
    scrub_fade = 1.0
    if t >= 8.45:
        scrub_fade = max(0.0, 1.0 - (t - 8.45) / 0.55)

    # ---- HOOK 0–2.2 ----
    im = navy_field(spotlight=0.55 + 0.45 * ease_out(min(1, t / 0.8)))

    # Dramatic zoom into BEFORE scalp — nearly full-bleed from frame 0
    if t < 2.35:
        zoom = 1.22 - 0.16 * ease_out(min(1, t / 1.55))
        y_bias = 0.34 + 0.05 * ease_out(min(1, t / 1.3))
        scalp_h = int(H * 0.86)
        scalp = fit_cover(BEFORE, W, scalp_h, zoom=zoom, y_bias=y_bias).convert("RGBA")
        plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        py0 = 130
        plate.alpha_composite(scalp, (0, py0))
        # Soft bottom fade into navy
        fade = Image.new("L", (W, scalp_h), 255)
        fd = ImageDraw.Draw(fade)
        for i in range(160):
            fd.line([(0, scalp_h - 160 + i), (W, scalp_h - 160 + i)], fill=int(255 * (1 - i / 160)))
        scalp2 = scalp.copy()
        scalp2.putalpha(fade)
        plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        plate.alpha_composite(scalp2, (0, py0))
        # Punch-in from slightly overscale (always visible at t=0)
        punch = 1.0 + 0.08 * (1 - ease_out(min(1, t / 0.55)))
        if punch > 1.001:
            nw, nh = int(W * punch), int(H * punch)
            plate = plate.resize((nw, nh), Image.Resampling.LANCZOS)
            plate = plate.crop(((nw - W) // 2, (nh - H) // 2, (nw - W) // 2 + W, (nh - H) // 2 + H))
        im.alpha_composite(plate)

        # FX — denser, earlier
        light_streak(im, t / 0.7, y0=640)
        light_streak(im, (t - 0.55) / 0.65, y0=880)
        wink_sparkle(im, 300, 560, (t - 0.12) / 0.5, scale=1.45)
        wink_sparkle(im, 780, 720, (t - 0.35) / 0.5, scale=1.15)
        wink_sparkle(im, 520, 500, (t - 0.55) / 0.45, scale=1.0)
        wink_sparkle(im, 640, 900, (t - 0.85) / 0.4, scale=0.9)
        if t > 0.95:
            shockwave(im, W // 2, 760, (t - 0.95) / 0.55)
        if t > 1.35:
            shockwave(im, W // 2, 760, (t - 1.35) / 0.45)

        # Handle slam-in at ~1.35s
        if t > 1.25:
            hu = ease_out_back(min(1, (t - 1.25) / 0.35))
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            hx = int(80 + (1 - hu) * -120)
            d.line([(hx, 260), (hx, 1400)], fill=(255, 255, 255, int(240 * hu)), width=4)
            kr = int(36 * hu)
            cy = 820
            d.ellipse([hx - kr, cy - kr, hx + kr, cy + kr], fill=(255, 255, 255, int(255 * hu)), outline=(*GOLD, int(255 * hu)), width=4)
            im.alpha_composite(layer)

        # Hook copy with punch scale
        hook_u = ease_out_back(min(1, max(0, (t - 0.35) / 0.4)))
        if hook_u > 0.05:
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            f1 = font(52, True)
            line = "כך השיער מתמלא"
            tw, th, bb = text_bb(d, line, f1, "he")
            scale = 0.86 + 0.14 * hook_u
            # fake scale via font size
            f1s = font(int(52 * scale), True)
            tw, th, bb = text_bb(d, line, f1s, "he")
            a = int(255 * min(1, hook_u))
            x = (W - tw) // 2 - bb[0]
            y = 100
            d.text((x, y + 4), line, font=f1s, fill=(0, 0, 0, int(120 * hook_u)), language="he")
            d.text((x, y), line, font=f1s, fill=(*IVORY, a), language="he")
            im.alpha_composite(layer)

        apply_logo(im, min(1, t / 0.4) * 0.92, y=28, size=78)

    # ---- SCRUBBER body ----
    if t >= 1.9 and scrub_fade > 0.03:
        # blend from hook navy into scrubber composition
        if t < 2.35:
            # already have im from hook; overlay scrubber rising
            pass
        else:
            im = navy_field(0.9)

        months = journey_months(t)
        progress = months_to_progress(months)
        zoom = 1.0 + 0.04 * ease_in_out(min(1.0, max(0, (t - 2.0) / 6.5)))
        body_a = scrub_fade
        if t < 2.4:
            body_a *= ease_out((t - 1.9) / 0.5)
        draw_scrubber(im, progress, months, t, body_a, zoom)
        apply_logo(im, 0.88 * body_a, y=28, size=74)

        # tiny gold sparkles during scrub advances
        if 2.5 < t < 8.2:
            wink_sparkle(im, 200 + int(progress * 600), 480, (t * 0.55) % 1.0, scale=0.7)

    # Pre-outro flash
    if 8.6 < t < 9.0:
        flash = Image.new("RGBA", (W, H), (CREAM[0], CREAM[1], CREAM[2], int(255 * ((t - 8.6) / 0.4))))
        im.alpha_composite(flash)

    return im


def main():
    print(f"v3 hook+house {N}f @{FPS}")
    for i in range(N):
        t = i / FPS
        fr = frame_at(t).convert("RGB")
        fr.save(FRAMES / f"f_{i:04d}.jpg", quality=93, optimize=True)
        if i % 60 == 0:
            print(f"frame {i} {t:.1f}s")
        if i in (0, 45, 90, 180, 360, 540, 660, 720):
            fr.save(QA / f"qa_{i:04d}.jpg", quality=92)
    print("DONE")


if __name__ == "__main__":
    main()
