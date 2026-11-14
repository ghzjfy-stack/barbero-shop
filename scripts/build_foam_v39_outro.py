#!/usr/bin/env python3
"""v39 focused CTA outro — Rogaine double hero only, CTA raised above TT UI."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

sys.path.insert(0, "/tmp/foam-v39")
from brand_logo import apply_brand_logo

OUT = Path("/tmp/foam-v39/outro60")
OUT.mkdir(parents=True, exist_ok=True)
W, H, FPS = 1080, 1920, 60
N = 240  # 4.0s
HEB_B = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Bold.ttf"
CREAM, CREAM2 = (245, 240, 232), (252, 248, 242)
GOLD, INK, NAVY, WHITE = (196, 158, 86), (22, 26, 38), (14, 28, 52), (255, 255, 255)


def font(size, bold=True):
    return ImageFont.truetype(HEB_B, size)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_out_back(t):
    t = max(0.0, min(1.0, t))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def cream_field():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.42) / (H * 0.9)) ** 2)
    mix = np.clip(1 - 0.2 * r, 0.75, 1.0)
    arr = np.array(CREAM, np.float32) + (np.array(CREAM2, np.float32) - np.array(CREAM, np.float32)) * mix[:, :, None]
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(wash)
    d.ellipse((-200, 1000, 560, 1800), fill=(255, 220, 180, 26))
    return Image.alpha_composite(im, wash.filter(ImageFilter.GaussianBlur(70)))


def reflection(p, op=0.3, frac=0.34):
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


def soft_shadow(c, box, x, y, a=120):
    sh = Image.new("RGBA", (box.size[0] + 70, 64), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([10, 16, box.size[0] + 55, 46], fill=(30, 22, 14, int(a * 0.55)))
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (x - 35, y + box.size[1] - 10))


def text_c(im, txt, y, size, fill, alpha=255):
    f = font(size)
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bb = d.textbbox((0, 0), txt, font=f, language="he")
    x = (W - (bb[2] - bb[0])) // 2 - bb[0]
    d.text((x + 2, y + 3), txt, font=f, fill=(0, 0, 0, int(80 * alpha / 255)), language="he")
    d.text((x, y), txt, font=f, fill=(*fill, alpha), language="he")
    im.alpha_composite(layer)


def load_dbl():
    dbl = Image.open("/tmp/foam-v20/double_on_cream.png").convert("RGBA")
    rgb = np.array(dbl.convert("RGB"))
    cream = np.array([248, 242, 230], np.float32)
    dist = np.linalg.norm(rgb.astype(np.float32) - cream, axis=2)
    a = np.where(dist < 26, 0, 255).astype(np.uint8)
    a = np.where(a > 40, 255, a).astype(np.uint8)
    dbl.putalpha(Image.fromarray(a, "L").filter(ImageFilter.GaussianBlur(0.5)))
    bb = dbl.getbbox()
    dbl = dbl.crop(bb) if bb else dbl
    h_target = 720
    sc = h_target / dbl.size[1]
    return dbl.resize((max(1, int(dbl.size[0] * sc)), h_target), Image.Resampling.LANCZOS)


def frame(i, dbl):
    t = i / FPS
    im = cream_field()
    ta = int(255 * ease_out(min(1, t / 0.25)))
    text_c(im, "מארז כפול לחצי שנה", 200, 48, INK, ta)
    if ta > 40:
        d = ImageDraw.Draw(im)
        rw = int(150 * ease_out(min(1, (t - 0.1) / 0.25)))
        d.rounded_rectangle([(W - rw) // 2, 275, (W + rw) // 2, 279], 2, fill=GOLD + (ta,))
    text_c(im, "המארז המקורי מארה״ב", 300, 30, (70, 74, 88), int(ta * 0.92))

    pop = ease_out_back(min(1.0, max(0.0, (t - 0.15) / 0.35)))
    pop_c = max(0.0, min(1.0, pop))
    drift = 1.0 + 0.03 * min(1, max(0, (t - 0.6) / 3.2))
    pw = max(1, int(dbl.size[0] * (0.88 + 0.12 * pop_c) * drift))
    ph = max(1, int(dbl.size[1] * (0.88 + 0.12 * pop_c) * drift))
    pp = dbl.resize((pw, ph), Image.Resampling.LANCZOS)
    if pop_c < 1:
        pp = pp.copy()
        pp.putalpha(pp.split()[-1].point(lambda a: int(a * pop_c)))
    px = (W - pw) // 2
    py = 420 + int((1 - pop_c) * 90)
    soft_shadow(im, pp, px, py, a=int(140 * pop_c))
    if pop_c > 0.5:
        im.alpha_composite(reflection(pp, op=0.32 * min(1, (pop_c - 0.5) / 0.5)), (px, py + ph - 6))
    im.alpha_composite(pp, (px, py))

    # CTA raised — clear of TikTok UI (~bottom 180px unsafe)
    cta_a = ease_out(min(1.0, max(0.0, (t - 0.7) / 0.3)))
    if cta_a > 0.05:
        for idx, (txt, yy, navy) in enumerate(
            [("להזמנה עכשיו", 1380, True), ("משלוח חינם עד הבית", 1485, False)]
        ):
            f = font(34 if idx == 0 else 28)
            bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), txt, font=f, language="he")
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            pw2, ph2 = tw + 64, th + 28
            pill = Image.new("RGBA", (pw2, ph2), (0, 0, 0, 0))
            fill = NAVY + (int(245 * cta_a),) if navy else (255, 255, 255, int(245 * cta_a))
            fg = (255, 255, 255, int(255 * cta_a)) if navy else INK + (int(255 * cta_a),)
            ImageDraw.Draw(pill).rounded_rectangle([0, 0, pw2 - 1, ph2 - 1], ph2 // 2, fill=fill)
            if not navy:
                ImageDraw.Draw(pill).rounded_rectangle(
                    [1, 1, pw2 - 2, ph2 - 2], ph2 // 2, outline=NAVY + (int(160 * cta_a),), width=2
                )
            ImageDraw.Draw(pill).text((32 - bb[0], 14 - bb[1]), txt, font=f, fill=fg, language="he")
            # gentle pulse on primary CTA
            pulse = 1.0 + (0.03 * math.sin(t * 6) if idx == 0 and t > 1.2 else 0)
            if abs(pulse - 1.0) > 0.001:
                nw, nh = int(pw2 * pulse), int(ph2 * pulse)
                pill = pill.resize((nw, nh), Image.Resampling.LANCZOS)
                pw2, ph2 = nw, nh
            im.alpha_composite(pill, ((W - pw2) // 2, yy + int((1 - cta_a) * 30)))

    im = apply_brand_logo(im, t + 8.0, y=36, size=96)
    return im


def main():
    dbl = load_dbl()
    for i in range(N):
        frame(i, dbl).convert("RGB").save(OUT / f"o_{i:04d}.jpg", quality=94, optimize=True)
        if i % 60 == 0:
            print("outro", i)
    print("DONE outro", N)


if __name__ == "__main__":
    main()
