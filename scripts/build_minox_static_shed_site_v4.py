#!/usr/bin/env python3
"""MinoxShop static post v4 — site-matched, not growth-stages clone.

Matches barbero-shop tokens (ink/ivory/gold/Heebo-like + serif display).
Layout is NOT a vertical timeline of colored stage cards (that echoed
Rogaine «what to expect»). Instead: panic hero plate + 3-up strip + closer.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/tmp/static-shed-v4")
ASSETS = ROOT / "assets"
OUT = ROOT / "out"
EXPORTS = Path("/agent/repos/barbero-shop/exports")
for p in (OUT, EXPORTS, ASSETS):
    p.mkdir(parents=True, exist_ok=True)

for _SRC in (Path("/tmp/static-shed-v3/assets"), Path("/tmp/static-shed-v2/assets"), Path("/tmp/static-shed/assets")):
    if _SRC.exists():
        for name in ("ba-before.jpg", "ba-after.jpg", "plate_a.jpg", "plate_c.jpg", "main-logo.png"):
            if (_SRC / name).exists() and not (ASSETS / name).exists():
                shutil.copy2(_SRC / name, ASSETS / name)
        break

_strip = Path("/agent/repos/barbero-shop/minoxshop-growth-hero/assets/results-4-months.png")
if _strip.exists():
    r = Image.open(_strip).convert("RGB")
    w, h = r.size
    top, bot = 40, 720
    if not (ASSETS / "plate_a.jpg").exists():
        r.crop((30, top, w // 2 - 20, bot)).save(ASSETS / "plate_a.jpg", quality=93)
    if not (ASSETS / "plate_c.jpg").exists():
        r.crop((w // 2 + 20, top, w - 30, bot)).save(ASSETS / "plate_c.jpg", quality=93)

W, H = 1080, 1350

# Site tokens from src/index.css
INK = (9, 9, 9)
IVORY = (244, 241, 234)
GOLD = (198, 161, 91)
GOLD_SOFT = (228, 210, 162)
MUTED = (163, 158, 147)
CHARCOAL = (20, 20, 22)
LINE = (198, 161, 91, 72)  # ~0.28 alpha gold

FONT_SANS_B = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Bold.ttf"
FONT_SANS_R = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf"
FONT_SERIF_B = "/usr/share/fonts/truetype/noto/NotoSerifHebrew-Bold.ttf"
FONT_SERIF_R = "/usr/share/fonts/truetype/noto/NotoSerifHebrew-Regular.ttf"


def font(size: int, bold: bool = True, serif: bool = False):
    if serif:
        return ImageFont.truetype(FONT_SERIF_B if bold else FONT_SERIF_R, size)
    return ImageFont.truetype(FONT_SANS_B if bold else FONT_SANS_R, size)


def text_bb(draw, text, fnt):
    bb = draw.textbbox((0, 0), text, font=fnt, language="he")
    return bb[2] - bb[0], bb[3] - bb[1], bb


def draw_he(d, xy, text, fnt, fill):
    d.text(xy, text, font=fnt, fill=fill, language="he")


def center_he(im, text, y, size, fill, bold=True, serif=False):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(size, bold, serif)
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


def kill_bottom(im: Image.Image, frac: float = 0.16) -> Image.Image:
    w, h = im.size
    return im.crop((0, 0, w, int(h * (1 - frac))))


def fit_square(im: Image.Image, size: int, y_bias: float = 0.4) -> Image.Image:
    w, h = im.size
    scale = max(size / w, size / h) * 1.05
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
    r = np.sqrt(((xx - w * 0.5) / (w * 0.5)) ** 2 + ((yy - h * 0.46) / (h * 0.44)) ** 2)
    mask = np.clip((p * 1.3 - r) / 0.3, 0, 1)
    out = a * (1 - mask[:, :, None]) + b * mask[:, :, None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def knock_logo(logo: Image.Image) -> Image.Image:
    arr = np.asarray(logo.convert("RGBA")).copy()
    rgb = arr[:, :, :3].astype(np.float32)
    mn, mx = rgb.min(axis=2), rgb.max(axis=2)
    bg = (mn > 195) & ((mx - mn) < 35) & (rgb.mean(axis=2) > 215)
    arr[:, :, 3] = np.where(bg, 0, 255).astype(np.uint8)
    out = Image.fromarray(arr, "RGBA")
    out.putalpha(out.split()[-1].filter(ImageFilter.GaussianBlur(0.7)))
    return out


def site_bg() -> Image.Image:
    """Match body background: ink + soft gold radial top-right."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # radial at 100% -10% like CSS
    cx, cy = W * 1.0, H * -0.08
    r = np.sqrt(((xx - cx) / 900) ** 2 + ((yy - cy) / 420) ** 2)
    glow = np.clip(1.0 - r, 0, 1) ** 2 * 0.08
    base = np.array(INK, np.float32)
    gold = np.array(GOLD, np.float32)
    arr = base + (gold - base) * glow[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


PLATE_A = kill_bottom(Image.open(ASSETS / "plate_a.jpg").convert("RGB"), 0.16)
PLATE_C = kill_bottom(Image.open(ASSETS / "plate_c.jpg").convert("RGB"), 0.16)
BEFORE = trim_white(Image.open(ASSETS / "ba-before.jpg").convert("RGB"))
AFTER = trim_white(Image.open(ASSETS / "ba-after.jpg").convert("RGB"))
LOGO = knock_logo(Image.open(ASSETS / "main-logo.png"))

SZ = 640
BASE_A = fit_square(PLATE_A, SZ, 0.44)
BASE_C = fit_square(PLATE_C, SZ, 0.44)
EARLY = ImageEnhance.Brightness(BASE_A).enhance(1.02)
MID = soft_blend(BASE_A, BASE_C, 0.65)
LATE = ImageEnhance.Contrast(BASE_C).enhance(1.05)

# Hero panic crop — wide, not a stage card
HERO = fit_square(BEFORE, 900, 0.42)
HERO = ImageEnhance.Contrast(HERO).enhance(1.06)


def rounded_photo(im: Image.Image, size: tuple[int, int], radius: int = 18) -> Image.Image:
    photo = im.resize(size, Image.Resampling.LANCZOS).convert("RGBA")
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius, fill=255)
    photo.putalpha(mask)
    return photo


