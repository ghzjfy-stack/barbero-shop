#!/usr/bin/env python3
"""MinoxShop Member's Mark — clipper fake-out v8 (aim 9.5/10 upload).

Hook uses a real hand + classic barber clipper on scalp (instantly readable),
not a floating toy cutout. Product mid stays clean 6-pack; logo CTA-only.
"""

from __future__ import annotations

import math
import os
import shutil
import struct
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H, FPS, DUR = 1080, 1920, 30, 24.0
N = int(round(FPS * DUR))
COVER_HOLD_SEC = 0.8
COVER_HOLD_N = int(round(COVER_HOLD_SEC * FPS))

ASSETS = Path(os.environ.get("MM_ASSETS", "/tmp/mm-reel"))
OUT = Path(os.environ.get("MM_OUT", "/tmp/mm-clipper-v8"))
ART = Path("/opt/cursor/artifacts")
LOGO_PATH = Path(os.environ.get("MINOX_LOGO", "/tmp/minox-mp/main-logo.png"))
_REPO_DIR = Path(__file__).resolve().parent.parent / "reels/members-mark-liquid-v8/assets"
_REPO_CLIPPER = _REPO_DIR / "clipper_rgba.png"
_REPO_HOOK = _REPO_DIR / "clipper_hand_hook.jpg"
CLIPPER_PATH = Path(os.environ.get("MM_CLIPPER", str(_REPO_CLIPPER if _REPO_CLIPPER.exists() else ASSETS / "clipper_rgba.png")))
_CLIPPER_CACHE: Image.Image | None = None
_HOOK_CACHE: Image.Image | None = None


def load_clipper() -> Image.Image | None:
    global _CLIPPER_CACHE
    if _CLIPPER_CACHE is not None:
        return _CLIPPER_CACHE
    for path in (CLIPPER_PATH, _REPO_CLIPPER, ASSETS / "clipper_rgba.png"):
        if path.exists():
            _CLIPPER_CACHE = Image.open(path).convert("RGBA")
            return _CLIPPER_CACHE
    return None


def load_hook_plate(fallback: Image.Image) -> Image.Image:
    """Real hand + classic clipper on scalp — reads instantly as a haircut machine."""
    global _HOOK_CACHE
    if _HOOK_CACHE is not None:
        return _HOOK_CACHE
    for path in (_REPO_HOOK, ASSETS / "clipper_hand_hook.jpg", ASSETS / "scalp.jpg"):
        if path.exists():
            _HOOK_CACHE = load_rgb(path)
            return _HOOK_CACHE
    _HOOK_CACHE = fallback
    return _HOOK_CACHE

FONT = "/usr/share/fonts/truetype/croscore/Arimo-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/croscore/Arimo-Regular.ttf"

# Beat map — shipping text gets a real hold before yellow foam chip (was ~0.2s flash)
HOOK_END = 3.20
STOP_END = 4.60
PRODUCT_IN = 4.70
ID_END = 7.80
MONTHS_END = 10.00
PRICE_END = 12.60
FOAM_IN = 14.70
FOAM_PEAK = 17.60
FOAM_OUT = 20.00
SHIP_END = 21.20
FOAM_FADE = 1.05


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT if bold else FONT_REG, size)


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 3 * t * t - 2 * t * t * t


