#!/usr/bin/env python3
"""MinoxShop brand logo overlay — CapCut-style plate + pulse + wink on every frame."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

LOGO_SRC = Path("/tmp/foam-v28/logo.png")
W, H = 1080, 1920


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def wink(layer: Image.Image, cx: int, cy: int, phase: float, scale: float = 0.85):
    pulse = math.sin(math.pi * max(0.0, min(1.0, phase)))
    if pulse < 0.06:
        return
    a = int(240 * pulse)
    sp = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sp)
    r = int(14 * scale * (0.5 + 0.5 * pulse))
    d.line([(cx - r, cy), (cx + r, cy)], fill=(255, 248, 220, a), width=2)
    d.line([(cx, cy - r), (cx, cy + r)], fill=(255, 248, 220, a), width=2)
    c = max(2, int(3 * scale * pulse))
    d.ellipse([cx - c, cy - c, cx + c, cy + c], fill=(255, 255, 255, a))
    layer.alpha_composite(sp.filter(ImageFilter.GaussianBlur(1.5)))
    layer.alpha_composite(sp)


_LOGO = None


def logo_base(size: int = 128) -> Image.Image:
    global _LOGO
    if _LOGO is None:
        im = Image.open(LOGO_SRC).convert("RGBA")
        im.thumbnail((size, size), Image.Resampling.LANCZOS)
        _LOGO = im
    return _LOGO.copy()


def apply_brand_logo(im: Image.Image, t: float, *, y: int = 56, size: int = 128) -> Image.Image:
    """Composite branded logo with entrance, soft pulse, and periodic wink.

    t = seconds from start of the full cut.
    """
    if im.mode != "RGBA":
        im = im.convert("RGBA")

    # entrance
    enter = ease_out(min(1.0, t / 0.45))
    if enter < 0.02:
        return im

    # gentle breathing pulse after land
    pulse = 1.0 + 0.04 * math.sin(t * math.pi * 1.15) * min(1.0, max(0.0, t - 0.5))
    logo = logo_base(size)
    lw = max(1, int(logo.size[0] * pulse))
    lh = max(1, int(logo.size[1] * pulse))
    logo = logo.resize((lw, lh), Image.Resampling.LANCZOS)

    # white rounded plate (classic reel look)
    pad = 14
    plate_w, plate_h = lw + pad * 2, lh + pad * 2
    plate = Image.new("RGBA", (plate_w, plate_h), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle(
        [0, 0, plate_w - 1, plate_h - 1],
        18,
        fill=(255, 255, 255, int(235 * enter)),
    )
    # soft drop shadow
    sh = Image.new("RGBA", (plate_w + 30, plate_h + 30), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        [8, 10, plate_w + 18, plate_h + 18], 20, fill=(20, 16, 12, int(50 * enter))
    )
    sh = sh.filter(ImageFilter.GaussianBlur(10))

    # slide down slightly on entrance
    dy = int((1 - enter) * 24)
    lx = (W - plate_w) // 2
    ly = y + dy

    # alpha on logo
    logo.putalpha(logo.split()[-1].point(lambda a: int(a * enter)))

    im.alpha_composite(sh, (lx - 8, ly - 6))
    im.alpha_composite(plate, (lx, ly))
    im.alpha_composite(logo, (lx + pad, ly + pad))

    # wink on top-right of plate every ~2.4s
    cycle = (t - 0.7) % 2.4
    wink(im, lx + plate_w - 10, ly + 12, cycle / 0.28, scale=0.9)
    return im
