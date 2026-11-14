#!/usr/bin/env python3
"""MinoxShop scrubber Short — international grade, full-bleed, 1080x1920 @ 60fps."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/tmp/scrubber-reel")
ASSETS = ROOT / "assets"
FRAMES = ROOT / "frames"
QA = ROOT / "qa"
FRAMES.mkdir(parents=True, exist_ok=True)
QA.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1920
FPS = 60
DURATION = 12.0
N = int(DURATION * FPS)

NAVY = (15, 39, 72)
NAVY_DEEP = (8, 22, 40)
GOLD = (201, 162, 74)
GOLD_SOFT = (226, 199, 135)
IVORY = (245, 247, 251)

FONT_HE_B = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Bold.ttf"
FONT_HE_R = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf"
FONT_LAT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size: int, bold: bool = True, he: bool = True):
    if he:
        path = FONT_HE_B if bold else FONT_HE_R
    else:
        path = FONT_LAT_B
    return ImageFont.truetype(path, size)


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 0.5 * (1 - math.cos(math.pi * t))


def text_size(draw, text, fnt, language=None):
    kw = {"language": language} if language else {}
    bb = draw.textbbox((0, 0), text, font=fnt, **kw)
    return bb[2] - bb[0], bb[3] - bb[1], bb


BEFORE_SRC = ImageEnhance.Contrast(Image.open(ASSETS / "ba-before.jpg").convert("RGB")).enhance(1.06)
AFTER_SRC = ImageEnhance.Contrast(Image.open(ASSETS / "ba-after.jpg").convert("RGB")).enhance(1.1)
LOGO = Image.open(ASSETS / "main-logo.png").convert("RGBA")
PACK = Image.open(ASSETS / "rogaine-double-man.png").convert("RGBA")


def fit_cover(im: Image.Image, tw: int, th: int, y_bias: float = 0.38) -> Image.Image:
    w, h = im.size
    scale = max(tw / w, th / h)
    nw, nh = int(w * scale + 0.5), int(h * scale + 0.5)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - tw) // 2
    y = int((nh - th) * y_bias)
    y = max(0, min(nh - th, y))
    return im.crop((x, y, x + tw, y + th))


def months_to_progress(m: float) -> float:
    t = max(0.0, min(1.0, m / 6.0))
    return t ** 0.82


def month_label(m: float):
    # Snap display to honest manufacturer milestones
    if m < 1.0:
        return "0", "חודש 0", "תחילת הדרך"
    if m < 3.0:
        return "2", "חודש 2", "השיער מתחיל להתחזק"
    if m < 5.35:
        return "4", "חודש 4", "צפיפות ניכרת מהשטח"
    return "6", "חודש 6", "תוצאה מלאה יותר"


def journey_months(t: float) -> float:
    """0–8.6s: hold → accelerate → settle at 6."""
    t0, t1 = 0.35, 8.6
    if t <= t0:
        return 0.05
    u = ease_in_out(min(1.0, (t - t0) / (t1 - t0)))
    # Slight pause sensation around month 4
    if u < 0.62:
        return 0.05 + (u / 0.62) * 3.95
    return 4.0 + ((u - 0.62) / 0.38) * 2.0


def navy_wash() -> Image.Image:
    arr = np.zeros((H, W, 3), dtype=np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    # deep navy with soft spotlight behind scalp area
    arr[:] = np.array(NAVY_DEEP, dtype=np.float32)
    cx, cy = W * 0.5, H * 0.36
    r = np.sqrt(((xx - cx) / (W * 0.55)) ** 2 + ((yy - cy) / (H * 0.42)) ** 2)
    spot = np.clip(1.0 - r, 0, 1)[..., None]
    lift = np.array((36, 64, 110), dtype=np.float32)
    arr = arr * (1 - spot * 0.45) + (arr + lift) * (spot * 0.45)
    noise = np.random.default_rng(3).normal(0, 6, arr.shape)
    arr = np.clip(arr + noise, 0, 255)
    return Image.fromarray(arr.astype(np.uint8)).convert("RGBA")


def draw_scrubber_fullbleed(im: Image.Image, progress: float, months: float, pulse: float, alpha: float = 1.0):
    """Dominant edge-to-edge visual plane — international BA scrubber look."""
    # Media plane: full width, tall, slightly inset from top logo / bottom CTA
    plane_y0, plane_y1 = 210, 1380
    pw, ph = W, plane_y1 - plane_y0

    before = fit_cover(BEFORE_SRC, pw, ph).convert("RGBA")
    after = fit_cover(AFTER_SRC, pw, ph).convert("RGBA")

    px = int(progress * pw)
    feather = 36
    xs = np.arange(pw, dtype=np.float32)
    mask_1d = np.clip((px + feather - xs) / (2.0 * feather), 0.0, 1.0)
    mask = Image.fromarray(np.tile(mask_1d * 255, (ph, 1)).astype(np.uint8), "L")

    plane = before.copy()
    plane.paste(after, (0, 0), mask)

    # Cinematic letterbox gradients on plane
    ov = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for i in range(130):
        a = int(150 * (1 - i / 130))
        od.line([(0, i), (pw, i)], fill=(5, 12, 24, a))
    for i in range(220):
        a = int(190 * (i / 220))
        od.line([(0, ph - 220 + i), (pw, ph - 220 + i)], fill=(5, 12, 24, a))
    plane.alpha_composite(ov)

    d = ImageDraw.Draw(plane)

    # Tags
    f_tag = font(26, True)
    for txt, left_side, bg, fg in (
        ("אחרי", True, GOLD + (235,), (20, 16, 8, 255)),
        ("לפני", False, (10, 18, 32, 190), IVORY + (255,)),
    ):
        tw, th, bb = text_size(d, txt, f_tag, "he")
        pad_x, pad_y = 16, 9
        bw, bh = tw + pad_x * 2, th + pad_y * 2
        x0 = 28 if left_side else pw - 28 - bw
        y0 = 28
        d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], 20, fill=bg)
        d.text((x0 + pad_x - bb[0], y0 + pad_y - bb[1]), txt, font=f_tag, fill=fg, language="he")

    # Handle
    hx = max(2, min(pw - 2, px))
    d.line([(hx, 24), (hx, ph - 24)], fill=(255, 255, 255, 235), width=3)
    for rad, a in ((26, 35), (14, 60)):
        d.ellipse([hx - rad, ph // 2 - rad, hx + rad, ph // 2 + rad], fill=(255, 255, 255, a))
    kr = int(32 + 2.5 * math.sin(pulse * math.pi * 2))
    d.ellipse(
        [hx - kr, ph // 2 - kr, hx + kr, ph // 2 + kr],
        fill=(255, 255, 255, 255),
        outline=GOLD + (255,),
        width=4,
    )
    cy = ph // 2
    d.polygon([(hx - 11, cy), (hx - 2, cy - 8), (hx - 2, cy + 8)], fill=NAVY + (255,))
    d.polygon([(hx + 11, cy), (hx + 2, cy - 8), (hx + 2, cy + 8)], fill=NAVY + (255,))

    # Month HUD — large, international clarity
    _digit, word, hint = month_label(months)
    f_m = font(48, True)
    f_h = font(28, False)
    tw, th, bb = text_size(d, word, f_m, "he")
    hw, hh, hbb = text_size(d, hint, f_h, "he")
    block_w = max(tw, hw) + 56
    block_h = th + hh + 34
    bx = (pw - block_w) // 2
    by = ph - block_h - 36
    d.rounded_rectangle([bx, by, bx + block_w, by + block_h], 26, fill=(8, 22, 40, 210))
    d.text((bx + (block_w - tw) // 2 - bb[0], by + 12 - bb[1]), word, font=f_m, fill=GOLD_SOFT + (255,), language="he")
    d.text(
        (bx + (block_w - hw) // 2 - hbb[0], by + 16 + th - hbb[1]),
        hint,
        font=f_h,
        fill=(220, 226, 236, 235),
        language="he",
    )

    # Tick rail
    rail_y = ph - 16
    d.line([(48, rail_y), (pw - 48, rail_y)], fill=(255, 255, 255, 70), width=2)
    for mark in (0, 2, 4, 6):
        tx = int(48 + months_to_progress(mark) * (pw - 96))
        active = abs(months - mark) <= 0.65 or (mark == 6 and months > 5.2)
        r = 7 if active else 4
        col = GOLD + (255,) if active else (255, 255, 255, 150)
        d.ellipse([tx - r, rail_y - r, tx + r, rail_y + r], fill=col)
        # tiny digit under active marks via Latin font for crispness
        if active:
            f_num = font(18, True, he=False)
            num = str(mark)
            nw, nh, nbb = text_size(d, num, f_num)
            d.text((tx - nw // 2 - nbb[0], rail_y - r - nh - 6 - nbb[1]), num, font=f_num, fill=GOLD_SOFT + (255,))

    if alpha < 0.99:
        plane.putalpha(plane.split()[-1].point(lambda a: int(a * alpha)))

    # Soft shadow under plane edge
    im.alpha_composite(plane, (0, plane_y0))
    return im


def apply_logo(im: Image.Image, alpha: float = 1.0, y: int = 42, size: int = 86):
    if alpha < 0.05:
        return
    logo = LOGO.copy()
    logo.thumbnail((size, size), Image.Resampling.LANCZOS)
    if alpha < 0.99:
        logo.putalpha(logo.split()[-1].point(lambda a: int(a * alpha)))
    im.alpha_composite(logo, ((W - logo.size[0]) // 2, y))


def frame_at(t: float) -> Image.Image:
    im = navy_wash()
    months = journey_months(t)
    progress = months_to_progress(months)

    # Scrubber dominates from first frame
    fade_out = 1.0
    if t >= 9.0:
        fade_out = max(0.0, 1.0 - (t - 9.0) / 0.7)
    if fade_out > 0.02:
        draw_scrubber_fullbleed(im, progress, months, pulse=(t * 0.65) % 1.0, alpha=fade_out)

    # Hook line above plane (safe from TikTok username)
    hook_a = 1.0
    if t > 2.0:
        hook_a = max(0.0, 1.0 - (t - 2.0) / 0.45)
    if hook_a > 0.04:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        f1 = font(46, True)
        line = "כך השיער מתמלא"
        tw, th, bb = text_size(d, line, f1, "he")
        a = int(255 * hook_a)
        x = (W - tw) // 2 - bb[0]
        y = 118
        d.text((x, y + 3), line, font=f1, fill=(0, 0, 0, int(120 * hook_a)), language="he")
        d.text((x, y), line, font=f1, fill=(*IVORY, a), language="he")
        im.alpha_composite(layer)

    apply_logo(im, alpha=0.92 if t < 9.2 else max(0.0, 0.92 * (1 - (t - 9.2) / 0.4)), y=28, size=82)

    # Brand wordmark tiny under logo during body
    if t < 9.0:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        f = font(20, True, he=False)
        txt = "MinoxShop"
        tw, th, bb = text_size(d, txt, f)
        d.text(((W - tw) // 2 - bb[0], 118), txt, font=f, fill=(226, 199, 135, 200))
        # conflict with hook — only show after hook fades
        if t > 2.3:
            aa = min(1.0, (t - 2.3) / 0.35)
            layer.putalpha(layer.split()[-1].point(lambda a: int(a * aa)))
            im.alpha_composite(layer)

    # OUTRO 9.2–12.0
    if t >= 9.0:
        u = ease_out(min(1.0, (t - 9.0) / 0.55))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)

        # Focused product
        pack = PACK.copy()
        pack.thumbnail((520, 420), Image.Resampling.LANCZOS)
        pack.putalpha(pack.split()[-1].point(lambda a: int(a * u)))
        px = (W - pack.size[0]) // 2
        py = 420 + int((1 - u) * 40)
        # reflection-ish blur strip
        shadow = Image.new("RGBA", (pack.size[0] + 60, 40), (0, 0, 0, 0))
        ImageDraw.Draw(shadow).ellipse([0, 0, pack.size[0] + 60, 40], fill=(0, 0, 0, int(80 * u)))
        shadow = shadow.filter(ImageFilter.GaussianBlur(12))
        im.alpha_composite(shadow, (px - 30, py + pack.size[1] - 10))
        im.alpha_composite(pack, (px, py))

        f_line = font(40, True)
        line = "מארז כפול לחצי שנה"
        tw, th, bb = text_size(d, line, f_line, "he")
        a = int(255 * u)
        d.text(((W - tw) // 2 - bb[0], py + pack.size[1] + 28), line, font=f_line, fill=(*IVORY, a), language="he")

        f_cta = font(44, True)
        cta = "להזמנה עכשיו"
        tw, th, bb = text_size(d, cta, f_cta, "he")
        btn_w, btn_h = tw + 78, th + 38
        pulse = 1.0 + 0.02 * math.sin(t * 5.2)
        bw, bh = int(btn_w * pulse), int(btn_h * pulse)
        bx = (W - bw) // 2
        by = 1480
        d.rounded_rectangle([bx, by, bx + bw, by + bh], bh // 2, fill=(32, 96, 200, a))
        d.text((bx + (bw - tw) // 2 - bb[0], by + (bh - th) // 2 - bb[1]), cta, font=f_cta, fill=(255, 255, 255, a), language="he")

        f_sub = font(26, False)
        sub = "משלוח חינם עד הבית · מקורי מארה״ב"
        sw, sh, sbb = text_size(d, sub, f_sub, "he")
        d.text(((W - sw) // 2 - sbb[0], by + bh + 20), sub, font=f_sub, fill=(210, 218, 230, int(230 * u)), language="he")

        f_d = font(20, False)
        disc = "תוצאות משתנות בין אנשים"
        dw, dh, dbb = text_size(d, disc, f_d, "he")
        d.text(((W - dw) // 2 - dbb[0], 1840), disc, font=f_d, fill=(150, 160, 175, int(210 * u)), language="he")

        apply_logo(im, alpha=0.95 * u, y=48, size=96)
        im.alpha_composite(layer)

    return im


def main():
    print(f"scrubber reel v2 {N} frames @ {FPS}fps")
    for i in range(N):
        t = i / FPS
        fr = frame_at(t).convert("RGB")
        fr.save(FRAMES / f"f_{i:04d}.jpg", quality=93, optimize=True)
        if i % 60 == 0:
            print(f"frame {i} {t:.2f}s")
        if i in (0, 60, 240, 420, 540, 660):
            fr.save(QA / f"qa_{i:04d}.jpg", quality=92)
    print("DONE")


if __name__ == "__main__":
    main()