def load_rgb(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def cover_window(im: Image.Image, *, zoom: float, focus_x: float, focus_y: float) -> Image.Image:
    zoom = max(1.0, zoom)
    scale = max(W / im.width, H / im.height) * zoom
    nw, nh = max(W + 2, int(im.width * scale)), max(H + 2, int(im.height * scale))
    r = im.resize((nw, nh), Image.Resampling.LANCZOS)
    max_x, max_y = nw - W, nh - H
    x = int(max(0, min(max_x, max_x * focus_x)))
    y = int(max(0, min(max_y, max_y * focus_y)))
    return r.crop((x, y, x + W, y + H))


def fit_pack(
    im: Image.Image,
    *,
    zoom: float = 1.0,
    margin_x: float = 0.05,
    margin_y: float = 0.20,
    bg=(236, 238, 242),
) -> Image.Image:
    """Fit FULL pack width into 9:16 so all bottles stay visible (no side crop)."""
    zoom = max(0.85, zoom)
    usable_w = int(W * (1 - 2 * margin_x) / zoom)
    usable_h = int(H * (1 - 2 * margin_y) / zoom)
    scale = min(usable_w / im.width, usable_h / im.height)
    nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    r = im.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (W, H), bg)
    canvas.paste(r, ((W - nw) // 2, (H - nh) // 2))
    return canvas


def grade(im: Image.Image, *, contrast: float = 1.1, bright: float = 0.94, color: float = 1.05) -> Image.Image:
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Color(im).enhance(color)
    return ImageEnhance.Brightness(im).enhance(bright)


def phone_photo(im: Image.Image, *, seed: int = 0, strength: float = 1.0) -> Image.Image:
    """Break AI-clean look: grain, mild blur/sharpen, vignette — keeps the read intact."""
    s = max(0.0, min(1.5, strength))
    arr = np.array(im.convert("RGB")).astype(np.float32)
    h, w = arr.shape[:2]
    rng = np.random.default_rng(19_000 + int(seed) % 10_000)
    grain = rng.normal(0, 5.5 * s, (h, w)).astype(np.float32)
    arr[..., 0] += grain * 0.9
    arr[..., 1] += grain * 0.85
    arr[..., 2] += grain * 0.95
    # soft vignette
    yy, xx = np.mgrid[0:h, 0:w]
    rad = np.sqrt(((yy - h / 2) / (h * 0.75)) ** 2 + ((xx - w / 2) / (w * 0.75)) ** 2)
    vig = np.clip(1.0 - 0.18 * s * (rad ** 1.5), 0.82, 1.0)
    arr *= vig[..., None]
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    out = out.filter(ImageFilter.GaussianBlur(0.35 * s))
    out = ImageEnhance.Sharpness(out).enhance(1.0 + 0.22 * s)
    out = ImageEnhance.Color(out).enhance(0.92)  # AI often oversaturates
    out = ImageEnhance.Contrast(out).enhance(1.04)
    return out


def prepare_logo(path: Path, width: int = 200) -> Image.Image:
    logo = Image.open(path).convert("RGBA")
    arr = np.array(logo)
    rgb = arr[..., :3].astype(np.int16)
    white = (rgb[:, :, 0] > 232) & (rgb[:, :, 1] > 232) & (rgb[:, :, 2] > 225)
    arr[..., 3] = np.where(white, 0, 255).astype(np.uint8)
    logo = Image.fromarray(arr, "RGBA")
    if logo.getbbox():
        logo = logo.crop(logo.getbbox())
    h = int(logo.height * width / logo.width)
    return logo.resize((width, h), Image.Resampling.LANCZOS)


def draw_text(d: ImageDraw.ImageDraw, xy, text: str, *, size: int, fill, bold: bool = True, anchor="mm"):
    f = font(size, bold)
    kw = dict(font=f, fill=fill, anchor=anchor)
    if any("\u0590" <= c <= "\u05FF" for c in text):
        kw["direction"] = "rtl"
        kw["language"] = "he"
    d.text(xy, text, **kw)


def chip_block(
    canvas: Image.Image,
    y: int,
    lines: list[str],
    *,
    size: int,
    opacity: float,
    style: str = "dark",
    pop: float = 1.0,
):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    f = font(size)
    widths, heights = [], []
    for line in lines:
        bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), line, font=f)
        widths.append(bb[2] - bb[0])
        heights.append(bb[3] - bb[1])
    pad_x, pad_y, gap = 40, 24, 12
    # pop = entrance scale (starts slightly small, lands at 1.0)
    scale = 0.88 + 0.12 * max(0.0, min(1.0, pop))
    box_w = int((max(widths) + pad_x * 2) * scale)
    box_h = int((sum(heights) + gap * (len(lines) - 1) + pad_y * 2) * scale)
    x0 = (W - box_w) // 2
    y0 = y
    if style == "stamp":
        fill = (8, 12, 20, int(235 * opacity))
        radius = 18
    elif style == "alert":
        fill = (200, 18, 28, int(245 * opacity))
        radius = 14
    elif style == "hook":
        fill = (255, 214, 40, int(245 * opacity))
        radius = 12
    else:
        fill = (0, 0, 0, int(205 * opacity))
        radius = 22
    d.rounded_rectangle((x0, y0, x0 + box_w, y0 + box_h), radius=radius, fill=fill)
    if style == "hook":
        d.rounded_rectangle(
            (x0, y0, x0 + box_w, y0 + box_h),
            radius=radius,
            outline=(20, 20, 20, int(180 * opacity)),
            width=4,
        )
    cy = y0 + pad_y
    text_fill = (12, 12, 14, int(255 * opacity)) if style == "hook" else (255, 255, 255, int(255 * opacity))
    tsize = max(18, int(size * scale))
    for i, line in enumerate(lines):
        draw_text(d, (W // 2, cy + int(heights[i] * scale) // 2), line, size=tsize, fill=text_fill)
        cy += int(heights[i] * scale) + gap
    canvas.alpha_composite(layer)


def paste_logo(canvas: Image.Image, logo: Image.Image, *, opacity: float = 1.0):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lw, lh = logo.size
    x = (W - lw) // 2
    y = int(H * 0.905)
    pillow = Image.new("RGBA", (lw + 36, lh + 28), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pillow)
    pd.rounded_rectangle((0, 0, lw + 36, lh + 28), radius=18, fill=(255, 255, 255, int(200 * opacity)))
    layer.alpha_composite(pillow, (x - 18, y - 14))
    mark = logo.copy()
    if opacity < 0.99:
        a = mark.split()[-1].point(lambda v: int(v * opacity))
        mark.putalpha(a)
    layer.alpha_composite(mark, (x, y))
    canvas.alpha_composite(layer)


def apply_shake(im: Image.Image, amount: float, t: float) -> Image.Image:
    if amount < 0.01:
        return im
    dx = int(amount * 14 * math.sin(t * 62))
    dy = int(amount * 11 * math.cos(t * 51))
    base = Image.new("RGB", (W, H), (18, 16, 16))
    base.paste(im, (dx, dy))
    return base


def flash_white(im: Image.Image, amount: float) -> Image.Image:
    if amount <= 0:
        return im
    white = Image.new("RGB", (W, H), (255, 255, 255))
    return Image.blend(im, white, min(1.0, amount))


def _prep_clipper(scale: float) -> Image.Image | None:
    """Resize classic clipper — blade teeth dominate, tip aimed down."""
    src = load_clipper()
    if src is None:
        return None
    # classic asset is wide (blade left); scale larger so teeth read clearly
    h = int(520 * scale)
    w = max(1, int(src.width * h / src.height))
    clip = src.resize((w, h), Image.Resampling.LANCZOS)
    # tip is bottom-left → rotate so teeth face down
    clip = clip.rotate(55, expand=True, resample=Image.Resampling.BICUBIC)
    a = clip.split()[-1].filter(ImageFilter.MinFilter(3))
    a = a.filter(ImageFilter.GaussianBlur(0.55))
    clip.putalpha(a)
    return clip


def draw_red_clipper(canvas: Image.Image, cx: float, tip_y: float, *, scale: float = 1.0, buzz: float = 0.0):
    """Photoreal red clipper — blade tip anchored at (cx, tip_y)."""
    jx = int(5 * buzz * math.sin(tip_y * 0.45 + 1.2))
    jy = int(3 * buzz * math.cos(cx * 0.35))
    cx, tip_y = int(cx) + jx, int(tip_y) + jy

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # soft contact shadow just under the teeth
    d.ellipse((cx - 55, tip_y + 6, cx + 55, tip_y + 48), fill=(0, 0, 0, 70))

    clip = _prep_clipper(scale)
    if clip is None:
        d.rounded_rectangle((cx - 70, tip_y - 180, cx + 70, tip_y + 10), radius=28, fill=(198, 22, 30, 255))
        canvas.alpha_composite(layer)
        return

    # tip = bottom-center of rotated bbox (blade teeth)
    px = cx - clip.width // 2
    py = tip_y - clip.height + 8
    # 1px dark holdout under the cutout kills residual halo on scalp
    hold = clip.split()[-1].filter(ImageFilter.MaxFilter(3))
    hold = hold.point(lambda v: 90 if v > 20 else 0)
    dark = Image.new("RGBA", clip.size, (18, 12, 10, 255))
    dark.putalpha(hold)
    layer.alpha_composite(dark, (px, py + 1))
    layer.alpha_composite(clip, (px, py))
    canvas.alpha_composite(layer)


def tip_contact(canvas: Image.Image, tip_y: float, t: float):
    """Soft dark contact under the blade only — no red laser stripe on the hair."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x = int(W * 0.50 + 4 * math.sin(t * 18))
    tip = int(tip_y)
    d.ellipse((x - 48, tip + 2, x + 48, tip + 36), fill=(12, 8, 6, 55))
    canvas.alpha_composite(layer)


def chip_at(t: float):
    """Returns lines, opacity, style, size, pop (0→1 entrance)."""
    def pop_since(start: float, win: float = 0.28) -> float:
        return ease_out(min(1.0, max(0.0, (t - start) / win)))

    if 0.05 <= t < HOOK_END:
        return ["לגלח את זה", "ולגמור עם זה?"], 1.0, "hook", 62, pop_since(0.05)
    if HOOK_END + 0.04 <= t < STOP_END:
        return ["רגע."], 1.0, "stamp", 132, pop_since(HOOK_END + 0.04, 0.22)
    if PRODUCT_IN <= t < ID_END:
        return ["מינוקסידיל 5%", "טיפות · Member's Mark"], 1.0, "dark", 50, pop_since(PRODUCT_IN)
    if ID_END <= t < MONTHS_END:
        return ["6 בקבוקים", "6 חודשים מלאים"], 1.0, "stamp", 56, pop_since(ID_END)
    if MONTHS_END <= t < PRICE_END:
        # Black Friday persuasion — hold long
        return ["BLACK FRIDAY", "375₪", "מחיר שובר שוק"], 1.0, "bf", 52, pop_since(MONTHS_END, 0.35)
    if PRICE_END <= t < FOAM_IN:
        # ~2.1s readable hold — was a 0.2s flash before yellow foam
        return ["משלוח חינם", "עד הבית עם שליח"], 1.0, "dark", 46, pop_since(PRICE_END, 0.40)
    if FOAM_IN <= t < FOAM_OUT:
        return ["יש גם קצף במלאי", "אותו 5 אחוז · Member's Mark"], 1.0, "hook", 48, pop_since(FOAM_IN, 0.55)
    if FOAM_OUT <= t < SHIP_END:
        return ["משלוח חינם עד הבית"], 1.0, "dark", 46, pop_since(FOAM_OUT, 0.35)
    if SHIP_END <= t < DUR - 0.08:
        return ["הקישור בפרופיל", "עכשיו"], 1.0, "stamp", 52, pop_since(SHIP_END)
    return None


def foam_mix(t: float) -> float:
    """0→1→0 soft envelope for foam plate blend (slower fades)."""
    if t < FOAM_IN or t > FOAM_OUT:
        return 0.0
    if t < FOAM_IN + FOAM_FADE:
        return ease_in_out((t - FOAM_IN) / FOAM_FADE)
    if t > FOAM_OUT - FOAM_FADE:
        return ease_in_out(1.0 - (t - (FOAM_OUT - FOAM_FADE)) / FOAM_FADE)
    return 1.0


def draw_sparkles(canvas: Image.Image, t: float, amount: float):
    """Soft glints over foam cans — pretty, not flare-spam."""
    if amount < 0.05:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # fixed pretty positions over 4-can pack (mid frame)
    seeds = [
        (0.28, 0.38), (0.42, 0.34), (0.55, 0.40), (0.68, 0.36),
        (0.35, 0.52), (0.50, 0.48), (0.62, 0.55), (0.45, 0.62),
        (0.58, 0.30), (0.33, 0.44),
    ]
    for i, (fx, fy) in enumerate(seeds):
        phase = (t * 3.2 + i * 0.73) % 1.0
        twinkle = max(0.0, math.sin(phase * math.pi)) ** 2
        a = int(200 * amount * twinkle)
        if a < 12:
            continue
        cx, cy = int(W * fx), int(H * fy)
        r = 3 + int(5 * twinkle)
        # 4-point sparkle
        d.line((cx - r * 2, cy, cx + r * 2, cy), fill=(255, 255, 255, a), width=2)
        d.line((cx, cy - r * 2, cx, cy + r * 2), fill=(255, 255, 255, a), width=2)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 250, 230, int(a * 0.7)))
    # soft foam bloom near center cans
    bloom = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bloom)
    br = int(40 + 30 * amount)
    bd.ellipse((W // 2 - br, int(H * 0.48) - br, W // 2 + br, int(H * 0.48) + br), fill=(255, 255, 255, int(55 * amount)))
    bloom = bloom.filter(ImageFilter.GaussianBlur(18))
    canvas.alpha_composite(bloom)
    canvas.alpha_composite(layer)


def beat_camera(t: float):
    if t < HOOK_END:
        # tighter punch into blade teeth — stronger scroll-stop, less empty scalp
        z = 1.38 + 0.22 * ease_out(t / HOOK_END) + 0.015 * math.sin(t * 7)
        return z, 0.58, 0.30, 0.0, 0.45 + 0.22 * math.sin(t * 20)
    if t < STOP_END:
        return 1.0, 0.5, 0.45, 0.0, 0.0
    u = t - PRODUCT_IN
    z = 1.02 + 0.06 * min(1.0, u / 10.0) + 0.012 * math.sin(u * 1.4)
    flash = 0.0
    if MONTHS_END <= t < MONTHS_END + 0.28:
        flash = 0.22
    elif FOAM_IN <= t < FOAM_IN + 0.45:
        flash = 0.08 * (1.0 - (t - FOAM_IN) / 0.45)
    return z, 0.5, 0.48, flash, 0.04


def draw_bf_stack(canvas: Image.Image, y: int, lines: list[str], *, opacity: float, pop: float):
    """Dedicated Black Friday price stack — badge + huge price + subline."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    scale = 0.86 + 0.14 * pop
    cy = y

    # BF badge
    bf = lines[0]
    fbf = font(44)
    bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), bf, font=fbf)
    ww, hh = bb[2] - bb[0], bb[3] - bb[1]
    bw, bh = int((ww + 52) * scale), int((hh + 26) * scale)
    bx = (W - bw) // 2
    d.rounded_rectangle((bx, cy, bx + bw, cy + bh), radius=12, fill=(196, 22, 32, int(245 * opacity)))
    draw_text(d, (W // 2, cy + bh // 2), bf, size=int(44 * scale), fill=(255, 255, 255, int(255 * opacity)))
    cy += bh + 18

    # price
    price = lines[1]
    fp = font(int(130 * scale))
    bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), price, font=fp)
    ww, hh = bb[2] - bb[0], bb[3] - bb[1]
    pw, ph = ww + 72, hh + 44
    px = (W - pw) // 2
    d.rounded_rectangle((px, cy, px + pw, cy + ph), radius=28, fill=(0, 0, 0, int(245 * opacity)))
    draw_text(d, (W // 2, cy + ph // 2), price, size=int(130 * scale), fill=(255, 255, 255, int(255 * opacity)))
    cy += ph + 18

    # sub
    sub = lines[2]
    fsub = font(46)
    bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), sub, font=fsub)
    ww, hh = bb[2] - bb[0], bb[3] - bb[1]
    sw, sh = ww + 48, hh + 28
    sx = (W - sw) // 2
    d.rounded_rectangle((sx, cy, sx + sw, cy + sh), radius=16, fill=(255, 205, 55, int(240 * opacity)))
    draw_text(d, (W // 2, cy + sh // 2), sub, size=46, fill=(20, 18, 12, int(255 * opacity)))
    canvas.alpha_composite(layer)


def frame_at(i: int, scalp: Image.Image, bottles: Image.Image, foam: Image.Image, logo: Image.Image) -> Image.Image:
    t = i / FPS
    zoom, fx, fy, flash, shake = beat_camera(t)

    if t < HOOK_END:
        # Real hand gripping a classic clipper — phone-grade to de-AI the plate
        hook = load_hook_plate(scalp)
        plate = cover_window(hook, zoom=zoom, focus_x=fx, focus_y=fy)
        plate = grade(plate, contrast=1.12, bright=0.94, color=0.98)
        plate = phone_photo(plate, seed=i, strength=0.85)
        canvas = plate.convert("RGBA")
    elif t < STOP_END:
        canvas = Image.new("RGBA", (W, H), (6, 8, 12, 255))
    else:
        mix = foam_mix(t)
        # Full 6-pack width — no box swap (that caused logo-on-product clutter)
        pack_zoom = 1.0 + 0.035 * min(1.0, max(0.0, (t - PRODUCT_IN) / 8.0))
        # Extra pad so top chips / BF stack clear bottle caps
        liquid = fit_pack(bottles, zoom=pack_zoom, margin_x=0.04, margin_y=0.24)
        liquid = grade(liquid, contrast=1.14, bright=0.97, color=1.05)
        if mix > 0.01:
            foam_plate = fit_pack(foam, zoom=1.0, margin_x=0.06, margin_y=0.24)
            foam_plate = grade(foam_plate, contrast=1.12, bright=1.0, color=1.05)
            plate = Image.blend(liquid, foam_plate, mix)
        else:
            plate = liquid
        canvas = plate.convert("RGBA")
        vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        vd = ImageDraw.Draw(vig)
        for k, a in ((0, 0), (1, 16), (2, 32)):
            m = 40 + k * 70
            vd.rectangle((0, 0, W, m), fill=(8, 14, 28, a))
            vd.rectangle((0, H - m, W, H), fill=(8, 14, 28, a))
        canvas = Image.alpha_composite(canvas, vig)
        if mix > 0.08:
            draw_sparkles(canvas, t, mix)

    canvas_rgb = apply_shake(canvas.convert("RGB"), shake, t)
    canvas_rgb = flash_white(canvas_rgb, flash)
    canvas = canvas_rgb.convert("RGBA")

    info = chip_at(t)
    if info:
        lines, op, style, size, pop = info
        if t < HOOK_END:
            y = int(H * 0.08)
            chip_block(canvas, y, lines, size=size, opacity=op, style=style, pop=pop)
        elif style == "stamp" and lines == ["רגע."]:
            y = int(H * 0.40)
            chip_block(canvas, y, lines, size=size, opacity=op, style=style, pop=pop)
        elif style == "bf":
            # Top stack + tighter pack margin — was covering mid caps at 0.28
            y = int(H * 0.05)
            draw_bf_stack(canvas, y, lines, opacity=op, pop=pop)
        else:
            y = int(H * 0.07)
            chip_block(canvas, y, lines, size=size, opacity=op, style=style, pop=pop)

    # Logo ONLY on CTA — never over product hero (that looked messy on IG)
    if t >= SHIP_END:
        paste_logo(canvas, logo, opacity=min(1.0, (t - SHIP_END) / 0.35))

    return canvas.convert("RGB")

def make_audio(path: Path):
    sr = 44100
    n = int(DUR * sr)
    t = np.arange(n) / sr
    rng = np.random.default_rng(19)
    beat = 60 / 128

    def adsr(length, a=0.01, d=0.08, s=0.7, r=0.12):
        env = np.ones(length)
        ia, idc, ir = int(a * sr), int(d * sr), int(r * sr)
        if ia:
            env[:ia] = np.linspace(0, 1, ia)
        if idc:
            env[ia : ia + idc] = np.linspace(1, s, idc)
        if ir:
            env[-ir:] = np.linspace(env[-ir] if len(env) else s, 0, ir)
        return env

    # aggressive clipper buzz during hook → hard cut to silence
    buzz = np.zeros(n)
    hook_n = int(HOOK_END * sr)
    tt = np.arange(hook_n) / sr
    buzz[:hook_n] = (
        0.18 * np.sin(2 * np.pi * 78 * tt)
        + 0.12 * np.sin(2 * np.pi * 156 * tt)
        + 0.09 * np.sin(2 * np.pi * 312 * tt)
        + 0.07 * rng.standard_normal(hook_n)
    ) * (0.5 + 0.5 * np.sin(2 * np.pi * 32 * tt))
    # hard kill into «רגע» silence
    cut = int(0.04 * sr)
    if hook_n > cut:
        buzz[hook_n - cut : hook_n] *= np.linspace(1, 0, cut)
    # keep stop beat nearly silent (pattern interrupt)
    stop_a, stop_b = int(HOOK_END * sr), int(STOP_END * sr)
    mute = np.ones(n)
    mute[stop_a:stop_b] = 0.08

    kick = np.zeros(n)
    snare = np.zeros(n)
    for i, bt in enumerate(np.arange(STOP_END, DUR, beat)):
        i0 = int(bt * sr)
        length = int(0.2 * sr)
        if i0 + length > n:
            break
        tt = np.arange(length) / sr
        freq = 100 * np.exp(-17 * tt) + 40
        amp = 0.40 if i % 2 == 0 else 0.22
        kick[i0 : i0 + length] += amp * np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-10 * tt)
        if i % 2 == 1:
            sl = int(0.08 * sr)
            if i0 + sl <= n:
                noise = rng.standard_normal(sl)
                snare[i0 : i0 + sl] += 0.18 * noise * np.exp(-42 * np.arange(sl) / sr)

    bass = np.zeros(n)
    notes = [73.42, 73.42, 87.31, 65.41]
    bar = 4 * beat
    for bi, start in enumerate(np.arange(STOP_END, DUR, bar)):
        note = notes[bi % len(notes)]
        i0 = int(start * sr)
        length = min(int(bar * sr * 0.88), n - i0)
        if length <= 0:
            break
        tt = np.arange(length) / sr
        wave_b = 0.55 * np.sin(2 * np.pi * note * tt) + 0.22 * np.sin(2 * np.pi * note * 2 * tt)
        bass[i0 : i0 + length] += 0.15 * wave_b * adsr(length)

    impact = np.zeros(n)
    for wt, amp in (
        (0.04, 0.18),
        (HOOK_END, 0.62),
        (PRODUCT_IN, 0.42),
        (MONTHS_END, 0.72),  # BF price punch
        (FOAM_IN, 0.35),
        (SHIP_END, 0.28),
    ):
        i0 = int(wt * sr)
        length = min(int(0.32 * sr), n - i0)
        if length <= 0:
            continue
        tt = np.arange(length) / sr
        impact[i0 : i0 + length] += amp * np.sin(2 * np.pi * (55 * np.exp(-16 * tt)) * tt) * np.exp(-10 * tt)
        noise = np.convolve(rng.standard_normal(length), np.ones(60) / 60, mode="same")
        impact[i0 : i0 + length] += 0.11 * amp * noise * np.sin(np.linspace(0, np.pi, length))

    # short riser into BF price
    riser = np.zeros(n)
    r0 = int((MONTHS_END - 0.45) * sr)
    rl = int(0.45 * sr)
    if r0 > 0 and r0 + rl < n:
        tt = np.arange(rl) / sr
        riser[r0 : r0 + rl] = 0.14 * np.sin(2 * np.pi * (220 + 680 * (tt / 0.45)) * tt) * (tt / 0.45)

    pad = np.zeros(n)
    for f in (146.83, 174.61, 220.0):
        pad += np.sin(2 * np.pi * f * t)
    pad = pad / 4.5 * 0.045
    pad = np.convolve(pad, np.ones(41) / 41, mode="same")
    pad[: int(STOP_END * sr)] *= 0.15

    bed = (buzz + kick + snare + bass + pad + impact + riser) * mute
    # lift energy after product reveal (BF push)
    gate = np.ones(n)
    gi = int(PRODUCT_IN * sr)
    gate[gi:] = 1.10
    gbf = int(MONTHS_END * sr)
    gate[gbf:] = 1.18
    bed = bed * gate
    peak = np.max(np.abs(bed)) + 1e-9
    bed = np.tanh(bed / peak * 0.82) * 0.95
    fi, fo = int(0.04 * sr), int(0.35 * sr)
    bed[:fi] *= np.linspace(0, 1, fi)
    bed[-fo:] *= np.linspace(1, 0, fo)
    audio = np.clip(bed, -1, 1)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(x * 30000)) for x in audio))


