#!/usr/bin/env python3
"""MinoxShop TWO BOXES reel — pack-hero commercial, zero scalp.
Completely different from scrubber / failed month2-stop.
14s navy: gold drop → one carton → twin locks → year → ₪765 → free ship.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/tmp/two-boxes")
ASSETS = ROOT / "assets"
FRAMES = ROOT / "frames"
QA = ROOT / "qa"
EXPORTS = Path("/agent/repos/barbero-shop/exports")
for p in (FRAMES, QA, EXPORTS):
    p.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1920
FPS = 60
DURATION = 14.0
N = int(DURATION * FPS)

NAVY = (14, 28, 52)
NAVY_DEEP = (6, 12, 26)
GOLD = (196, 158, 86)
GOLD_SOFT = (226, 199, 135)
IVORY = (243, 245, 248)
MUTED = (140, 150, 168)

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


PACK_FULL = Image.open(ASSETS / "kirkland-double-composed.png").convert("RGBA")
LOGO = Image.open(ASSETS / "main-logo.png").convert("RGBA")
# Front carton — aggressive right crop so beat-2 is clearly ONE box
_bw, _bh = PACK_FULL.size
PACK_ONE = PACK_FULL.crop((int(_bw * 0.46), int(_bh * 0.02), _bw - 4, _bh)).convert("RGBA")


def navy_field(spot: float = 0.9) -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cy, cx = H * 0.40, W * 0.5
    r = np.sqrt(((xx - cx) / (W * 0.58)) ** 2 + ((yy - cy) / (H * 0.45)) ** 2)
    s = np.clip(1.0 - r, 0, 1) ** 1.35 * spot
    deep = np.array(NAVY_DEEP, np.float32)
    base = np.array(NAVY, np.float32)
    arr = deep + (base - deep) * s[:, :, None]
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
    if he:
        draw_he(d, ((W - tw) // 2 - bb[0], y - bb[1]), text, f, color)
    else:
        d.text(((W - tw) // 2 - bb[0], y - bb[1]), text, font=f, fill=color)
    im.alpha_composite(layer)


def caption(im, text, y, size, fill, u, shadow=True):
    if u < 0.05:
        return
    a = int(255 * u)
    if shadow:
        text_c(im, text, y + 2, size, (0, 0, 0), int(a * 0.45))
    text_c(im, text, y, size, fill, a)


def apply_logo(im, alpha, y=40, size=96):
    if alpha < 0.05:
        return
    logo = LOGO.copy()
    logo.thumbnail((size, size), Image.Resampling.LANCZOS)
    logo.putalpha(logo.split()[-1].point(lambda a: int(a * alpha)))
    im.alpha_composite(logo, ((W - logo.size[0]) // 2, y))


def soft_shadow(im, pack, px, py, a=150, blur=30):
    sh = Image.new("RGBA", pack.size, (0, 0, 0, 0))
    mask = pack.split()[-1]
    sh.paste((0, 0, 0, a), (0, 0), mask)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    im.alpha_composite(sh, (px, py + 22))


def floor_reflection(pack: Image.Image, op: float = 0.28) -> Image.Image:
    flip = pack.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    arr = np.asarray(flip).astype(np.float32)
    h = arr.shape[0]
    fade = np.linspace(op, 0, h, dtype=np.float32)[:, None]
    arr[:, :, 3] *= fade
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def gold_drop(im: Image.Image, t_local: float):
    """Drawn gold drop + single ripple — topical solution cue, not a scalp."""
    u = ease_out(min(1.0, max(0.0, t_local / 0.55)))
    if u < 0.02:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # fall path: start high → settle ~1/3 down
    y_start, y_end = 280, 640
    y = int(y_start + (y_end - y_start) * u)
    x = W // 2
    # drop body
    a = int(240 * min(1.0, u / 0.7))
    rw, rh = 34, 48
    # teardrop approx: ellipse + triangle tip
    d.ellipse([x - rw, y - rh, x + rw, y + rh // 2], fill=(*GOLD, a))
    d.polygon(
        [(x, y - rh - 28), (x - rw + 4, y - rh // 3), (x + rw - 4, y - rh // 3)],
        fill=(*GOLD_SOFT, a),
    )
    # highlight
    d.ellipse([x - 10, y - rh + 6, x + 2, y - rh // 2], fill=(255, 240, 200, int(a * 0.55)))
    # ripple after settle
    if t_local > 0.55:
        r_u = ease_out(min(1.0, (t_local - 0.55) / 0.7))
        fade = max(0.0, 1.0 - (t_local - 1.1) / 0.7) if t_local > 1.1 else 1.0
        rad = int(40 + 120 * r_u)
        ra = int(160 * (1 - r_u) * fade)
        if ra > 8:
            d.ellipse([x - rad, y + 10 - rad // 3, x + rad, y + 10 + rad // 3], outline=(*GOLD, ra), width=3)
    im.alpha_composite(layer)


def place_pack(im, pack, t_pop, y_base=520, max_w=780, drift=0.0, x_offset=0, alpha=1.0):
    pop = ease_out_back(min(1.0, max(0.0, t_pop)))
    if pop < 0.02 or alpha < 0.02:
        return None
    p = pack.copy()
    p = ImageEnhance.Brightness(p).enhance(1.10)
    p = ImageEnhance.Contrast(p).enhance(1.08)
    p.thumbnail((max_w, int(max_w * 0.85)), Image.Resampling.LANCZOS)
    scale = (0.86 + 0.14 * pop) * (1.0 + 0.02 * drift)
    pw = max(1, int(p.size[0] * scale))
    ph = max(1, int(p.size[1] * scale))
    pp = p.resize((pw, ph), Image.Resampling.LANCZOS)
    aa = min(1.0, pop) * alpha
    if aa < 0.99:
        pp.putalpha(pp.split()[-1].point(lambda a: int(a * aa)))
    px = (W - pw) // 2 + x_offset
    py = y_base + int((1 - pop) * 80)
    soft_shadow(im, pp, px, py, a=int(160 * aa))
    if pop > 0.55:
        ref = floor_reflection(pp, op=0.26 * min(1.0, (pop - 0.55) / 0.45) * alpha)
        im.alpha_composite(ref, (px, py + ph - 8))
    im.alpha_composite(pp, (px, py))
    return px, py, pw, ph


def glint(im, x, y, t_local, scale=1.0):
    u = ease_out(min(1.0, max(0.0, t_local)))
    if u < 0.05 or u > 0.95:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = int(200 * math.sin(math.pi * u))
    s = int(18 * scale)
    d.ellipse([x - s, y - s // 2, x + s, y + s // 2], fill=(255, 240, 200, a))
    d.line([(x - s * 2, y), (x + s * 2, y)], fill=(*GOLD_SOFT, a), width=2)
    im.alpha_composite(layer)


def line_window(t, start, end, fade_in=0.28, fade_out=0.30):
    if t < start or t > end:
        return 0.0
    u = 1.0
    if t < start + fade_in:
        u = ease_out((t - start) / fade_in)
    if t > end - fade_out:
        u *= max(0.0, 1.0 - (t - (end - fade_out)) / fade_out)
    return u


def frame_at(t: float) -> Image.Image:
    im = navy_field(0.92 + 0.08 * math.sin(t * 0.35))
    apply_logo(im, max(0.85, min(1.0, t / 0.25)) * 0.94, y=44, size=100)

    # ---- 0–2.2 gold drop (already mid-fall on frame 0) ----
    if t < 2.35:
        gold_drop(im, t + 0.35)
        caption(im, "נוזל לגברים", 1480, 48, IVORY, max(0.88, line_window(t, 0.0, 2.15)))

    # ---- 2.2–4.6 one carton ----
    if 2.05 < t < 4.70:
        local = t - 2.20
        fade = 1.0
        if t > 4.35:
            fade = max(0.0, 1.0 - (t - 4.35) / 0.35)
        if fade > 0.02:
            drift = min(1.0, max(0.0, local / 2.2))
            place_pack(im, PACK_ONE, max(0.15, local / 0.40), y_base=500, max_w=560, drift=drift * 0.8, alpha=fade)
        caption(im, "קירקלנד חמישה אחוזים", 1480, 42, GOLD_SOFT, line_window(t, 2.25, 4.45))

    # ---- 4.6–9.4 twin lock + year ----
    if t >= 4.45:
        local = t - 4.60
        # slide-in: start offset left then settle
        slide = ease_out(min(1.0, max(0.0, local / 0.55)))
        x_off = int(-90 * (1 - slide))
        drift = min(1.0, max(0.0, local / 4.0))
        pack_a = 1.0
        y_base = 480
        # from 9.4 lift packs up for price
        if t >= 9.40:
            lift = ease_out(min(1.0, (t - 9.40) / 0.45))
            y_base = int(480 - 160 * lift)
        place_pack(
            im,
            PACK_FULL,
            max(0.01, local / 0.40),
            y_base=y_base,
            max_w=820,
            drift=drift,
            x_offset=x_off,
            alpha=pack_a,
        )
        if 4.9 < t < 6.2:
            glint(im, W // 2 + 40, 700, (t - 4.9) / 0.7, scale=1.3)

    if 4.60 <= t < 7.15:
        caption(im, "שתי קופסאות יחד", 1480, 46, IVORY, line_window(t, 4.65, 7.05))
    elif 7.10 <= t < 9.45:
        caption(im, "שנה שלמה מראש", 1480, 48, GOLD_SOFT, line_window(t, 7.15, 9.35))

    # ---- 9.4–11.8 price ----
    if t >= 9.40:
        pu = ease_out(min(1.0, (t - 9.45) / 0.35))
        # spelled price then holds under as ₪765 dominates
        if t < 11.85:
            caption(
                im,
                "שבע מאות שישים וחמש שקל",
                1320,
                28,
                MUTED,
                line_window(t, 9.50, 11.70) * 0.95,
            )
        # Big ₪765 — Latin font
        if pu > 0.05:
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            f = font(72, True, he=False)
            price = "₪765"
            tw, th, bb = text_bb(d, price, f)
            a = int(255 * pu)
            # shadow
            d.text(((W - tw) // 2 - bb[0] + 2, 1385 - bb[1] + 2), price, font=f, fill=(0, 0, 0, int(a * 0.4)))
            d.text(((W - tw) // 2 - bb[0], 1385 - bb[1]), price, font=f, fill=(*GOLD_SOFT, a))
            # gold hairline under price
            if t >= 11.70:
                hu = ease_out(min(1.0, (t - 11.70) / 0.25))
                rw = int(160 * hu)
                d.rounded_rectangle(
                    [(W - rw) // 2, 1385 + th + 10, (W + rw) // 2, 1385 + th + 14],
                    2,
                    fill=(*GOLD, int(230 * hu)),
                )
            im.alpha_composite(layer)

    # ---- 11.8–14 free ship ----
    if t >= 11.80:
        caption(im, "משלוח חינם עד הבית", 1520, 40, IVORY, line_window(t, 11.85, 14.0, fade_out=0.15))
        disc = ease_out(min(1.0, (t - 12.2) / 0.3))
        text_c(im, "תוצאות משתנות בין אנשים", 1788, 18, (100, 110, 128), int(150 * disc))

    return im


def make_cover() -> Image.Image:
    im = navy_field(0.95)
    apply_logo(im, 0.95, y=48, size=104)
    place_pack(im, PACK_FULL, 1.0, y_base=420, max_w=800, drift=0.5)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(78, True, he=False)
    price = "₪765"
    tw, th, bb = text_bb(d, price, f)
    d.text(((W - tw) // 2 - bb[0] + 2, 1180 - bb[1] + 2), price, font=f, fill=(0, 0, 0, 120))
    d.text(((W - tw) // 2 - bb[0], 1180 - bb[1]), price, font=f, fill=(*GOLD_SOFT, 255))
    im.alpha_composite(layer)
    caption(im, "משלוח חינם עד הבית", 1320, 36, IVORY, 1.0)
    caption(im, "מארז כפול קירקלנד", 1420, 32, MUTED, 1.0)
    return im.convert("RGB")


def main():
    print(f"two-boxes v1 {N}f @{FPS}")
    for i in range(N):
        t = i / FPS
        fr = frame_at(t).convert("RGB")
        fr.save(FRAMES / f"f_{i:04d}.jpg", quality=93, optimize=True)
        if i % 60 == 0:
            print(f"frame {i} {t:.1f}s")
        if i in (0, 60, 150, 300, 420, 540, 600, 720, 800):
            fr.save(QA / f"qa_{i:04d}.jpg", quality=92)
    cover = make_cover()
    cover.save(EXPORTS / "MinoxShop-two-boxes_v1-COVER.jpg", quality=94, optimize=True)
    cover.save(QA / "cover.jpg", quality=94)
    print("DONE")


if __name__ == "__main__":
    main()
