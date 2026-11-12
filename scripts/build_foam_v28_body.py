#!/usr/bin/env python3
"""v27 CapCut cream BODY — same language as v26 outro (mirror / wink / bounce).

No navy bokeh poster beats. Continuous cream stage so the shelf outro feels earned.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
import sys
sys.path.insert(0, "/tmp/foam-v28")
from brand_logo import apply_brand_logo

OUT = Path("/tmp/foam-v28/body_frames")
OUT.mkdir(parents=True, exist_ok=True)
PACKS = Path("/tmp/foam-v27/packs")
W, H, FPS = 1080, 1920, 30

# Body length before outro (~10.2s) — then v26 cream shelf
N = 306  # 10.2s

HEB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
HEB_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
CREAM = (245, 240, 232)
CREAM2 = (252, 248, 242)
GOLD = (196, 158, 86)
INK = (28, 32, 44)
NAVY = (18, 32, 58)
WHITE = (255, 255, 255)


def font(size: int, bold: bool = True):
    return ImageFont.truetype(HEB if bold else HEB_R, size)


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
    # subtle warm shift
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


def draw_text(im, text, y, size, fill, alpha=255, bold=True):
    f = font(size, bold)
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bb = d.textbbox((0, 0), text, font=f, language="he")
    x = (W - (bb[2] - bb[0])) // 2 - bb[0]
    d.text((x, y + 2), text, font=f, fill=(0, 0, 0, int(70 * alpha / 255)), language="he")
    d.text((x, y), text, font=f, fill=(*fill, alpha), language="he")
    im.alpha_composite(layer)


def gold_rule(im, y, w, alpha=255):
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([(W - w) // 2, y, (W + w) // 2, y + 3], 2, fill=GOLD + (alpha,))


def load_assets():
    life = Image.open("/tmp/foam-v27/ref/life.jpg").convert("RGB")
    # Prefer sharp lifestyle master if available
    hero = Path("/tmp/minox-brand/hero-home-lifestyle-bg.png")
    if hero.exists():
        life = Image.open(hero).convert("RGB")
    # fit cover 1080x1920
    life = ImageEnhance.Color(life).enhance(1.05)
    life = ImageEnhance.Contrast(life).enhance(1.04)

    def cover(im: Image.Image) -> Image.Image:
        s = max(W / im.size[0], H / im.size[1])
        nw, nh = int(im.size[0] * s) + 1, int(im.size[1] * s) + 1
        im = im.resize((nw, nh), Image.Resampling.LANCZOS)
        x = (nw - W) // 2
        y = max(0, (nh - H) // 2 - 40)
        return im.crop((x, y, x + W, y + H))

    life = cover(life)

    # Double pack on cream — opaque
    dbl = Image.open("/tmp/foam-v20/double_on_cream.png").convert("RGBA")
    # knock cream-ish
    rgb = np.array(dbl.convert("RGB"))
    cream = np.array([248, 242, 230], np.float32)
    dist = np.linalg.norm(rgb.astype(np.float32) - cream, axis=2)
    a = np.where(dist < 26, 0, 255).astype(np.uint8)
    # harden
    a = np.where(a > 40, 255, a).astype(np.uint8)
    dbl.putalpha(Image.fromarray(a, "L").filter(ImageFilter.GaussianBlur(0.5)))
    bb = dbl.getbbox()
    dbl = dbl.crop(bb) if bb else dbl
    # fit height ~700
    h_target = 700
    sc = h_target / dbl.size[1]
    dbl = dbl.resize((max(1, int(dbl.size[0] * sc)), h_target), Image.Resampling.LANCZOS)

    # Single front pack for offer beat
    single = Image.open(PACKS / "rogaine_men.png").convert("RGBA")
    sh = 520
    single = single.resize((max(1, int(single.size[0] * sh / single.size[1])), sh), Image.Resampling.LANCZOS)

    logo = Image.open(PACKS / "logo.png").convert("RGBA")
    logo.thumbnail((120, 120), Image.Resampling.LANCZOS)
    return {"life": life, "dbl": dbl, "single": single, "logo": logo}


def kenburns(base: Image.Image, t: float, zoom0=1.0, zoom1=1.08, pan_y=0.0) -> Image.Image:
    z = zoom0 + (zoom1 - zoom0) * ease_in_out(t)
    nw, nh = int(W * z), int(H * z)
    im = base.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - W) // 2
    y = int((nh - H) // 2 + pan_y * (nh - H) * 0.15)
    y = max(0, min(y, nh - H))
    return im.crop((x, y, x + W, y + H)).convert("RGBA")


def frame_at(i: int, assets: dict) -> Image.Image:
    t = i / FPS  # seconds
    # Beats (cream CapCut language throughout)
    # 0.0–2.8  hook lifestyle
    # 2.8–6.6  product double + mirror bounce
    # 6.6–10.2 offer text + single pack mirror (NO navy)

    if t < 2.8:
        local = t / 2.8
        im = kenburns(assets["life"], local, 1.0, 1.10, pan_y=-0.3)
        # soft cream wash so it matches outro grade
        wash = cream_field(0.15)
        wash.putalpha(Image.new("L", (W, H), 55))
        im = Image.alpha_composite(im, wash)
        # bottom vignette for type
        vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(vig).rectangle([0, 1450, W, H], fill=(20, 16, 12, 110))
        im.alpha_composite(vig.filter(ImageFilter.GaussianBlur(40)))
        ta = int(255 * ease_out(min(1, max(0, (t - 0.35) / 0.45))))
        if ta > 10:
            draw_text(im, "מארז כפול לחצי שנה", 1520, 48, WHITE, ta)
            if ta > 80:
                gold_rule(im, 1590, int(140 * ease_out(min(1, (t - 0.7) / 0.4))), ta)
            draw_text(im, "שיער שנראה חזק יותר", 1610, 30, (240, 236, 228), int(ta * 0.9), bold=False)
        # wink on hairline area
        wink_sparkle(im, 620, 420, (t - 1.1) / 0.35, scale=1.1)
        wink_sparkle(im, 480, 380, (t - 1.8) / 0.3, scale=0.7)
        im = apply_brand_logo(im, t, y=36, size=96)
        return im

    if t < 6.6:
        local = (t - 2.8) / 3.8
        im = cream_field(0.05 + 0.05 * math.sin(local * math.pi))
        # headline
        ta = int(255 * ease_out(min(1, local / 0.18)))
        draw_text(im, "מארז כפול לחצי שנה", 220, 46, INK, ta)
        if ta > 60:
            gold_rule(im, 290, int(120 * ease_out(min(1, (local - 0.08) / 0.25))), ta)
        draw_text(im, "מקורי מארה״ב", 310, 30, (70, 74, 88), int(ta * 0.92), bold=False)

        # double pack bounce + mirror
        pop = ease_out_back(min(1.0, max(0.0, (local - 0.08) / 0.28)))
        pop_c = max(0.0, min(1.0, pop))
        dbl = assets["dbl"]
        ps = 0.82 + 0.18 * pop_c
        # slow drift zoom after land
        drift = 1.0 + 0.04 * ease_in_out(max(0, (local - 0.4) / 0.6))
        pw = max(1, int(dbl.size[0] * ps * drift))
        ph = max(1, int(dbl.size[1] * ps * drift))
        pp = dbl.resize((pw, ph), Image.Resampling.LANCZOS)
        if pop_c < 1:
            pp = pp.copy()
            pp.putalpha(pp.split()[-1].point(lambda a: int(a * pop_c)))
        dy = int((1 - pop_c) * 120)
        px = (W - pw) // 2
        py = 460 + dy
        soft_shadow(im, pp, px, py, a=int(130 * pop_c))
        if pop_c > 0.5:
            ref = reflection(pp, op=0.30 * min(1, (pop_c - 0.5) / 0.5), frac=0.34)
            im.alpha_composite(ref, (px, py + ph - 6))
        im.alpha_composite(pp, (px, py))
        wink_sparkle(im, px + int(pw * 0.72), py + 40, (local - 0.35) / 0.2, scale=1.0)
        wink_sparkle(im, px + int(pw * 0.28), py + 60, (local - 0.55) / 0.18, scale=0.75)

        # chips CapCut pop
        chip_t = ease_out_back(min(1.0, max(0.0, (local - 0.45) / 0.2)))
        chip_c = max(0.0, min(1.0, chip_t))
        if chip_c > 0.05:
            for idx, (txt, yy) in enumerate(
                [("קצף רוגיין לגברים", 1280), ("6 פחיות · חצי שנה", 1360)]
            ):
                a = int(255 * chip_c)
                # pill
                f = font(28 if idx == 0 else 24, True)
                tmp = Image.new("RGBA", (W, 80), (0, 0, 0, 0))
                d = ImageDraw.Draw(tmp)
                bb = d.textbbox((0, 0), txt, font=f, language="he")
                tw, th = bb[2] - bb[0], bb[3] - bb[1]
                pw2, ph2 = tw + 48, th + 22
                pill = Image.new("RGBA", (pw2, ph2), (0, 0, 0, 0))
                fill = NAVY + (int(230 * chip_c),) if idx == 0 else (255, 255, 255, int(235 * chip_c))
                fg = (255, 255, 255, a) if idx == 0 else INK + (a,)
                ImageDraw.Draw(pill).rounded_rectangle([0, 0, pw2 - 1, ph2 - 1], ph2 // 2, fill=fill)
                if idx == 1:
                    ImageDraw.Draw(pill).rounded_rectangle(
                        [1, 1, pw2 - 2, ph2 - 2], ph2 // 2, outline=NAVY + (int(160 * chip_c),), width=2
                    )
                ImageDraw.Draw(pill).text((24 - bb[0], 11 - bb[1]), txt, font=f, fill=fg, language="he")
                ox = int((1 - chip_c) * 40)
                im.alpha_composite(pill, ((W - pw2) // 2, yy + ox))
        im = apply_brand_logo(im, t, y=36, size=96)
        return im

    # --- Offer beat: cream CapCut typography + single pack (matches outro) ---
    local = (t - 6.6) / 3.6
    im = cream_field(0.08)
    # soft foam bubbles (subtle, same family as classic reel — not navy snow)
    rng = np.random.default_rng(7)
    bub = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    db = ImageDraw.Draw(bub)
    for k in range(28):
        bx = int(rng.integers(40, W - 40))
        by = int((rng.random() * H + local * 80 * (0.5 + rng.random())) % H)
        br = int(8 + rng.random() * 28)
        ba = int(18 + rng.random() * 22)
        db.ellipse([bx - br, by - br, bx + br, by + br], fill=(255, 255, 255, ba))
    im.alpha_composite(bub.filter(ImageFilter.GaussianBlur(1.2)))

    ta = int(255 * ease_out(min(1, local / 0.2)))
    draw_text(im, "עשרה אחוז", 230, 58, INK, ta)
    if ta > 40:
        rw = int(140 * ease_out(min(1, (local - 0.1) / 0.25)))
        gold_rule(im, 310, rw, ta)
        wink_sparkle(im, (W + rw) // 2 - 4, 311, (local - 0.25) / 0.18, scale=0.85)
    draw_text(im, "נקודות בונוס בנובמבר", 340, 34, INK, int(ta * 0.95))
    draw_text(im, "משלוח חינם עד הבית", 400, 30, (70, 74, 88), int(ta * 0.9), bold=False)

    # single pack bounce with mirror — same language as shelf
    pop = ease_out_back(min(1.0, max(0.0, (local - 0.15) / 0.3)))
    pop_c = max(0.0, min(1.0, pop))
    single = assets["single"]
    ps = 0.85 + 0.15 * pop_c
    drift = 1.0 + 0.03 * ease_in_out(max(0, (local - 0.45) / 0.55))
    pw = max(1, int(single.size[0] * ps * drift))
    ph = max(1, int(single.size[1] * ps * drift))
    pp = single.resize((pw, ph), Image.Resampling.LANCZOS)
    if pop_c < 1:
        pp = pp.copy()
        pp.putalpha(pp.split()[-1].point(lambda a: int(a * pop_c)))
    dy = int((1 - pop_c) * 100)
    px = (W - pw) // 2
    py = 760 + dy
    soft_shadow(im, pp, px, py, a=int(120 * pop_c))
    if pop_c > 0.5:
        ref = reflection(pp, op=0.28 * min(1, (pop_c - 0.5) / 0.5), frac=0.32)
        im.alpha_composite(ref, (px, py + ph - 6))
    im.alpha_composite(pp, (px, py))
    wink_sparkle(im, px + pw // 2 + 30, py + 30, (local - 0.4) / 0.2, scale=0.95)

    im = apply_brand_logo(im, t, y=36, size=96)
    return im


def main():
    assets = load_assets()
    print("life", assets["life"].size, "dbl", assets["dbl"].size, "single", assets["single"].size)
    for i in range(N):
        fr = frame_at(i, assets)
        fr.convert("RGB").save(OUT / f"b_{i:04d}.jpg", quality=94, optimize=True)
        if i % 60 == 0:
            print("frame", i, f"{i/FPS:.1f}s")
    for qi in (20, 60, 120, 180, 240, 290):
        Image.open(OUT / f"b_{qi:04d}.jpg").save(f"/tmp/foam-v27/qa/body_{qi}.jpg", quality=92)
    print("DONE body frames", N)


if __name__ == "__main__":
    main()
