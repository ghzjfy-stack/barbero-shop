#!/usr/bin/env python3
"""v32 — show authentic price ₪758 for MinoxShop foam reel.

- Opening: NO top logo — face + message own the frame
- Big bold Hebrew with heavy bottom gradient / shadow contrast
- Marketing hook in first second, then value line
- Product/offer/shelf keep CapCut cream language + logo from product beat
- 60fps throughout
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

sys.path.insert(0, "/tmp/foam-v32")
from brand_logo import apply_brand_logo

OUT = Path("/tmp/foam-v32/frames")
OUT.mkdir(parents=True, exist_ok=True)
PACKS = Path("/tmp/foam-v32/packs")
W, H, FPS = 1080, 1920, 60

# Body before shelf outro
BODY_SEC = 10.2
N_BODY = int(BODY_SEC * FPS)  # 612

HEB_B = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Bold.ttf"
HEB_R = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf"
LAT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LAT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
# Authentic site price: rogaine-double-man
PRICE = 758
PRICE_WAS = 998
PRICE_SAVE = 240
CREAM = (245, 240, 232)
CREAM2 = (252, 248, 242)
GOLD = (196, 158, 86)
INK = (22, 26, 38)
NAVY = (14, 28, 52)
WHITE = (255, 255, 255)


def font(size: int, bold: bool = True):
    return ImageFont.truetype(HEB_B if bold else HEB_R, size)


def font_lat(size: int, bold: bool = True):
    return ImageFont.truetype(LAT_B if bold else LAT_R, size)


def draw_price_block(im: Image.Image, y: int, alpha: int = 255, large: bool = True):
    """Site-authentic price. Digits via DejaVu (Noto Hebrew has no ASCII digits)."""
    if alpha < 8:
        return
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    price = f"₪{PRICE}"
    was = f"₪{PRICE_WAS}"
    f_price = font_lat(72 if large else 56, True)
    f_was = font_lat(28 if large else 24, True)
    bb = d.textbbox((0, 0), price, font=f_price)
    tw = bb[2] - bb[0]
    th = bb[3] - bb[1]
    x = (W - tw) // 2 - bb[0]
    # soft shadow
    for ox, oy, a in ((0, 4, 120), (0, 2, 90)):
        d.text((x + ox, y + oy), price, font=f_price, fill=(0, 0, 0, int(a * alpha / 255)))
    d.text((x, y), price, font=f_price, fill=(*INK, alpha))
    # strikethrough was-price under / beside
    wb = d.textbbox((0, 0), was, font=f_was)
    ww = wb[2] - wb[0]
    wx = (W - ww) // 2 - wb[0]
    wy = y + th + 8
    d.text((wx, wy), was, font=f_was, fill=(120, 124, 136, int(alpha * 0.85)))
    # strike line
    mid = wy + (wb[3] - wb[1]) // 2 + 2
    d.line([(wx, mid), (wx + ww, mid)], fill=(120, 124, 136, int(alpha * 0.9)), width=3)
    im.alpha_composite(layer)
    # Hebrew savings line (no digits — avoid tofu)
    draw_text_shadowed(
        im,
        "חיסכון של מאתיים ארבעים שקלים",
        wy + 36,
        26 if large else 24,
        (70, 74, 88),
        int(alpha * 0.95),
        bold=True,
        shadow=2,
    )



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
    """Clean cinematic gradient so white type pops — no hard bar."""
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = band.load()
    for y in range(top_y, H):
        u = (y - top_y) / max(1, H - top_y)
        # smooth ease — no mid bar
        a = int((0.05 + 0.82 * (u ** 1.65)) * 255 * strength)
        for x in range(W):
            px[x, y] = (10, 8, 6, a)
    # pre-blur whole band for silky edge (no seam)
    im.alpha_composite(band.filter(ImageFilter.GaussianBlur(18)))


def draw_text_shadowed(
    im: Image.Image,
    text: str,
    y: int,
    size: int,
    fill,
    alpha: int = 255,
    bold: bool = True,
    shadow: int = 6,
):
    f = font(size, bold)
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bb = d.textbbox((0, 0), text, font=f, language="he")
    x = (W - (bb[2] - bb[0])) // 2 - bb[0]
    # multi soft shadow for perfect contrast
    for ox, oy, a in ((0, shadow, 160), (0, shadow // 2, 120), (2, 2, 90)):
        d.text((x + ox, y + oy), text, font=f, fill=(0, 0, 0, int(a * alpha / 255)), language="he")
    d.text((x, y), text, font=f, fill=(*fill, alpha), language="he")
    im.alpha_composite(layer)
    return bb[3] - bb[1]


def gold_rule(im, y, w, alpha=255):
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([(W - w) // 2, y, (W + w) // 2, y + 4], 2, fill=GOLD + (alpha,))


def load_assets():
    hero = Path("/tmp/minox-brand/hero-home-lifestyle-bg.png")
    life = Image.open(hero if hero.exists() else "/tmp/foam-v28/qa/fix_20.jpg").convert("RGB")
    life = ImageEnhance.Color(life).enhance(1.06)
    life = ImageEnhance.Contrast(life).enhance(1.06)

    def cover(im: Image.Image) -> Image.Image:
        s = max(W / im.size[0], H / im.size[1])
        nw, nh = int(im.size[0] * s) + 1, int(im.size[1] * s) + 1
        im = im.resize((nw, nh), Image.Resampling.LANCZOS)
        # bias LEFT so more of the face stays in frame (avoid cheek crop)
        x = max(0, (nw - W) // 2 - 90)
        y = max(0, (nh - H) // 2 - 60)
        return im.crop((x, y, x + W, y + H))

    life = cover(life)

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
    return {"life": life, "dbl": dbl, "single": single}


def kenburns(base: Image.Image, t: float, zoom0=1.0, zoom1=1.12, pan_y=-0.35) -> Image.Image:
    z = zoom0 + (zoom1 - zoom0) * ease_in_out(t)
    nw, nh = int(W * z), int(H * z)
    im = base.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - W) // 2
    y = int((nh - H) // 2 + pan_y * (nh - H) * 0.18)
    y = max(0, min(y, nh - H))
    return im.crop((x, y, x + W, y + H)).convert("RGBA")


def frame_body(i: int, assets: dict) -> Image.Image:
    t = i / FPS

    # ---- HOOK 0–3.0s: face + marketing hook, NO logo ----
    if t < 3.0:
        local = t / 3.0
        im = kenburns(assets["life"], local, 1.0, 1.12, pan_y=-0.4)
        # slight cream grade wash (subtle, not muddy)
        wash = cream_field(0.12)
        wash.putalpha(Image.new("L", (W, H), 40))
        im = Image.alpha_composite(im, wash)
        bottom_readability_band(im, top_y=1280, strength=1.05)

        # Phase A (0–1.35): HOOK question — stop the scroll
        hook_a = ease_out(min(1.0, t / 0.28))
        hook_hold = 1.0 if t < 1.15 else ease_out(max(0.0, 1.0 - (t - 1.15) / 0.35))
        ha = int(255 * hook_a * hook_hold)
        if ha > 8:
            # no "?" glyph issues in Hebrew font — punchy hook line
            draw_text_shadowed(im, "איך שומרים על שיער מלא", 1320, 72, WHITE, ha, bold=True, shadow=10)

        # Phase B (from ~1.2): VALUE — big brand promise
        vb = ease_out(min(1.0, max(0.0, (t - 1.2) / 0.35)))
        va = int(255 * vb)
        if va > 8:
            # main line DRAMATICALLY large for mobile stop-scroll
            draw_text_shadowed(im, "מארז כפול לחצי שנה", 1440, 74, WHITE, va, bold=True, shadow=11)
            if va > 60:
                gold_rule(im, 1545, int(200 * ease_out(min(1, (t - 1.45) / 0.35))), va)
            draw_text_shadowed(
                im, "המארז המקורי מארה״ב", 1570, 42, (250, 246, 238), int(va * 0.98), bold=True, shadow=6
            )

        # subtle wink on hair — premium, not clutter
        wink_sparkle(im, 600, 400, (t - 0.9) / 0.35, scale=1.05)
        return im

    # ---- PRODUCT 3.0–6.7s ----
    if t < 6.7:
        local = (t - 3.0) / 3.7
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
        px = (W - pw) // 2  # perfect center
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
            for idx, (txt, yy) in enumerate(
                [("קצף רוגיין לגברים", 1180), ("שש פחיות לחצי שנה", 1265)]
            ):
                a = int(255 * chip_c)
                f = font(30 if idx == 0 else 26, True)
                tmp = Image.new("RGBA", (W, 90), (0, 0, 0, 0))
                d = ImageDraw.Draw(tmp)
                bb = d.textbbox((0, 0), txt, font=f, language="he")
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

        # Price — stops drop-off before site visit (authentic minox-shop.co.il)
        price_t = ease_out(min(1.0, max(0.0, (local - 0.48) / 0.22)))
        if price_t > 0.05:
            draw_price_block(im, 1385, alpha=int(255 * price_t), large=True)

        # logo only from product beat (not opening)
        im = apply_brand_logo(im, t - 3.0, y=36, size=96)
        return im

    # ---- OFFER 6.7–10.2s ----
    local = (t - 6.7) / 3.5
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

    im = apply_brand_logo(im, t - 3.0, y=36, size=96)
    return im


def main():
    assets = load_assets()
    print("life", assets["life"].size, "dbl", assets["dbl"].size, "fps", FPS, "frames", N_BODY)
    for i in range(N_BODY):
        fr = frame_body(i, assets)
        fr.convert("RGB").save(OUT / f"b_{i:04d}.jpg", quality=94, optimize=True)
        if i % 120 == 0:
            print("frame", i, f"{i/FPS:.2f}s")
    for qi in (20, 60, 90, 150, 240, 400, 550):
        Image.open(OUT / f"b_{qi:04d}.jpg").save(f"/tmp/foam-v32/qa/body_{qi}.jpg", quality=92)
    print("DONE body", N_BODY)


if __name__ == "__main__":
    main()