def gold_rule(im, y, pad=72, alpha=120):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.line([(pad, y), (W - pad, y)], fill=(*GOLD, alpha), width=1)
    im.alpha_composite(layer)


def build() -> Image.Image:
    im = site_bg()

    # logo
    logo = LOGO.copy()
    logo.thumbnail((78, 78), Image.Resampling.LANCZOS)
    im.alpha_composite(logo, ((W - logo.size[0]) // 2, 36))

    # eyebrow — site tracking style (sans, gold)
    center_he(im, "רגע לפני שאתה מפסיק", 128, 22, GOLD, True, serif=False)

    # display serif headline — site Frank-like
    center_he(im, "למה בהתחלה זה נראה", 170, 44, IVORY, True, serif=True)
    center_he(im, "יותר גרוע", 230, 48, GOLD_SOFT, True, serif=True)

    # HERO full-bleed-ish plate (not a timeline card)
    hero = rounded_photo(HERO, (980, 420), radius=22)
    # darken bottom of hero for caption sit
    ha = np.asarray(hero).astype(np.float32)
    fade = np.linspace(0, 0.55, ha.shape[0])[:, None, None]
    ha[:, :, :3] *= 1 - fade * 0.65
    hero = Image.fromarray(np.clip(ha, 0, 255).astype(np.uint8), "RGBA")
    im.alpha_composite(hero, ((W - 980) // 2, 300))

    # caption on hero
    center_he(im, "הנשירה הראשונה מפחידה  אל תעצור שם", 670, 24, IVORY, True, serif=False)
    # note: visual period avoided (tofu); spacing acts as beat

    gold_rule(im, 720, pad=80, alpha=90)

    # section label
    center_he(im, "מה באמת קורה על הקרקפת", 745, 20, MUTED, False, serif=False)

    # THREE-UP strip — RTL order for Hebrew: first weeks on the RIGHT
    thumbs = [
        (LATE, "ארבעה עד שישה חודשים", "כבר רואים שינוי"),
        (MID, "חודשיים עד ארבעה חודשים", "צומח שיער עדין"),
        (EARLY, "שבועות ראשונים", "השיער הישן נושר"),
    ]
    tw, th = 290, 290
    gap = 28
    total = tw * 3 + gap * 2
    x0 = (W - total) // 2
    y0 = 790
    for i, (photo, label, sub) in enumerate(thumbs):
        x = x0 + i * (tw + gap)
        pic = rounded_photo(photo, (tw, th), radius=16)
        # thin gold hairline frame like site line color
        frame = Image.new("RGBA", (tw + 4, th + 4), (0, 0, 0, 0))
        ImageDraw.Draw(frame).rounded_rectangle([0, 0, tw + 3, th + 3], 17, outline=(*GOLD, 100), width=1)
        im.alpha_composite(frame, (x - 2, y0 - 2))
        im.alpha_composite(pic, (x, y0))

        # labels under — sans, site muted/gold
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        f1 = font(18, True, False)
        f2 = font(16, False, False)
        t1, h1, b1 = text_bb(d, label, f1)
        t2, h2, b2 = text_bb(d, sub, f2)
        cx = x + tw // 2
        draw_he(d, (cx - t1 // 2 - b1[0], y0 + th + 16 - b1[1]), label, f1, (*GOLD_SOFT, 255))
        draw_he(d, (cx - t2 // 2 - b2[0], y0 + th + 44 - b2[1]), sub, f2, (*MUTED, 255))
        im.alpha_composite(layer)

    gold_rule(im, 1188, pad=80, alpha=90)

    center_he(im, "ממשיכים כי עצירה מחזירה אחורה", 1215, 26, GOLD_SOFT, True, serif=False)
    center_he(im, "תוצאות משתנות מאדם לאדם", 1265, 20, MUTED, False, serif=False)
    return im.convert("RGB")


def main():
    im = build()
    path = EXPORTS / "MinoxShop-static-shed-site-v4.jpg"
    im.save(path, quality=95, optimize=True)
    im.save(OUT / "shed-site-v4.jpg", quality=95)
    im.save(EXPORTS / "MinoxShop-static-shed-stages.jpg", quality=95, optimize=True)
    print("WROTE", path, im.size)


if __name__ == "__main__":
    main()
