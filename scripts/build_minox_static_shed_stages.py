#!/usr/bin/env python3
"""MinoxShop static IG post — dread-shed stages (same energy as growth timeline, new angle).

Scroll-stop idea: people panic when hair sheds first. Flip the growth-stages format
into «why it looks worse before it looks better».
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/tmp/static-shed")
ASSETS = ROOT / "assets"
OUT = ROOT / "out"
EXPORTS = Path("/agent/repos/barbero-shop/exports")
for p in (OUT, EXPORTS, ASSETS):
    p.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1350  # IG portrait feed

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
    scale = max(size / w, size / h) * 1.04
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
    r = np.sqrt(((xx - w * 0.5) / (w * 0.48)) ** 2 + ((yy - h * 0.45) / (h * 0.42)) ** 2)
    mask = np.clip((p * 1.25 - r) / 0.28, 0, 1)
    out = a * (1 - mask[:, :, None]) + b * mask[:, :, None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


BEFORE = Image.open(ASSETS / "ba-before.jpg").convert("RGB")
AFTER = trim_white(Image.open(ASSETS / "ba-after.jpg").convert("RGB"))
AFTER = ImageEnhance.Brightness(AFTER).enhance(1.06)
AFTER = ImageEnhance.Contrast(AFTER).enhance(1.08)
LOGO = Image.open(ASSETS / "main-logo.png").convert("RGBA")

MID = soft_blend(fit_square(BEFORE, 520, 0.40), fit_square(AFTER, 520, 0.38), 0.42)
EARLY = ImageEnhance.Contrast(fit_square(BEFORE, 520, 0.42)).enhance(1.05)
LATE = fit_square(AFTER, 520, 0.36)


def navy_bg() -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.7)) ** 2 + ((yy - H * 0.35) / (H * 0.55)) ** 2)
    s = np.clip(1.1 - r, 0, 1) ** 1.35
    deep = np.array(NAVY_DEEP, np.float32)
    base = np.array(NAVY, np.float32)
    arr = deep + (base - deep) * s[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def stage_card(photo: Image.Image, badge: str, title: str, sub: str, accent) -> Image.Image:
    """One horizontal stage row: photo left, copy right — or stacked for feed."""
    cw, ch = W - 80, 280
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], 24, fill=(8, 14, 28, 230))
    d.rounded_rectangle([2, 2, cw - 3, ch - 3], 22, outline=(*accent, 200), width=2)

    ph = 220
    pic = photo.resize((ph, ph), Image.Resampling.LANCZOS).convert("RGBA")
    clip = Image.new("L", (ph, ph), 0)
    ImageDraw.Draw(clip).rounded_rectangle([0, 0, ph - 1, ph - 1], 18, fill=255)
    pic.putalpha(clip)
    card.alpha_composite(pic, (24, (ch - ph) // 2))

    # badge
    f_b = font(22, True)
    tw, th, bb = text_bb(d, badge, f_b)
    bx, by = 270, 36
    d.rounded_rectangle([bx, by, bx + tw + 28, by + th + 16], 14, fill=(*accent, 230))
    draw_he(d, (bx + 14 - bb[0], by + 8 - bb[1]), badge, f_b, (12, 14, 18, 255))

    f_t = font(34, True)
    tw, th, bb = text_bb(d, title, f_t)
    draw_he(d, (270 - bb[0], 100 - bb[1]), title, f_t, (*IVORY, 255))

    f_s = font(24, False)
    tw, th, bb = text_bb(d, sub, f_s)
    draw_he(d, (270 - bb[0], 160 - bb[1]), sub, f_s, (*MUTED, 255))
    return card


def build() -> Image.Image:
    im = navy_bg()

    # gold frame
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([28, 28, W - 29, H - 29], 8, outline=(*GOLD, 160), width=2)

    # logo
    logo = LOGO.copy()
    logo.thumbnail((88, 88), Image.Resampling.LANCZOS)
    im.alpha_composite(logo, ((W - logo.size[0]) // 2, 48))

    # hook headline — pain of the panic moment
    center_he(im, "רגע לפני שאתה מפסיק", 160, 28, GOLD_SOFT, True)
    center_he(im, "למה בהתחלה זה נראה", 210, 48, IVORY, True)
    center_he(im, "גרוע יותר", 275, 56, YELLOW, True)

    stages = [
        (EARLY, "שלב א", "נשירה זמנית", "שבועות ראשונים  השיער הישן נושר", (255, 120, 90)),
        (MID, "שלב ב", "בייבי הייר", "חודש־חודשיים  השיער החדש יוצא", GOLD),
        (LATE, "שלב ג", "צפיפות חוזרת", "ארבעה חודשים  רואים הבדל אמיתי", (120, 210, 140)),
    ]

    y = 360
    for photo, badge, title, sub, accent in stages:
        card = stage_card(photo, badge, title, sub, accent)
        im.alpha_composite(card, (40, y))
        y += 300

    # bottom trust line
    center_he(im, "זה לא נסיגה  זה השלב הראשון של הצמיחה", 1265, 26, GOLD_SOFT, True)
    center_he(im, "תוצאות משתנות בין אנשים  מקורי מארה״ב", 1305, 20, MUTED, False)
    return im.convert("RGB")


def main():
    im = build()
    path = EXPORTS / "MinoxShop-static-shed-stages.jpg"
    im.save(path, quality=95, optimize=True)
    im.save(OUT / "shed-stages.jpg", quality=95)
    # also square crop-friendly version for feed experiments
    sq = Image.new("RGB", (1080, 1080), NAVY_DEEP)
    # rebuild tighter? save portrait only for now
    print("WROTE", path, im.size)


if __name__ == "__main__":
    main()
