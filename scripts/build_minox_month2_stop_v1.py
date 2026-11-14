#!/usr/bin/env python3
"""MinoxShop elevated reel v1 — 'רוב הגברים עוצרים בחודש השני'
Level above scrubber: two stills + black cut, no HUD, sparse copy, navy pack outro.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/tmp/month2-stop")
ASSETS = ROOT / "assets"
FRAMES = ROOT / "frames"
QA = ROOT / "qa"
EXPORTS = Path("/agent/repos/barbero-shop/exports")
FRAMES.mkdir(exist_ok=True)
QA.mkdir(exist_ok=True)
EXPORTS.mkdir(exist_ok=True)

W, H = 1080, 1920
FPS = 60
DURATION = 14.0
N = int(DURATION * FPS)

NAVY = (14, 28, 52)
NAVY_DEEP = (8, 16, 32)
GOLD = (196, 158, 86)
GOLD_SOFT = (226, 199, 135)
IVORY = (243, 245, 248)
INK_SOFT = (180, 188, 200)

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


def text_bb(draw, text, fnt, language=None):
    kw = {"language": language} if language else {}
    bb = draw.textbbox((0, 0), text, font=fnt, **kw)
    return bb[2] - bb[0], bb[3] - bb[1], bb


def draw_he(d, xy, text, fnt, fill):
    d.text(xy, text, font=fnt, fill=fill, language="he")


def polish_after(im: Image.Image) -> Image.Image:
    arr = np.asarray(im.convert("RGB")).astype(np.float32)
    lum = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    mx = arr.max(axis=2)
    mn = arr.min(axis=2)
    sat = (mx - mn) / (mx + 1e-3)
    h, w = lum.shape
    yy, xx = np.mgrid[0:h, 0:w]
    cy, cx = h * 0.48, w * 0.50
    r = np.sqrt(((xx - cx) / (w * 0.38)) ** 2 + ((yy - cy) / (h * 0.34)) ** 2)
    center = np.clip(1.15 - r, 0, 1)
    glare = np.clip((lum - 85) / 85, 0, 1) * np.clip((0.45 - sat) / 0.38, 0, 1)
    glare = glare * (0.6 + 0.4 * center)
    g_im = Image.fromarray((np.clip(glare, 0, 1) * 255).astype(np.uint8), "L").filter(
        ImageFilter.GaussianBlur(16)
    )
    glare = np.asarray(g_im).astype(np.float32) / 255.0
    dark = lum < 70
    hair_target = np.median(arr[dark], axis=0) if dark.any() else np.array([42, 28, 22], np.float32)
    strength = 0.42
    arr2 = arr * (1 - glare[:, :, None] * strength) + hair_target * (glare[:, :, None] * strength)
    arr2 = arr2 * (1 - 0.07 * center[:, :, None] * np.clip((lum - 40) / 110, 0, 1)[:, :, None])
    return Image.fromarray(np.clip(arr2, 0, 255).astype(np.uint8), "RGB")


def fit_cover(im, tw, th, zoom=1.0, y_bias=0.40):
    w, h = im.size
    scale = max(tw / w, th / h) * zoom
    nw, nh = int(w * scale + 0.5), int(h * scale + 0.5)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - tw) // 2
    y = max(0, min(nh - th, int((nh - th) * y_bias)))
    return im.crop((x, y, x + tw, y + th))


def blend_progress(before: Image.Image, after: Image.Image, p: float) -> Image.Image:
    """Photoreal blend for intermediate month — feathered wipe, no HUD."""
    p = max(0.0, min(1.0, p))
    b = np.asarray(before.convert("RGB")).astype(np.float32)
    a = np.asarray(after.convert("RGB")).astype(np.float32)
    h, w = b.shape[:2]
    # Soft left→right growth reveal (after on the right like scrubber)
    xx = np.linspace(0, 1, w, dtype=np.float32)[None, :].repeat(h, axis=0)
    edge = 0.10
    alpha = np.clip((xx - (1.0 - p) + edge) / (2 * edge + 1e-6), 0, 1)
    # Also lift overall density slightly with p so month-2 isn't pure before
    global_mix = 0.18 * p
    alpha = np.clip(alpha * 0.85 + global_mix, 0, 1)
    out = b * (1 - alpha[:, :, None]) + a * alpha[:, :, None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


BEFORE_RAW = ImageEnhance.Contrast(Image.open(ASSETS / "ba-before.jpg").convert("RGB")).enhance(1.1)
_after = polish_after(Image.open(ASSETS / "ba-after.jpg").convert("RGB"))
_after = polish_after(_after)  # second pass — denser midtones for month-6 still
_after = ImageEnhance.Contrast(_after).enhance(1.16)
_after = ImageEnhance.Color(_after).enhance(1.05)
# keep luminance up so "denser" doesn't read as just darker lighting
AFTER_RAW = ImageEnhance.Brightness(_after).enhance(1.04)
PACK = Image.open(ASSETS / "kirkland-double-composed.png").convert("RGBA")
LOGO = Image.open(ASSETS / "main-logo.png").convert("RGBA")

# Precompose full-bleed plates
# Month 2: mostly early — still looks like "nothing to see yet"
PLATE_M2 = fit_cover(
    blend_progress(BEFORE_RAW, AFTER_RAW, 0.22),
    W,
    H,
    zoom=1.10,
    y_bias=0.36,
)
PLATE_M6 = fit_cover(AFTER_RAW, W, H, zoom=1.04, y_bias=0.42)


def navy_field(spotlight: float = 0.85) -> Image.Image:
    im = Image.new("RGB", (W, H), NAVY_DEEP)
    arr = np.asarray(im).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    cy, cx = H * 0.42, W * 0.5
    r = np.sqrt(((xx - cx) / (W * 0.55)) ** 2 + ((yy - cy) / (H * 0.42)) ** 2)
    spot = np.clip(1.0 - r, 0, 1) ** 1.4 * spotlight
    base = np.array(NAVY, dtype=np.float32)
    deep = np.array(NAVY_DEEP, dtype=np.float32)
    arr = deep + (base - deep) * spot[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def soft_vignette(im: Image.Image, strength: float = 0.35) -> Image.Image:
    arr = np.asarray(im.convert("RGB")).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    cy, cx = H * 0.45, W * 0.5
    r = np.sqrt(((xx - cx) / (W * 0.72)) ** 2 + ((yy - cy) / (H * 0.62)) ** 2)
    vig = np.clip(1.0 - strength * np.clip(r - 0.55, 0, 1) ** 1.2, 0.55, 1.0)
    return Image.fromarray(np.clip(arr * vig[:, :, None], 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def text_c(im, text, y, size, fill, alpha=255, bold=True, he=True):
    if alpha < 8:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(size, bold, he)
    tw, th, bb = text_bb(d, text, f, "he" if he else None)
    a = max(0, min(255, int(alpha)))
    color = (*fill[:3], a) if len(fill) == 3 else (*fill[:3], int(fill[3] * a / 255))
    if he:
        draw_he(d, ((W - tw) // 2 - bb[0], y - bb[1]), text, f, color)
    else:
        d.text(((W - tw) // 2 - bb[0], y - bb[1]), text, font=f, fill=color)
    im.alpha_composite(layer)


def draw_lower_line(im, text, y, size, fill, alpha, shadow=True):
    """Single replacing caption — no pill, soft shadow for legibility."""
    if alpha < 0.05:
        return
    a = int(255 * alpha)
    if shadow:
        text_c(im, text, y + 2, size, (0, 0, 0), int(a * 0.55))
    text_c(im, text, y, size, fill, a)


def apply_logo(im, alpha, y=36, size=88):
    if alpha < 0.05:
        return
    logo = LOGO.copy()
    logo.thumbnail((size, size), Image.Resampling.LANCZOS)
    logo.putalpha(logo.split()[-1].point(lambda a: int(a * alpha)))
    im.alpha_composite(logo, ((W - logo.size[0]) // 2, y))


def soft_shadow(im, pack, px, py, a=120):
    sh = Image.new("RGBA", pack.size, (0, 0, 0, 0))
    mask = pack.split()[-1]
    sh.paste((0, 0, 0, a), (0, 0), mask)
    sh = sh.filter(ImageFilter.GaussianBlur(28))
    im.alpha_composite(sh, (px, py + 18))


def plate_with_grade(plate: Image.Image, darken: float = 0.0, vig: float = 0.32) -> Image.Image:
    im = soft_vignette(plate, vig)
    if darken > 0.01:
        arr = np.asarray(im.convert("RGB")).astype(np.float32) * (1.0 - darken)
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    return im


def frame_at(t: float) -> Image.Image:
    # Beat sheet (14s):
    # 0.00–1.90  M2 + hook
    # 1.90–4.10  M2 + reason
    # 4.10–4.30  black
    # 4.30–6.70  M6 + stay line
    # 6.70–8.90  M6 + verdict
    # 8.90–12.40 pack CTA
    # 12.40–14.00 club whisper

    if 4.10 <= t < 4.30:
        return Image.new("RGBA", (W, H), (0, 0, 0, 255))

    if t < 4.10:
        im = plate_with_grade(PLATE_M2, darken=0.06)
        # subtle bottom gradient so type reads
        grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(grad)
        for i in range(420):
            a = int(150 * (i / 420) ** 1.3)
            gd.line([(0, H - 420 + i), (W, H - 420 + i)], fill=(0, 0, 0, a))
        im.alpha_composite(grad)

        # month tick — hairline edge label only after hook settles
        if t >= 1.90:
            tick_a = ease_out(min(1.0, (t - 1.90) / 0.25))
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            f_he = font(22, True)
            f_num = font(22, True, he=False)
            he, num = "חודש", "2"
            tw_h, th_h, bb_h = text_bb(d, he, f_he, "he")
            tw_n, th_n, bb_n = text_bb(d, num, f_num)
            gap = 8
            x0, y0 = 48, 160
            # RTL visual: number left of Hebrew word
            a = int(220 * tick_a)
            nx = x0 - bb_n[0]
            hx = nx + tw_n + gap - bb_h[0]
            d.text((nx, y0 - bb_n[1] + (th_h - th_n) // 2), num, font=f_num, fill=(*GOLD_SOFT, a))
            draw_he(d, (hx, y0 - bb_h[1]), he, f_he, (*GOLD_SOFT, a))
            d.line(
                [(x0, y0 + th_h + 8), (x0 + tw_n + gap + tw_h, y0 + th_h + 8)],
                fill=(*GOLD, int(200 * tick_a)),
                width=2,
            )
            im.alpha_composite(layer)

        # captions replace each other — hook readable from first frames
        # no Latin '.' — Noto Hebrew tofus period
        if t < 1.90:
            u = max(0.82, ease_out(min(1.0, t / 0.28)))
            fade = 1.0
            if t > 1.55:
                fade = max(0.0, 1.0 - (t - 1.55) / 0.35)
            draw_lower_line(
                im,
                "רוב הגברים עוצרים בחודש השני",
                1520,
                44,
                IVORY,
                u * fade,
            )
        else:
            u = ease_out(min(1.0, (t - 1.90) / 0.28))
            fade = 1.0
            if t > 3.75:
                fade = max(0.0, 1.0 - (t - 3.75) / 0.35)
            draw_lower_line(
                im,
                "כי שם עוד אין מה לראות",
                1520,
                40,
                GOLD_SOFT,
                u * fade,
            )
        return im

    if t < 8.90:
        # Month 6 hold
        enter = ease_out(min(1.0, (t - 4.30) / 0.22))
        # lighter vignette — density must read as hair, not underexposure
        im = plate_with_grade(PLATE_M6, darken=0.0, vig=0.16)
        if enter < 0.99:
            # slight punch from black
            punch = 1.0 + 0.04 * (1 - enter)
            nw, nh = int(W * punch), int(H * punch)
            im = im.resize((nw, nh), Image.Resampling.LANCZOS)
            im = im.crop(((nw - W) // 2, (nh - H) // 2, (nw - W) // 2 + W, (nh - H) // 2 + H))

        grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(grad)
        for i in range(420):
            a = int(140 * (i / 420) ** 1.3)
            gd.line([(0, H - 420 + i), (W, H - 420 + i)], fill=(0, 0, 0, a))
        im.alpha_composite(grad)

        if t < 6.70:
            u = ease_out(min(1.0, (t - 4.30) / 0.30))
            fade = 1.0
            if t > 6.35:
                fade = max(0.0, 1.0 - (t - 6.35) / 0.35)
            draw_lower_line(
                im,
                "מי שנשאר רואה את ההבדל",
                1520,
                42,
                IVORY,
                u * fade,
            )
        else:
            u = ease_out(min(1.0, (t - 6.70) / 0.28))
            fade = 1.0
            if t > 8.45:
                fade = max(0.0, 1.0 - (t - 8.45) / 0.45)
            draw_lower_line(
                im,
                "הרצף עושה את העבודה",
                1520,
                44,
                GOLD_SOFT,
                u * fade,
            )

        # fall toward navy near end
        if t > 8.40:
            fall = (t - 8.40) / 0.50
            navy = navy_field(0.9)
            navy.putalpha(int(255 * min(1.0, fall)))
            base = Image.new("RGBA", (W, H), (0, 0, 0, 255))
            base.alpha_composite(im)
            base.alpha_composite(navy)
            return base
        return im

    # ---- NAVY PACK OUTRO ----
    t_out = t - 8.90
    im = navy_field(0.95)
    pack_a = ease_out(min(1.0, t_out / 0.35))
    pack = PACK.copy()
    pack = ImageEnhance.Brightness(pack).enhance(1.08)
    pack = ImageEnhance.Contrast(pack).enhance(1.06)
    pack.thumbnail((720, 580), Image.Resampling.LANCZOS)
    scale = 0.90 + 0.10 * pack_a
    pw = max(1, int(pack.size[0] * scale))
    ph = max(1, int(pack.size[1] * scale))
    pp = pack.resize((pw, ph), Image.Resampling.LANCZOS)
    if pack_a < 1:
        pp.putalpha(pp.split()[-1].point(lambda a: int(a * pack_a)))
    px = (W - pw) // 2
    py = 420 + int((1 - pack_a) * 70)
    soft_shadow(im, pp, px, py, a=int(150 * pack_a))
    im.alpha_composite(pp, (px, py))

    line_a = ease_out(min(1.0, max(0.0, (t_out - 0.25) / 0.35)))
    if line_a > 0.05:
        text_c(im, "מארז כפול קירקלנד", 1080, 42, IVORY, int(255 * line_a))
        # gold rule
        d = ImageDraw.Draw(im)
        rw = int(120 * line_a)
        d.rounded_rectangle(
            [(W - rw) // 2, 1140, (W + rw) // 2, 1144],
            2,
            fill=(*GOLD, int(230 * line_a)),
        )
        # price dual font
        f_p = font(48, True, he=False)
        price = "₪765"
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dd = ImageDraw.Draw(layer)
        pw2, ph2, pbb = text_bb(dd, price, f_p)
        dd.text(
            ((W - pw2) // 2 - pbb[0], 1170 - pbb[1]),
            price,
            font=f_p,
            fill=(*GOLD_SOFT, int(255 * line_a)),
        )
        im.alpha_composite(layer)
        text_c(im, "משלוח חינם עד הבית", 1260, 30, INK_SOFT, int(230 * line_a))
        text_c(im, "לשנה של טיפול", 1310, 24, (120, 130, 150), int(200 * line_a))

    # Club whisper sits under CTA copy; disclaimer stays fixed at bottom (no swap flash)
    club_a = ease_out(min(1.0, max(0.0, (t_out - 3.40) / 0.35)))
    if club_a > 0.05:
        text_c(im, "גם במועדון הנקודות", 1380, 22, (130, 140, 160), int(180 * club_a))

    disc_a = ease_out(min(1.0, max(0.0, (t_out - 0.55) / 0.3)))
    if disc_a > 0.05:
        text_c(im, "תוצאות משתנות בין אנשים", 1788, 18, (100, 110, 128), int(160 * disc_a))

    apply_logo(im, 0.9 * min(1.0, t_out / 0.35), y=40, size=92)
    return im


def make_cover() -> Image.Image:
    """Grid/TikTok cover — month-2 plate, two-line hook, no price."""
    im = plate_with_grade(PLATE_M2, darken=0.10)
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for i in range(520):
        a = int(170 * (i / 520) ** 1.15)
        gd.line([(0, H - 520 + i), (W, H - 520 + i)], fill=(0, 0, 0, a))
    im.alpha_composite(grad)
    # Safe zone center for IG/TikTok grid
    draw_lower_line(im, "רובם עוצרים", 1180, 56, IVORY, 1.0)
    draw_lower_line(im, "בחודש השני", 1270, 56, GOLD_SOFT, 1.0)
    apply_logo(im, 0.92, y=48, size=96)
    return im.convert("RGB")


def main():
    print(f"month2-stop v1 {N}f @{FPS} ({DURATION}s)")
    for i in range(N):
        t = i / FPS
        fr = frame_at(t).convert("RGB")
        fr.save(FRAMES / f"f_{i:04d}.jpg", quality=93, optimize=True)
        if i % 60 == 0:
            print(f"frame {i} {t:.1f}s")
        if i in (0, 60, 120, 250, 270, 320, 420, 540, 600, 720, 800):
            fr.save(QA / f"qa_{i:04d}.jpg", quality=92)
    cover = make_cover()
    cover_path = EXPORTS / "MinoxShop-month2-stop_v1-COVER.jpg"
    cover.save(cover_path, quality=94, optimize=True)
    cover.save(QA / "cover.jpg", quality=94)
    print(f"COVER {cover_path}")
    print("DONE")


if __name__ == "__main__":
    main()
