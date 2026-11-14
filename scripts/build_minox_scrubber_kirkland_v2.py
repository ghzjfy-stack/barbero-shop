#!/usr/bin/env python3
"""MinoxShop scrubber Short v2 — Kirkland double liquid, international craft."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/tmp/scrubber-v2")
ASSETS = ROOT / "assets"
FRAMES = ROOT / "frames"
QA = ROOT / "qa"
FRAMES.mkdir(exist_ok=True)
QA.mkdir(exist_ok=True)

W, H = 1080, 1920
FPS = 60
DURATION = 12.0
N = int(DURATION * FPS)

NAVY = (10, 22, 40)
NAVY_MID = (21, 40, 72)
GOLD = (201, 162, 74)
GOLD_SOFT = (226, 199, 135)
IVORY = (243, 245, 248)

FONT_HE_B = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Bold.ttf"
FONT_HE_R = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf"
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


def text_bb(draw, text, fnt, language=None):
    kw = {"language": language} if language else {}
    bb = draw.textbbox((0, 0), text, font=fnt, **kw)
    return bb[2] - bb[0], bb[3] - bb[1], bb


def load_rgb(path: Path, contrast=1.0):
    im = Image.open(path).convert("RGB")
    if contrast != 1.0:
        im = ImageEnhance.Contrast(im).enhance(contrast)
    return im


BEFORE = load_rgb(ASSETS / "ba-before.jpg", 1.08)
AFTER = load_rgb(ASSETS / "ba-after.jpg", 1.12)
LOGO = Image.open(ASSETS / "main-logo.png").convert("RGBA")


def prep_pack() -> Image.Image:
    path = ASSETS / "kirkland-double-composed.png"
    if not path.exists():
        path = ASSETS / "kirkland-liquid-double.png"
    im = Image.open(path).convert("RGBA")
    arr = np.array(im).astype(np.float32)
    rgb, a = arr[:, :, :3], arr[:, :, 3]
    lum = rgb.mean(axis=2)
    chroma = rgb.max(axis=2) - rgb.min(axis=2)
    bg = ((lum > 235) & (chroma < 18)) | ((rgb[:, :, 0] > 248) & (rgb[:, :, 1] > 248) & (rgb[:, :, 2] > 248))
    a[bg] = 0
    soft = (lum > 210) & (lum <= 235) & (chroma < 22)
    a[soft] = a[soft] * np.clip((235 - lum[soft]) / 25.0, 0, 1)
    arr[:, :, 3] = a
    return Image.fromarray(arr.astype(np.uint8))


PACK = prep_pack()


def fit_cover(im: Image.Image, tw: int, th: int, zoom: float = 1.0, y_bias: float = 0.40) -> Image.Image:
    w, h = im.size
    scale = max(tw / w, th / h) * zoom
    nw, nh = int(w * scale + 0.5), int(h * scale + 0.5)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - tw) // 2
    y = int((nh - th) * y_bias)
    y = max(0, min(nh - th, y))
    return im.crop((x, y, x + tw, y + th))


def months_to_progress(m: float) -> float:
    t = max(0.0, min(1.0, m / 6.0))
    return t ** 0.82


def journey_months(t: float) -> float:
    # 0.4–8.4s with soft holds near 2 and 4
    t0, t1 = 0.40, 8.40
    if t <= t0:
        return 0.0
    u = ease_in_out(min(1.0, (t - t0) / (t1 - t0)))
    # piecewise for editorial holds
    keys = [(0.0, 0.0), (0.22, 2.0), (0.28, 2.0), (0.55, 4.0), (0.62, 4.0), (1.0, 6.0)]
    for (u0, m0), (u1, m1) in zip(keys, keys[1:]):
        if u <= u1:
            local = 0 if u1 == u0 else (u - u0) / (u1 - u0)
            return m0 + (m1 - m0) * local
    return 6.0


def milestone(m: float):
    """Latin digit + short Hebrew word only (no restated number words)."""
    if m < 1.0:
        return "0", "התחלה"
    if m < 3.0:
        return "2", "חודשיים"
    if m < 5.2:
        return "4", "צפיפות ניכרת"
    return "6", "תוצאה מלאה יותר"


def atmosphere() -> Image.Image:
    arr = np.zeros((H, W, 3), dtype=np.float32)
    arr[:] = NAVY
    yy, xx = np.mgrid[0:H, 0:W]
    # cool spotlight behind scalp
    r = np.sqrt(((xx - W * 0.5) / (W * 0.52)) ** 2 + ((yy - H * 0.34) / (H * 0.38)) ** 2)
    spot = np.clip(1.0 - r, 0, 1)[..., None] ** 1.35
    lift = np.array((28, 55, 98), dtype=np.float32)
    arr = arr + lift * spot * 0.85
    # bottom stage for outro
    fade = np.clip((yy - H * 0.55) / (H * 0.45), 0, 1)[..., None]
    deep = np.array((6, 12, 22), dtype=np.float32)
    arr = arr * (1 - fade * 0.35) + deep * (fade * 0.35)
    noise = np.random.default_rng(11).normal(0, 5.5, arr.shape)
    return Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8)).convert("RGBA")


def draw_he(d, xy, text, fnt, fill, language="he"):
    d.text(xy, text, font=fnt, fill=fill, language=language)


def apply_logo(im: Image.Image, alpha: float, y: int = 36, size: int = 78):
    if alpha < 0.05:
        return
    logo = LOGO.copy()
    logo.thumbnail((size, size), Image.Resampling.LANCZOS)
    if alpha < 0.99:
        logo.putalpha(logo.split()[-1].point(lambda a: int(a * alpha)))
    im.alpha_composite(logo, ((W - logo.size[0]) // 2, y))


def draw_scrubber(im: Image.Image, progress: float, months: float, t: float, alpha: float, zoom: float):
    plane_y0, plane_y1 = 200, 1420
    pw, ph = W, plane_y1 - plane_y0

    before = fit_cover(BEFORE, pw, ph, zoom=zoom, y_bias=0.40).convert("RGBA")
    after = fit_cover(AFTER, pw, ph, zoom=zoom * 0.995, y_bias=0.40).convert("RGBA")

    px = int(progress * pw)
    feather = 40
    xs = np.arange(pw, dtype=np.float32)
    mask_1d = np.clip((px + feather - xs) / (2.0 * feather), 0.0, 1.0)
    mask = Image.fromarray(np.tile(mask_1d * 255, (ph, 1)).astype(np.uint8), "L")
    plane = before.copy()
    plane.paste(after, (0, 0), mask)

    # cinematic letterbox
    ov = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for i in range(160):
        a = int(170 * (1 - i / 160))
        od.line([(0, i), (pw, i)], fill=(4, 10, 20, a))
    for i in range(260):
        a = int(210 * (i / 260))
        od.line([(0, ph - 260 + i), (pw, ph - 260 + i)], fill=(4, 10, 20, a))
    plane.alpha_composite(ov)

    d = ImageDraw.Draw(plane)

    # Editorial corner tags — small, not noisy
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

    # Handle — thin blade + gold ring
    hx = max(3, min(pw - 3, px))
    d.line([(hx, 30), (hx, ph - 30)], fill=(255, 255, 255, 240), width=3)
    pulse = 0.5 + 0.5 * math.sin(t * 4.2)
    for rad, a in ((30, 22 + int(10 * pulse)), (16, 48)):
        d.ellipse([hx - rad, ph // 2 - rad, hx + rad, ph // 2 + rad], fill=(255, 255, 255, a))
    kr = 34
    d.ellipse([hx - kr, ph // 2 - kr, hx + kr, ph // 2 + kr], fill=(255, 255, 255, 255), outline=(*GOLD, 255), width=4)
    cy = ph // 2
    d.polygon([(hx - 12, cy), (hx - 3, cy - 9), (hx - 3, cy + 9)], fill=(*NAVY, 255))
    d.polygon([(hx + 12, cy), (hx + 3, cy - 9), (hx + 3, cy + 9)], fill=(*NAVY, 255))

    # Editorial milestone — NO pill box: big Latin numeral + Hebrew word in letterbox
    digit, word = milestone(months)
    f_num = font(86, True, he=False)
    f_word = font(34, True)
    nw, nh, nbb = text_bb(d, digit, f_num)
    ww, wh, wbb = text_bb(d, word, f_word, "he")
    # centered stack above bottom letterbox
    stack_h = nh + wh + 10
    sy = ph - 210
    nx = (pw - nw) // 2 - nbb[0]
    d.text((nx + 2, sy + 3 - nbb[1]), digit, font=f_num, fill=(0, 0, 0, 90))
    d.text((nx, sy - nbb[1]), digit, font=f_num, fill=(*GOLD_SOFT, 255))
    wx = (pw - ww) // 2 - wbb[0]
    draw_he(d, (wx, sy + nh - 4 - wbb[1]), word, f_word, (*IVORY, 245))

    # Quiet tick rail — only active mark labeled
    rail_y = ph - 48
    d.line([(64, rail_y), (pw - 64, rail_y)], fill=(255, 255, 255, 55), width=2)
    for mark in (0, 2, 4, 6):
        tx = int(64 + months_to_progress(mark) * (pw - 128))
        active = abs(months - mark) < 0.55 or (mark == 6 and months > 5.4)
        r = 6 if active else 3
        col = (*GOLD, 255) if active else (255, 255, 255, 120)
        d.ellipse([tx - r, rail_y - r, tx + r, rail_y + r], fill=col)

    if alpha < 0.99:
        plane.putalpha(plane.split()[-1].point(lambda a: int(a * alpha)))
    im.alpha_composite(plane, (0, plane_y0))


def draw_price_block(layer: Image.Image, y: int, alpha: int):
    """Dual-font price: ₪ left via DejaVu, Hebrew savings via Noto."""
    d = ImageDraw.Draw(layer)
    f_price = font(58, True, he=False)
    f_was = font(24, True, he=False)
    f_pill_he = font(22, True)
    f_pill_lat = font(22, True, he=False)
    price = "₪ 765"
    was = "₪1050"
    pw, ph, pbb = text_bb(d, price, f_price)
    x = (W - pw) // 2 - pbb[0]
    d.text((x, y + 3 - pbb[1]), price, font=f_price, fill=(0, 0, 0, int(alpha * 0.4)))
    d.text((x, y - pbb[1]), price, font=f_price, fill=(*IVORY, alpha))
    ww, wh, wbb = text_bb(d, was, f_was)
    wx = (W - ww) // 2 - wbb[0]
    wy = y + ph + 10
    d.text((wx, wy - wbb[1]), was, font=f_was, fill=(150, 158, 172, int(alpha * 0.85)))
    mid = wy + wh // 2
    d.line([(wx - 2, mid), (wx + ww + 2, mid)], fill=(150, 158, 172, int(alpha * 0.9)), width=3)

    # Savings pill — LTR amount then Hebrew
    he = "חיסכון"
    amt = "₪285"
    hb = text_bb(d, he, f_pill_he, "he")
    ab = text_bb(d, amt, f_pill_lat)
    gap, pad_x, pad_y = 10, 18, 10
    pill_w = ab[0] + gap + hb[0] + pad_x * 2
    pill_h = max(ab[1], hb[1]) + pad_y * 2
    pill = Image.new("RGBA", (pill_w, pill_h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle([0, 0, pill_w - 1, pill_h - 1], pill_h // 2, fill=(201, 162, 74, int(alpha * 0.95)))
    pd.text((pad_x - ab[2][0], (pill_h - ab[1]) // 2 - ab[2][1]), amt, font=f_pill_lat, fill=(18, 14, 6, alpha))
    pd.text(
        (pad_x + ab[0] + gap - hb[2][0], (pill_h - hb[1]) // 2 - hb[2][1]),
        he,
        font=f_pill_he,
        fill=(18, 14, 6, alpha),
        language="he",
    )
    layer.alpha_composite(pill, ((W - pill_w) // 2, wy + wh + 16))

    badge = "הכי משתלם"
    f_b = font(22, True)
    bw, bh, bbb = text_bb(d, badge, f_b, "he")
    draw_he(d, ((W - bw) // 2 - bbb[0], wy + wh + 16 + pill_h + 14), badge, f_b, (*GOLD_SOFT, alpha))


def frame_at(t: float) -> Image.Image:
    im = atmosphere()
    months = journey_months(t)
    progress = months_to_progress(months)
    # Slow Ken Burns on scalp
    zoom = 1.0 + 0.045 * ease_in_out(min(1.0, t / 8.4))

    # Scrubber clears fully before CTA
    fade = 1.0
    if t >= 8.45:
        fade = max(0.0, 1.0 - (t - 8.45) / 0.5)
    if fade > 0.03:
        draw_scrubber(im, progress, months, t, fade, zoom)

    # Hook — one line only
    hook_a = 1.0 if t < 1.9 else max(0.0, 1.0 - (t - 1.9) / 0.4)
    if t < 0.15:
        hook_a *= ease_out(t / 0.15)
    if hook_a > 0.04 and fade > 0.5:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        f1 = font(48, True)
        line = "כך השיער מתמלא"
        tw, th, bb = text_bb(d, line, f1, "he")
        a = int(255 * hook_a)
        x = (W - tw) // 2 - bb[0]
        y = 112
        d.text((x, y + 3), line, font=f1, fill=(0, 0, 0, int(110 * hook_a)), language="he")
        d.text((x, y), line, font=f1, fill=(*IVORY, a), language="he")
        im.alpha_composite(layer)

    # Logo during scrubber (small)
    if t < 8.6:
        la = min(1.0, t / 0.3) * (1.0 if t < 8.2 else max(0, 1 - (t - 8.2) / 0.35))
        apply_logo(im, 0.9 * la, y=28, size=74)

    # OUTRO — Kirkland double
    if t >= 8.95:
        u = ease_out(min(1.0, (t - 8.95) / 0.5))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        a = int(255 * u)

        apply_logo(im, 0.95 * u, y=48, size=92)

        pack = PACK.copy()
        pack.thumbnail((640, 520), Image.Resampling.LANCZOS)
        pack = ImageEnhance.Brightness(pack).enhance(1.12)
        pack = ImageEnhance.Contrast(pack).enhance(1.08)
        pack.putalpha(pack.split()[-1].point(lambda x: int(x * u)))
        px = (W - pack.size[0]) // 2
        py = 200 + int((1 - u) * 30)
        # soft ground shadow
        sh = Image.new("RGBA", (pack.size[0] + 80, 50), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([0, 0, pack.size[0] + 80, 50], fill=(0, 0, 0, int(90 * u)))
        sh = sh.filter(ImageFilter.GaussianBlur(14))
        im.alpha_composite(sh, (px - 40, py + pack.size[1] - 8))
        im.alpha_composite(pack, (px, py))

        f_title = font(36, True)
        title = "מארז כפול קירקלנד לגברים"
        tw, th, bb = text_bb(d, title, f_title, "he")
        draw_he(d, ((W - tw) // 2 - bb[0], py + pack.size[1] + 18), title, f_title, (*IVORY, a))

        f_sub = font(26, False)
        sub = "שנה של טיפול"
        sw, shh, sbb = text_bb(d, sub, f_sub, "he")
        draw_he(d, ((W - sw) // 2 - sbb[0], py + pack.size[1] + 18 + th + 8), sub, f_sub, (190, 198, 210, int(230 * u)))

        price_y = py + pack.size[1] + 18 + th + 8 + 40
        draw_price_block(layer, price_y, a)

        # CTA sits tight under price (TikTok-safe, ~y 1180)
        f_cta = font(42, True)
        cta = "להזמנה עכשיו"
        cw, ch, cbb = text_bb(d, cta, f_cta, "he")
        pulse = 1.0 + 0.018 * math.sin(t * 5.0)
        bw, bh = int((cw + 76) * pulse), int((ch + 36) * pulse)
        bx = (W - bw) // 2
        by = min(1280, price_y + 250)
        d.rounded_rectangle([bx, by, bx + bw, by + bh], bh // 2, fill=(32, 96, 200, a))
        draw_he(d, (bx + (bw - cw) // 2 - cbb[0], by + (bh - ch) // 2 - cbb[1]), cta, f_cta, (255, 255, 255, a))

        f_ship = font(24, False)
        ship = "משלוח חינם עד הבית"
        sw, shh, sbb = text_bb(d, ship, f_ship, "he")
        draw_he(d, ((W - sw) // 2 - sbb[0], by + bh + 14), ship, f_ship, (200, 208, 220, int(230 * u)))
        ship2 = "מקורי מארה״ב"
        s2w, s2h, s2bb = text_bb(d, ship2, f_ship, "he")
        draw_he(d, ((W - s2w) // 2 - s2bb[0], by + bh + 14 + s2h + 2), ship2, f_ship, (180, 190, 205, int(210 * u)))

        f_d = font(18, False)
        disc = "תוצאות משתנות בין אנשים"
        dw, dh, dbb = text_bb(d, disc, f_d, "he")
        draw_he(d, ((W - dw) // 2 - dbb[0], min(1720, by + bh + 100)), disc, f_d, (140, 150, 165, int(200 * u)))

        im.alpha_composite(layer)

    return im


def main():
    print(f"v2 kirkland scrubber {N}f @{FPS}")
    for i in range(N):
        t = i / FPS
        fr = frame_at(t).convert("RGB")
        fr.save(FRAMES / f"f_{i:04d}.jpg", quality=93, optimize=True)
        if i % 60 == 0:
            print(f"frame {i} {t:.1f}s")
        if i in (0, 90, 240, 420, 540, 660):
            fr.save(QA / f"qa_{i:04d}.jpg", quality=92)
    print("DONE")


if __name__ == "__main__":
    main()