def build_hook_cover(scalp: Image.Image) -> Image.Image:
    """Scroll-stop cover: blade-forward crop + lean offer (less sticker clutter)."""
    hook = load_hook_plate(scalp)
    # tighter on teeth/hand — stronger first-frame punch
    plate = cover_window(hook, zoom=1.62, focus_x=0.60, focus_y=0.28)
    plate = grade(plate, contrast=1.14, bright=0.93, color=0.97)
    plate = phone_photo(plate, seed=7, strength=1.0)
    canvas = plate.convert("RGBA")
    chip_block(canvas, int(H * 0.07), ["לגלח את זה", "ולגמור עם זה?"], size=60, opacity=1.0, style="hook", pop=1.0)

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = int(H * 0.78)

    def measure(text: str, size: int):
        bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), text, font=font(size))
        return bb[2] - bb[0], bb[3] - bb[1]

    # lean stack — price dominates, less banner spam
    price = "375₪"
    ww, hh = measure(price, 108)
    pw, ph = ww + 56, hh + 28
    px = (W - pw) // 2
    d.rounded_rectangle((px, y, px + pw, y + ph), radius=22, fill=(0, 0, 0, 235))
    draw_text(d, (W // 2, y + ph // 2), price, size=108, fill=(255, 255, 255, 255))
    y += ph + 12
    draw_text(d, (W // 2, y), "BLACK FRIDAY · 6 בקבוקים", size=32, fill=(255, 220, 80, 255))
    return Image.alpha_composite(canvas, layer).convert("RGB")


def encode_mp4(frames_dir: Path, audio: Path, mp4: Path, start_idx: int = 0, count: int | None = None):
    # ffmpeg image2 from numbered sequence — write a contiguous temp pattern if needed
    pattern = frames_dir / "f_%05d.png"
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-start_number", str(start_idx),
        "-i", str(pattern),
        "-i", str(audio),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest", "-movflags", "+faststart",
        str(mp4),
    ]
    if count is not None:
        cmd.insert(-1, "-frames:v")
        cmd.insert(-1, str(count))
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def render() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    frames = OUT / "frames"
    if frames.exists():
        shutil.rmtree(frames)
    frames.mkdir()

    scalp = load_rgb(ASSETS / "scalp.jpg")
    bottles = load_rgb(ASSETS / "liquid_gall.jpg")
    foam = load_rgb(ASSETS / "foam_gall.jpg")
    logo = prepare_logo(LOGO_PATH, width=180)

    def pad_pack(im: Image.Image, top=0.08, side=0.06, bottom=0.08) -> Image.Image:
        pad_t = int(im.height * top)
        pad_s = int(im.width * side)
        pad_b = int(im.height * bottom)
        out = Image.new("RGB", (im.width + 2 * pad_s, im.height + pad_t + pad_b), (236, 238, 242))
        out.paste(im, (pad_s, pad_t))
        return out

    bottles_p = pad_pack(bottles)
    foam_p = pad_pack(foam, top=0.16, side=0.14, bottom=0.16)

    cover = build_hook_cover(scalp)
    cover_path = OUT / "MinoxShop_MM_clipper_v8_COVER.jpg"
    cover.save(cover_path, quality=95)

    print(f"Rendering {N} frames (v8 de-AI — phone grain + tighter cover)…")
    for i in range(N):
        im = frame_at(i, scalp, bottles_p, foam_p, logo)
        im.save(frames / f"f_{i:05d}.png")
        if i % 60 == 0:
            print(f"  body {i}/{N}")

    audio = OUT / "audio.wav"
    make_audio(audio)

    mp4 = OUT / "MinoxShop_MM_clipper_v8_24s.mp4"
    encode_mp4(frames, audio, mp4)

    yt_frames = OUT / "frames_yt"
    if yt_frames.exists():
        shutil.rmtree(yt_frames)
    yt_frames.mkdir()
    for i in range(COVER_HOLD_N):
        cover.save(yt_frames / f"f_{i:05d}.png")
    for i in range(N):
        shutil.copy2(frames / f"f_{i:05d}.png", yt_frames / f"f_{COVER_HOLD_N + i:05d}.png")
    with wave.open(str(audio), "rb") as r:
        sr, sw, ch = r.getframerate(), r.getsampwidth(), r.getnchannels()
        body = r.readframes(r.getnframes())
    lead = b"\x00" * (int(COVER_HOLD_SEC * sr) * sw * ch)
    yt_audio = OUT / "audio_yt.wav"
    with wave.open(str(yt_audio), "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(sw)
        w.setframerate(sr)
        w.writeframes(lead + body)
    yt_mp4 = OUT / "MinoxShop_MM_clipper_v8_YT.mp4"
    encode_mp4(yt_frames, yt_audio, yt_mp4)

    ART.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mp4, ART / "DOWNLOAD_MinoxShop_MM_clipper_v8_24s.mp4")
    shutil.copy2(mp4, ART / "DOWNLOAD_MinoxShop_MM_clipper_v8_23s.mp4")  # alias
    shutil.copy2(mp4, ART / "DOWNLOAD_MinoxShop_MM_clipper_v8_22s.mp4")  # alias
    shutil.copy2(mp4, ART / "DOWNLOAD_MinoxShop_MM_clipper_v8_17s.mp4")  # alias
    shutil.copy2(yt_mp4, ART / "DOWNLOAD_MinoxShop_MM_clipper_v8_YT.mp4")
    shutil.copy2(cover_path, ART / "DOWNLOAD_MinoxShop_MM_clipper_v8_COVER.jpg")
    shutil.copy2(mp4, ART / "mm_clipper_v8_demo.mp4")
    for label, sec in (
        ("hook", 0.6),
        ("clipper", 2.2),
        ("stop", 3.8),
        ("product", 5.5),
        ("six", 8.5),
        ("price", 12.0),
        ("ship_pre", 13.5),
        ("foam", 17.5),
        ("cta", 22.0),
    ):
        frame_at(int(sec * FPS), scalp, bottles_p, foam_p, logo).save(ART / f"mm_v8_preview_{label}.jpg", quality=92)
    cover.save(ART / "mm_v8_preview_cover.jpg", quality=92)
    print("Wrote", mp4)
    print("Wrote", yt_mp4)
    return mp4


if __name__ == "__main__":
    render()
