#!/usr/bin/env python3
"""MinoxShop TWO BOXES v2b — natural Hebrew + no overlapping layers.

Fixes vs v2:
- Spoken boutique Hebrew (club-native)
- One caption at a time, exclusive time windows
- Pack / evidence card / mosaic never stack on each other
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/tmp/two-boxes-v2b")
ASSETS = ROOT / "assets"
FRAMES = ROOT / "frames"
QA = ROOT / "qa"
EXPORTS = Path("/agent/repos/barbero-shop/exports")
for p in (FRAMES, QA, EXPORTS):
    p.mkdir(parents=True, exist_ok=True)

# reuse prepared assets from v2 if present
_SRC = Path("/tmp/two-boxes-v2/assets")
if _SRC.exists() and not (ASSETS / "pack_trim.png").exists():
    ASSETS.mkdir(parents=True, exist_ok=True)
    import shutil

    for name in (
        "pack_trim.png",
        "main-logo.png",
        "ba-before.jpg",
        "ba-after.jpg",
        "res_before.jpg",
        "res_after.jpg",
    ):
        shutil.copy2(_SRC / name, ASSETS / name)

W, H = 1080, 1920
FPS = 60
DURATION = 15.0
N = int(DURATION * FPS)

NAVY = (14, 28, 52)
NAVY_DEEP = (5, 10, 22)
GOLD = (196, 158, 86)
GOLD_SOFT = (226, 199, 135)
IVORY = (243, 245, 248)
MUTED = (150, 160, 178)

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


PACK = Image.open(ASSETS / "pack_trim.png").convert("RGBA")
LOGO = Image.open(ASSETS / "main-logo.png").convert("RGBA")
BEFORE = Image.open(ASSETS / "ba-before.jpg").convert("RGB")
AFTER = Image.open(ASSETS / "ba-after.jpg").convert("RGB")
RES_B = Image.open(ASSETS / "res_before.jpg").convert("RGB")
RES_A = Image.open(ASSETS / "res_after.jpg").convert("RGB")


def polish(im: Image.Image) -> Image.Image:
    arr = np.asarray(im).astype(np.float32)
    lum = 0.2126 * arr[:, :, 0] + 0.7152 * arr[:, :, 1] + 0.0722 * arr[:, :, 2]
    mx, mn = arr.max(axis=2), arr.min(axis=2)
    sat = (mx - mn) / (mx + 1e-3)
    h, w = lum.shape
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w * 0.5) / (w * 0.4)) ** 2 + ((yy - h * 0.48) / (h * 0.36)) ** 2)
    center = np.clip(1.15 - r, 0, 1)
    glare = np.clip((lum - 85) / 85, 0, 1) * np.clip((0.45 - sat) / 0.38, 0, 1) * (0.55 + 0.45 * center)
    g = Image.fromarray((np.clip(glare, 0, 1) * 255).astype(np.uint8), "L").filter(ImageFilter.GaussianBlur(14))
    glare = np.asarray(g).astype(np.float32) / 255.0
    dark = lum < 70
    hair = np.median(arr[dark], axis=0) if dark.any() else np.array([42.0, 28.0, 22.0])
    arr2 = arr * (1 - glare[:, :, None] * 0.4) + hair * (glare[:, :, None] * 0.4)
    arr2 = arr2 * (1 - 0.06 * center[:, :, None] * np.clip((lum - 40) / 110, 0, 1)[:, :, None])
    out = Image.fromarray(np.clip(arr2, 0, 255).astype(np.uint8), "RGB")
    return ImageEnhance.Contrast(ImageEnhance.Brightness(out).enhance(1.03)).enhance(1.1)


AFTER = polish(AFTER)
RES_A = polish(RES_A)


def navy_field(t: float = 0.0) -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cy, cx = H * 0.38, W * 0.5
    r = np.sqrt(((xx - cx) / (W * 0.62)) ** 2 + ((yy - cy) / (H * 0.48)) ** 2)
    pulse = 0.04 * math.sin(t * 0.9)
    s = np.clip(1.05 - r + pulse, 0, 1) ** 1.25
    deep = np.array(NAVY_DEEP, np.float32)
    base = np.array(NAVY, np.float32)
    goldish = np.array([28.0, 36.0, 52.0], np.float32)
    arr = deep + (base - deep) * s[:, :, None]
    # subtle warm spotlight behind product zone
    r2 = np.sqrt(((xx - cx) / (W * 0.35)) ** 2 + ((yy - H * 0.42) / (H * 0.22)) ** 2)
    glow = np.clip(1.0 - r2, 0, 1) ** 2 * 0.22
    arr = arr + (goldish - arr) * glow[:, :, None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def text_c(im, text, y, size, fill, alpha=255, he=True, bold=True):
    if alpha < 8:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(size, bold, he)
    tw, th, bb = text_bb(d, text, f, "he" if he else None)
    a = int(max(0, min(255, alpha)))
    color = (*fill[:3], a)
    xy = ((W - tw) // 2 - bb[0], y - bb[1])
    if he:
        draw_he(d, xy, text, f, color)
    else:
        d.text(xy, text, font=f, fill=color)
    im.alpha_composite(layer)


def caption(im, text, y, size, fill, u, rise=12):
    if u < 0.04:
        return
    a = int(255 * u)
    yy = y - int(rise * (1 - u))
    text_c(im, text, yy + 2, size, (0, 0, 0), int(a * 0.4))
    text_c(im, text, yy, size, fill, a)


def line_u(t, start, end, fi=0.22, fo=0.28):
    if t < start or t > end:
        return 0.0
    u = 1.0
    if t < start + fi:
        u = ease_out((t - start) / fi)
    if t > end - fo:
        u *= max(0.0, 1.0 - (t - (end - fo)) / fo)
    return u


def apply_logo(im, alpha, y=48, size=104):
    if alpha < 0.05:
        return
    logo = LOGO.copy()
    logo.thumbnail((size, size), Image.Resampling.LANCZOS)
    logo.putalpha(logo.split()[-1].point(lambda a: int(a * alpha)))
    im.alpha_composite(logo, ((W - logo.size[0]) // 2, y))


def gold_frame(im, progress: float):
    """Hairline gold frame drawing in — premium stage cue."""
    p = ease_out(min(1.0, max(0.0, progress)))
    if p < 0.02:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    m = 42
    a = int(180 * p)
    # draw perimeter progressively
    perim = 2 * ((W - 2 * m) + (H - 2 * m))
    drawn = perim * p
    # top
    top = W - 2 * m
    if drawn > 0:
        d.line([(m, m), (m + min(top, drawn), m)], fill=(*GOLD, a), width=2)
        drawn -= top
    # right
    right = H - 2 * m
    if drawn > 0:
        d.line([(W - m, m), (W - m, m + min(right, drawn))], fill=(*GOLD, a), width=2)
        drawn -= right
    # bottom
    if drawn > 0:
        d.line([(W - m, H - m), (W - m - min(top, drawn), H - m)], fill=(*GOLD, a), width=2)
        drawn -= top
    # left
    if drawn > 0:
        d.line([(m, H - m), (m, H - m - min(right, drawn))], fill=(*GOLD, a), width=2)
    im.alpha_composite(layer)


def soft_shadow(im, pack, px, py, a=170, blur=36):
    sh = Image.new("RGBA", pack.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, a), (0, 0), pack.split()[-1])
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    im.alpha_composite(sh, (px - 8, py + 28))


def floor_stage(im, y_line=1088, alpha=0.55):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # elliptical contact shadow
    d.ellipse([180, y_line - 18, W - 180, y_line + 34], fill=(0, 0, 0, int(110 * alpha)))
    d.line([(160, y_line), (W - 160, y_line)], fill=(*GOLD, int(90 * alpha)), width=1)
    im.alpha_composite(layer)


def reflection(pack, op=0.30, height=120):
    flip = pack.transpose(Image.Transpose.FLIP_TOP_BOTTOM).crop((0, 0, pack.size[0], min(height, pack.size[1])))
    arr = np.asarray(flip).astype(np.float32)
    h = arr.shape[0]
    fade = np.linspace(op, 0.0, h, dtype=np.float32)[:, None]
    arr[:, :, 3] *= fade
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def specular_sweep(im, px, py, pw, ph, t_local):
    u = max(0.0, min(1.0, t_local))
    if u < 0.02 or u > 0.98:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x = int(px + pw * u)
    a = int(90 * math.sin(math.pi * u))
    d.polygon(
        [(x - 18, py + 40), (x + 10, py + 40), (x + 28, py + ph - 60), (x, py + ph - 60)],
        fill=(255, 240, 210, a),
    )
    im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(6)))


def place_pack(im, max_w, y_center, pop=1.0, alpha=1.0, specular_t=None):
    """Place FULL twin pack inside safe stage — never clipped."""
    pop = max(0.0, min(1.0, pop))
    if pop < 0.02 or alpha < 0.02:
        return None
    p = PACK.copy()
    p = ImageEnhance.Brightness(p).enhance(1.12)
    p = ImageEnhance.Contrast(p).enhance(1.10)
    p = ImageEnhance.Color(p).enhance(1.05)
    # hard max width so left/right margins >= 60px
    max_w = min(max_w, W - 120)
    p.thumbnail((max_w, int(max_w * 0.9)), Image.Resampling.LANCZOS)
    scale = 0.90 + 0.10 * ease_out_back(pop)
    pw = max(1, int(p.size[0] * scale))
    ph = max(1, int(p.size[1] * scale))
    pp = p.resize((pw, ph), Image.Resampling.LANCZOS)
    aa = pop * alpha
    if aa < 0.99:
        pp.putalpha(pp.split()[-1].point(lambda a: int(a * aa)))
    px = (W - pw) // 2
    py = int(y_center - ph / 2)
    # keep pack above text zone
    py = max(210, min(py, 980 - ph))
    floor_stage(im, y_line=py + ph - 8, alpha=0.5 * aa)
    soft_shadow(im, pp, px, py, a=int(175 * aa))
    ref = reflection(pp, op=0.28 * aa, height=110)
    im.alpha_composite(ref, (px, py + ph - 6))
    im.alpha_composite(pp, (px, py))
    if specular_t is not None:
        specular_sweep(im, px, py, pw, ph, specular_t)
    return px, py, pw, ph


def fit_square(im, size, y_bias=0.38):
    """Cover-fit square — no letterbox bars."""
    w, h = im.size
    scale = max(size / w, size / h) * 1.02
    nw, nh = int(w * scale + 0.5), int(h * scale + 0.5)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - size) // 2
    y = max(0, min(nh - size, int((nh - size) * y_bias)))
    return im.crop((x, y, x + size, y + size))


def evidence_card(progress_wipe: float, alpha: float) -> Image.Image:
    """Gold-stroked card: before → after wipe, Hebrew tabs we draw."""
    cw, ch = 820, 720
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    # panel bg
    d.rounded_rectangle([0, 0, cw - 1, ch - 1], 28, fill=(10, 18, 34, int(235 * alpha)))
    d.rounded_rectangle([2, 2, cw - 3, ch - 3], 26, outline=(*GOLD, int(210 * alpha)), width=3)

    # fill card media area edge-to-edge (no gray side bars)
    media_w, media_h = cw - 24, ch - 24
    before = fit_square(BEFORE, max(media_w, media_h), y_bias=0.34).resize((media_w, media_h), Image.Resampling.LANCZOS)
    after = fit_square(AFTER, max(media_w, media_h), y_bias=0.40).resize((media_w, media_h), Image.Resampling.LANCZOS)
    # wipe
    p = max(0.0, min(1.0, progress_wipe))
    feather = 36
    mask = Image.new("L", (media_w, media_h), 0)
    md = ImageDraw.Draw(mask)
    cut = int(media_w * p)
    md.rectangle([0, 0, max(0, cut - feather), media_h], fill=255)
    for i in range(feather * 2):
        x = cut - feather + i
        if 0 <= x < media_w:
            md.line([(x, 0), (x, media_h)], fill=int(255 * (i / (feather * 2))))
    plate = before.copy()
    plate.paste(after, (0, 0), mask)
    # rounded clip
    clip = Image.new("L", (media_w, media_h), 0)
    ImageDraw.Draw(clip).rounded_rectangle([0, 0, media_w - 1, media_h - 1], 22, fill=255)
    plate_rgba = plate.convert("RGBA")
    plate_rgba.putalpha(clip)
    card.alpha_composite(plate_rgba, (12, 12))

    # tabs
    f = font(26, True)
    tab = "לפני" if p < 0.55 else "אחרי ארבעה חודשים"
    tw, th, bb = text_bb(d, tab, f, "he")
    pad_x, pad_y = 18, 10
    bw, bh = tw + pad_x * 2, th + pad_y * 2
    x0 = 28
    y0 = 28
    fill = (8, 14, 26, int(220 * alpha)) if p < 0.55 else (*GOLD, int(230 * alpha))
    fg = (*IVORY, int(255 * alpha)) if p < 0.55 else (18, 14, 6, int(255 * alpha))
    d.rounded_rectangle([x0, y0, x0 + bw, y0 + bh], 16, fill=fill)
    draw_he(d, (x0 + pad_x - bb[0], y0 + pad_y - bb[1]), tab, f, fg)

    if alpha < 0.99:
        card.putalpha(card.split()[-1].point(lambda a: int(a * alpha)))
    return card


def results_mosaic(alpha: float) -> Image.Image:
    """Three real crown crops — honest multi-result strip, no faces."""
    strip_w, strip_h = 920, 280
    strip = Image.new("RGBA", (strip_w, strip_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(strip)
    d.rounded_rectangle([0, 0, strip_w - 1, strip_h - 1], 22, fill=(8, 16, 30, int(210 * alpha)))
    d.rounded_rectangle([1, 1, strip_w - 2, strip_h - 2], 20, outline=(*GOLD, int(160 * alpha)), width=2)

    # three distinct real plates — before / after / second case after
    tiles = [
        fit_square(BEFORE, 220, y_bias=0.32),
        fit_square(AFTER, 220, y_bias=0.40),
        fit_square(RES_A, 220, y_bias=0.36),
    ]

    gap = 24
    total = 220 * 3 + gap * 2
    x = (strip_w - total) // 2
    for i, tile in enumerate(tiles):
        t = tile.convert("RGBA")
        # gold border
        border = Image.new("RGBA", (228, 228), (0, 0, 0, 0))
        ImageDraw.Draw(border).rounded_rectangle([0, 0, 227, 227], 16, outline=(*GOLD, int(200 * alpha)), width=2)
        strip.alpha_composite(t, (x + 4, 30))
        strip.alpha_composite(border, (x, 26))
        x += 220 + gap

    if alpha < 0.99:
        strip.putalpha(strip.split()[-1].point(lambda a: int(a * alpha)))
    return strip


def seal_row(im, items, y, alpha):
    if alpha < 0.05:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(24, True)
    gap = 18
    # measure
    boxes = []
    for txt in items:
        tw, th, bb = text_bb(d, txt, f, "he")
        bw, bh = tw + 36, th + 22
        boxes.append((txt, bw, bh, bb, tw, th))
    total = sum(b[1] for b in boxes) + gap * (len(boxes) - 1)
    x = (W - total) // 2
    a = int(245 * alpha)
    for txt, bw, bh, bb, tw, th in boxes:
        d.rounded_rectangle([x, y, x + bw, y + bh], bh // 2, fill=(255, 255, 255, int(18 * alpha)))
        d.rounded_rectangle([x, y, x + bw, y + bh], bh // 2, outline=(*GOLD, int(160 * alpha)), width=2)
        # gold dot
        d.ellipse([x + 12, y + bh // 2 - 4, x + 20, y + bh // 2 + 4], fill=(*GOLD, a))
        draw_he(d, (x + 28 - bb[0], y + (bh - th) // 2 - bb[1]), txt, f, (*IVORY, a))
        x += bw + gap
    im.alpha_composite(layer)


CAP_Y = 1460  # single caption band — never stack lines


def frame_at(t: float) -> Image.Image:
    """Exclusive layers: pack XOR card XOR mosaic. One caption at a time."""
    im = navy_field(t)
    gold_frame(im, min(1.0, t / 0.45))
    apply_logo(im, max(0.88, min(1.0, t / 0.2)), y=44, size=108)

    # ---- PHASE A: pack only 0–2.15 ----
    if t < 2.25:
        fade = 1.0
        if t > 2.00:
            fade = max(0.0, 1.0 - (t - 2.00) / 0.25)
        spec = None
        if 0.35 < t < 1.15:
            spec = max(0.0, min(1.0, (t - 0.35) / 0.65))
        place_pack(
            im,
            max_w=900,
            y_center=560,
            pop=ease_out(min(1.0, (t + 0.15) / 0.4)),
            alpha=fade,
            specular_t=spec,
        )

    # ---- PHASE B: evidence card only 2.15–4.85 ----
    if 2.10 < t < 4.95:
        card_a = ease_out(min(1.0, (t - 2.15) / 0.30))
        if t > 4.55:
            card_a *= max(0.0, 1.0 - (t - 4.55) / 0.35)
        wipe = ease_in_out(min(1.0, max(0.0, (t - 2.40) / 1.20)))
        card = evidence_card(wipe, card_a)
        cx = (W - card.size[0]) // 2
        cy = 280 + int((1 - card_a) * 50)
        im.alpha_composite(card, (cx, cy))

    # ---- PHASE C: mosaic only 4.85–6.15 ----
    if 4.80 < t < 6.25:
        ma = line_u(t, 4.85, 6.15, fi=0.22, fo=0.28)
        if ma > 0.05:
            mosa = results_mosaic(ma)
            # centered in mid frame — clear of caption band
            im.alpha_composite(mosa, ((W - mosa.size[0]) // 2, 720))

    # ---- PHASE D: pack returns 6.05–end ----
    if t >= 6.05:
        local = t - 6.05
        pop = ease_out(min(1.0, local / 0.38))
        lift = ease_out(min(1.0, (t - 10.4) / 0.4)) if t >= 10.4 else 0.0
        y_c = int(540 - 130 * lift)
        max_w = int(880 - 30 * lift)
        place_pack(
            im,
            max_w=max_w,
            y_center=y_c,
            pop=pop,
            alpha=1.0,
            specular_t=(local / 0.65) if local < 0.65 else None,
        )

    # ---- ONE caption at a time (exclusive windows, natural Hebrew) ----
    caption(im, "במועדון כבר מכירים את המארז", CAP_Y, 40, IVORY, line_u(t, 0.10, 2.10))
    caption(im, "הקרקפת מכוסה יותר", CAP_Y, 42, GOLD_SOFT, line_u(t, 3.40, 4.70))
    caption(im, "ככה נראות התוצאות במועדון", CAP_Y, 36, IVORY, line_u(t, 4.90, 6.10))
    caption(im, "שתי קופסאות לשנה שלמה", CAP_Y, 44, IVORY, line_u(t, 6.20, 8.00))
    caption(im, "במועדון חוזרים על אותו מארז", CAP_Y, 38, GOLD_SOFT, line_u(t, 8.05, 9.85))
    caption(im, "בחודשיים הראשונים עוד לא רואים", CAP_Y, 34, MUTED, line_u(t, 9.90, 11.05))

    # ---- Price block (own band, above seals) ----
    if t >= 11.10:
        pu = ease_out(min(1.0, (t - 11.10) / 0.30))
        caption(im, "כל השנה במחיר אחד", 1260, 28, MUTED, line_u(t, 11.15, 13.35) * pu)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        f = font(88, True, he=False)
        price = "₪765"
        tw, th, bb = text_bb(d, price, f)
        a = int(255 * pu)
        d.text(((W - tw) // 2 - bb[0] + 3, 1310 - bb[1] + 3), price, font=f, fill=(0, 0, 0, int(a * 0.45)))
        d.text(((W - tw) // 2 - bb[0], 1310 - bb[1]), price, font=f, fill=(*GOLD_SOFT, a))
        if t >= 11.70:
            hu = ease_out(min(1.0, (t - 11.70) / 0.25))
            rw = int(180 * hu)
            d.rounded_rectangle(
                [(W - rw) // 2, 1310 + th + 12, (W + rw) // 2, 1310 + th + 16],
                2,
                fill=(*GOLD, int(230 * hu)),
            )
        im.alpha_composite(layer)

    # ---- Seals last — below price, no caption collision ----
    if t >= 13.20:
        su = ease_out(min(1.0, (t - 13.20) / 0.28))
        seal_row(im, ["מקורי מארה״ב", "משלוח חינם הביתה", "חמישה אחוזים לגברים"], 1520, su)
        caption(im, "מארז כפול של קירקלנד", 1640, 28, MUTED, line_u(t, 13.40, 15.0, fo=0.12) * su)

    if t >= 2.30:
        da = ease_out(min(1.0, (t - 2.30) / 0.30))
        text_c(im, "תוצאות משתנות בין אנשים", 1820, 18, (105, 115, 132), int(155 * da))

    return im


def make_cover() -> Image.Image:
    im = navy_field(0.5)
    gold_frame(im, 1.0)
    apply_logo(im, 0.95, y=48, size=110)
    place_pack(im, max_w=900, y_center=520, pop=1.0, alpha=1.0, specular_t=0.45)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(82, True, he=False)
    price = "₪765"
    tw, th, bb = text_bb(d, price, f)
    d.text(((W - tw) // 2 - bb[0] + 2, 1120 - bb[1] + 2), price, font=f, fill=(0, 0, 0, 120))
    d.text(((W - tw) // 2 - bb[0], 1120 - bb[1]), price, font=f, fill=(*GOLD_SOFT, 255))
    im.alpha_composite(layer)
    caption(im, "שתי קופסאות לשנה שלמה", 1240, 40, IVORY, 1.0)
    caption(im, "מקורי מארה״ב ומשלוח חינם", 1320, 28, MUTED, 1.0)
    return im.convert("RGB")


def main():
    print(f"two-boxes v2b hebrew {N}f @{FPS}")
    for i in range(N):
        t = i / FPS
        fr = frame_at(t).convert("RGB")
        fr.save(FRAMES / f"f_{i:04d}.jpg", quality=93, optimize=True)
        if i % 60 == 0:
            print(f"frame {i} {t:.1f}s")
        if i in (0, 60, 150, 240, 300, 360, 420, 540, 660, 780, 840):
            fr.save(QA / f"qa_{i:04d}.jpg", quality=92)
    cover = make_cover()
    cover.save(EXPORTS / "MinoxShop-two-boxes_v2b-COVER.jpg", quality=94, optimize=True)
    cover.save(QA / "cover.jpg", quality=94)
    print("DONE")


if __name__ == "__main__":
    main()
