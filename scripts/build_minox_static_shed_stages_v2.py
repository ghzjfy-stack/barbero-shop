#!/usr/bin/env python3
"""MinoxShop static IG post v2 — dread-shed stages, panel fixes.

Fixes: 3 visually distinct plates, bigger photos, honest timelines,
no «מקורי מארה״ב» on a no-pack educational post, keep-going closer.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path("/tmp/static-shed-v2")
ASSETS = ROOT / "assets"
OUT = ROOT / "out"
EXPORTS = Path("/agent/repos/barbero-shop/exports")
for p in (OUT, EXPORTS, ASSETS):
    p.mkdir(parents=True, exist_ok=True)

_SRC = Path("/tmp/static-shed/assets")
if _SRC.exists():
    for name in (
        "ba-before.jpg",
        "ba-after.jpg",
        "res_before.jpg",
        "res_after.jpg",
        "strip_before.jpg",
        "strip_after.jpg",
        "plate_a.jpg",
        "plate_c.jpg",
        "main-logo.png",
    ):
        if (_SRC / name).exists():
            shutil.copy2(_SRC / name, ASSETS / name)

# inset plates from results strip — kill BEFORE/AFTER chrome bars (banner ~y738+)
_strip = Path("/agent/repos/barbero-shop/minoxshop-growth-hero/assets/results-4-months.png")
if _strip.exists():
    r = Image.open(_strip).convert("RGB")
    w, h = r.size
    top, bot = 40, 720  # content only — flat banner starts ~738
    r.crop((30, top, w // 2 - 20, bot)).save(ASSETS / "plate_a.jpg", quality=93)
    r.crop((w // 2 + 20, top, w - 30, bot)).save(ASSETS / "plate_c.jpg", quality=93)

W, H = 1080, 1350

NAVY = (12, 22, 42)
NAVY_DEEP = (5, 10, 20)
GOLD = (196, 158, 86)
GOLD_SOFT = (226, 199, 135)
IVORY = (245, 246, 248)
YELLOW = (255, 220, 50)
MUTED = (140, 150, 168)

FONT_HE_B = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Bold.ttf"
FONT_HE_R = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf"


def font(size: int, bold: bool = True):
    return ImageFont.truetype(FONT_HE_B if bold else FONT_HE_R, size)


def text_bb(draw, text, fnt):
    bb = draw.textbbox((0, 0), text, font=fnt, language="he")
    return bb[2] - bb[0], bb[3] - bb[1], bb


def draw_he(d, xy, text, fnt, fill):
    d.text(xy, text, font=fnt, fill=fill, language="he")


def center_he(im, text, y, size, fill, bold=True):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(size, bold)
    tw, th, bb = text_bb(d, text, f)
    draw_he(d, ((W - tw) // 2 - bb[0], y - bb[1]), text, f, fill)
    im.alpha_composite(layer)
    return th


def trim_white(im: Image.Image) -> Image.Image:
    arr = np.asarray(im.convert("RGB"))
    bright = arr.mean(axis=2) > 230
    col = bright.mean(axis=0)
    left = next((i for i, f in enumerate(col) if f < 0.3), 0)
    right = next((i for i in range(len(col) - 1, -1, -1) if col[i] < 0.5), len(col) - 1)
    if right - left < arr.shape[1] * 0.7:
        return im
    return im.crop((left, 0, right + 1, arr.shape[0]))


def fit_square(im: Image.Image, size: int, y_bias: float = 0.38) -> Image.Image:
    w, h = im.size
    scale = max(size / w, size / h) * 1.06
    nw, nh = int(w * scale + 0.5), int(h * scale + 0.5)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - size) // 2
    y = max(0, min(nh - size, int((nh - size) * y_bias)))
    return im.crop((x, y, x + size, y + size))


def soft_blend(before: Image.Image, after: Image.Image, p: float) -> Image.Image:
    p = max(0.0, min(1.0, p))
    a = np.asarray(before).astype(np.float32)
    b = np.asarray(after).astype(np.float32)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w * 0.5) / (w * 0.50)) ** 2 + ((yy - h * 0.46) / (h * 0.44)) ** 2)
    mask = np.clip((p * 1.3 - r) / 0.30, 0, 1)
    out = a * (1 - mask[:, :, None]) + b * mask[:, :, None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def reduce_flash(im: Image.Image) -> Image.Image:
    """Pull harsh scalp glare down so density reads clearer."""
    arr = np.asarray(im).astype(np.float32)
    lum = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    glare = np.clip((lum - 110) / 90, 0, 1)
    dark = lum < 80
    hair = np.median(arr[dark], axis=0) if dark.any() else np.array([40.0, 28.0, 22.0])
    arr2 = arr * (1 - glare[:, :, None] * 0.35) + hair * (glare[:, :, None] * 0.35)
    out = Image.fromarray(np.clip(arr2, 0, 255).astype(np.uint8), "RGB")
    return ImageEnhance.Contrast(ImageEnhance.Brightness(out).enhance(1.02)).enhance(1.08)


def auto_trim_chrome(im: Image.Image) -> Image.Image:
    """Drop flat BEFORE/AFTER banners and white side rails."""
    a = np.asarray(im.convert("RGB"))
    h, w = a.shape[:2]
    bot = h
    for y in range(h - 1, h // 2, -1):
        if a[y].std() < 20 and a[y].mean() > 150:
            bot = y
        else:
            break
    top = 0
    for y in range(0, h // 4):
        if a[y].std() < 20 and a[y].mean() > 150:
            top = y + 1
        else:
            break
    left = 0
    for x in range(0, w // 4):
        if a[:, x].std() < 22 and a[:, x].mean() > 200:
            left = x + 1
        else:
            break
    right = w
    for x in range(w - 1, 3 * w // 4, -1):
        if a[:, x].std() < 22 and a[:, x].mean() > 200:
            right = x
        else:
            break
    if bot - top < h * 0.5 or right - left < w * 0.5:
        return im
    return im.crop((left, top, right, bot))


BEFORE = trim_white(Image.open(ASSETS / "ba-before.jpg").convert("RGB"))
AFTER = trim_white(Image.open(ASSETS / "ba-after.jpg").convert("RGB"))
PLATE_A = auto_trim_chrome(Image.open(ASSETS / "plate_a.jpg").convert("RGB")) if (ASSETS / "plate_a.jpg").exists() else BEFORE
PLATE_C = auto_trim_chrome(Image.open(ASSETS / "plate_c.jpg").convert("RGB")) if (ASSETS / "plate_c.jpg").exists() else AFTER
LOGO = Image.open(ASSETS / "main-logo.png").convert("RGBA")

# SAME case A→B→C — hard-crop bottom chrome, then one shared square crop
SZ = 640


def kill_bottom_banner(im: Image.Image, frac: float = 0.14) -> Image.Image:
    w, h = im.size
    return im.crop((0, 0, w, int(h * (1 - frac))))


PLATE_A = kill_bottom_banner(PLATE_A, 0.16)
PLATE_C = kill_bottom_banner(PLATE_C, 0.16)
# shared framing so A/B/C stay the same crown
BASE_A = fit_square(PLATE_A, SZ, 0.44)
BASE_C = fit_square(PLATE_C, SZ, 0.44)
EARLY = ImageEnhance.Brightness(BASE_A).enhance(1.03)
MID = soft_blend(BASE_A, BASE_C, 0.45)
LATE = soft_blend(BASE_A, BASE_C, 0.92)  # same head as A/B, clearly denser
LATE = ImageEnhance.Contrast(LATE).enhance(1.05)


def navy_bg() -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H * 0.35) / (H * 0.55)) ** 2)
    s = np.clip(1.1 - r, 0, 1) ** 1.35
    deep = np.array(NAVY_DEEP, np.float32)
    base = np.array(NAVY, np.float32)
    arr = deep + (base - deep) * s[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def wrap_he(draw, text, fnt, max_w):
    """Simple space wrap for Hebrew (logical order)."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (w + " " + cur).strip() if cur else w
        # for RTL display we still measure logical string
        tw, _, _ = text_bb(draw, trial if not cur else (cur + " " + w), fnt)
        candidate = w if not cur else cur + " " + w
        tw, _, _ = text_bb(draw, candidate, fnt)
        if tw <= max_w or not cur:
            cur = candidate
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def stage_card(photo: Image.Image, badge: str, title: str, sub: str, accent) -> Image.Image:
    """Bigger photo left — text right. Readable without fake density."""
    cw, ch = W - 72, 300
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], 26, fill=(8, 14, 28, 235))
    d.rounded_rectangle([2, 2, cw - 3, ch - 3], 24, outline=(*accent, 210), width=3)

    ph = 256
    pic = photo.resize((ph, ph), Image.Resampling.LANCZOS).convert("RGBA")
    clip = Image.new("L", (ph, ph), 0)
    ImageDraw.Draw(clip).rounded_rectangle([0, 0, ph - 1, ph - 1], 20, fill=255)
    pic.putalpha(clip)
    card.alpha_composite(pic, (18, (ch - ph) // 2))

    tx = 292
    text_w = cw - tx - 24

    f_b = font(22, True)
    tw, th, bb = text_bb(d, badge, f_b)
    bx, by = tx, 28
    d.rounded_rectangle([bx, by, bx + tw + 28, by + th + 14], 14, fill=(*accent, 235))
    draw_he(d, (bx + 14 - bb[0], by + 7 - bb[1]), badge, f_b, (12, 14, 18, 255))

    f_t = font(36, True)
    tw, th, bb = text_bb(d, title, f_t)
    draw_he(d, (tx - bb[0], 88 - bb[1]), title, f_t, (*IVORY, 255))

    f_s = font(23, False)
    lines = wrap_he(d, sub, f_s, text_w)
    yy = 150
    for line in lines[:3]:
        tw, th, bb = text_bb(d, line, f_s)
        draw_he(d, (tx - bb[0], yy - bb[1]), line, f_s, (*MUTED, 255))
        yy += th + 8
    return card


def build() -> Image.Image:
    im = navy_bg()
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([24, 24, W - 25, H - 25], 8, outline=(*GOLD, 150), width=2)

    logo = LOGO.copy()
    logo.thumbnail((80, 80), Image.Resampling.LANCZOS)
    im.alpha_composite(logo, ((W - logo.size[0]) // 2, 40))

    center_he(im, "רגע לפני שאתה מפסיק", 140, 26, GOLD_SOFT, True)
    center_he(im, "למה בהתחלה זה נראה", 185, 46, IVORY, True)
    center_he(im, "גרוע יותר", 245, 54, YELLOW, True)

    stages = [
        (
            EARLY,
            "שלב א",
            "נשירה",
            "בשבועות הראשונים השיער הישן נושר",
            (255, 120, 90),
        ),
        (
            MID,
            "שלב ב",
            "שיער חדש",
            "אחרי חודשיים עד ארבעה יוצא שיער חדש עדין",
            GOLD,
        ),
        (
            LATE,
            "שלב ג",
            "הבדל ברור",
            "בין החודש הרביעי לשישי מתחילים לראות הבדל",
            (120, 210, 140),
        ),
    ]

    y = 320
    for photo, badge, title, sub, accent in stages:
        card = stage_card(photo, badge, title, sub, accent)
        im.alpha_composite(card, (36, y))
        y += 318

    center_he(im, "ממשיכים  כי עצירה מחזירה אחורה", 1280, 26, GOLD_SOFT, True)
    center_he(im, "תוצאות משתנות בין אנשים", 1320, 20, MUTED, False)
    return im.convert("RGB")


def main():
    im = build()
    path = EXPORTS / "MinoxShop-static-shed-stages-v2.jpg"
    im.save(path, quality=95, optimize=True)
    im.save(OUT / "shed-stages-v2.jpg", quality=95)
    # also refresh canonical name for feed use
    im.save(EXPORTS / "MinoxShop-static-shed-stages.jpg", quality=95, optimize=True)
    print("WROTE", path, im.size)


if __name__ == "__main__":
    main()
