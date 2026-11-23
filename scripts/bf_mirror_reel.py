#!/usr/bin/env python3
"""MinoxShop Black Friday mirror reel — 16s 1080x1920.

v3: pleasant warm BF audio, faster price smash, cleaner chips/CTA,
Arimo + libraqm RTL Hebrew.
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

W, H, FPS, DUR = 1080, 1920, 30, 16
N = FPS * DUR

ASSETS = Path(os.environ.get("MINOX_ASSETS", "/tmp/minox-mp"))
OUT = Path(os.environ.get("BF_OUT", "/tmp/bf-mirror-reel-v2"))
ART = Path("/opt/cursor/artifacts")

FONT = "/usr/share/fonts/truetype/croscore/Arimo-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/croscore/Arimo-Regular.ttf"

# Expert-ranked polish (Grok + Composer): show deal early, fewer chips, clean CTA.
COPY = {
    "hook": "BLACK FRIDAY",
    "hook_mid": "Rogaine מארז כפול",
    "hook_deal": "₪998 → ₪758",
    "hook_save": "חוסכים ₪240",
    "before_note": "מחיר מלא",
    "now_tag": "עכשיו רק",
    "month_line": "≈₪126 לחודש · 6 חודשים",
    "save_line": "חוסכים ₪240 על המארז",
    "chip1": "מקורי מארה״ב",
    "chip2": "מארז כפול · 6 חודשים",
    "chip_foot": "קצף 5% · משלוח עד הבית",
    "cta_product": "Rogaine מארז כפול",
    "cta_urgency": "עד סוף השבוע",
    "cta_action": "הקישור בפרופיל",
}

RED = (220, 40, 50)
WHITE = (255, 255, 255)
MUTED = (180, 185, 195)
GOLD = (255, 214, 110)
SOFT_GOLD = (255, 230, 170)


def font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT if bold else FONT_REG, size)


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 3 * t * t - 2 * t * t * t


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def fit_cover(im: Image.Image, tw: int, th: int, zoom: float = 1.0, pan: float = 0.0) -> Image.Image:
    """Cover crop with optional Ken Burns zoom (1.0+) and vertical pan 0..1."""
    scale = max(tw / im.width, th / im.height) * max(1.0, zoom)
    nw, nh = int(im.width * scale), int(im.height * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - tw) // 2
    max_y = max(0, nh - th)
    y = int(max_y * max(0.0, min(1.0, pan)))
    return im.crop((x, y, x + tw, y + th))


def fit_contain(im: Image.Image, tw: int, th: int) -> Image.Image:
    scale = min(tw / im.width, th / im.height)
    nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    return im.resize((nw, nh), Image.Resampling.LANCZOS)


def soft_product(im: Image.Image) -> Image.Image:
    """Knock back hard white product card edges into a soft studio plate."""
    arr = np.array(im).astype(np.float32)
    rgb = arr[..., :3]
    # near-white → transparent-ish fringe
    whiteness = np.min(rgb, axis=2)
    alpha = arr[..., 3]
    fringe = np.clip((whiteness - 230) / 25.0, 0, 1)
    alpha = alpha * (1.0 - fringe * 0.92)
    arr[..., 3] = alpha
    out = Image.fromarray(arr.astype(np.uint8), "RGBA")
    # soft shadow under product
    shadow = Image.new("RGBA", out.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse(
        (int(out.width * 0.08), int(out.height * 0.88), int(out.width * 0.92), int(out.height * 1.02)),
        fill=(0, 0, 0, 90),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    base = Image.new("RGBA", out.size, (0, 0, 0, 0))
    base = Image.alpha_composite(base, shadow)
    base = Image.alpha_composite(base, out)
    return base


def dark_bg(
    base: Image.Image | None = None,
    glow: tuple[int, int, int] = (35, 25, 20),
    zoom: float = 1.0,
    pan: float = 0.35,
    brightness: float = 0.32,
) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), (10, 11, 14, 255))
    if base is not None:
        bg = fit_cover(base.convert("RGBA"), W, H, zoom=zoom, pan=pan)
        bg = ImageEnhance.Brightness(bg).enhance(brightness)
        bg = ImageEnhance.Color(bg).enhance(0.6)
        bg = bg.filter(ImageFilter.GaussianBlur(14))
        canvas = Image.alpha_composite(canvas, bg)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    cx, cy = W // 2, int(H * 0.40)
    for r, a in ((520, 50), (340, 75), (200, 95)):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*glow, a))
    overlay = overlay.filter(ImageFilter.GaussianBlur(42))
    canvas = Image.alpha_composite(canvas, overlay)
    # soft vignette
    vig = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vig)
    vd.ellipse((-120, -80, W + 120, H + 80), fill=(0, 0, 0, 0))
    # draw radial by stacked rings
    for i in range(8):
        pad = 40 + i * 70
        vd.rectangle((0, 0, W, H), outline=(0, 0, 0, 12 + i * 8), width=pad)
    vig = vig.filter(ImageFilter.GaussianBlur(30))
    return Image.alpha_composite(canvas, vig)


def draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    *,
    size: int = 64,
    fill=WHITE,
    anchor: str = "mm",
    rtl: bool = True,
    stroke: int = 0,
    stroke_fill=(0, 0, 0),
    bold: bool = True,
) -> None:
    f = font(size, bold=bold)
    kwargs = dict(font=f, fill=fill, anchor=anchor)
    if stroke:
        kwargs["stroke_width"] = stroke
        kwargs["stroke_fill"] = stroke_fill
    has_he = any("\u0590" <= ch <= "\u05FF" for ch in text)
    if rtl and has_he:
        kwargs["direction"] = "rtl"
        kwargs["language"] = "he"
    draw.text(xy, text, **kwargs)


def shadow_text(draw, xy, text, **kwargs):
    x, y = xy
    shadow_kwargs = dict(kwargs)
    shadow_kwargs["fill"] = (0, 0, 0)
    shadow_kwargs["stroke"] = 0
    draw_text(draw, (x + 3, y + 4), text, **shadow_kwargs)
    draw_text(draw, xy, text, **kwargs)


def pill(
    canvas: Image.Image,
    cy: int,
    text: str,
    *,
    fill=(200, 30, 40, 235),
    text_fill=WHITE,
    size: int = 40,
    scale: float = 1.0,
) -> None:
    f = font(size)
    bbox = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pw, ph = int((tw + 72) * scale), int((th + 32) * scale)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0 = (W - pw) // 2
    y0 = cy - ph // 2
    d.rounded_rectangle((x0, y0, x0 + pw, y0 + ph), radius=ph // 2, fill=fill)
    draw_text(d, (W // 2, cy), text, size=int(size * scale), fill=text_fill, rtl=False)
    canvas.alpha_composite(layer)


def chip(canvas: Image.Image, cy: int, text: str, *, size: int = 42) -> None:
    f = font(size)
    bbox = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox(
        (0, 0), text, font=f, direction="rtl", language="he"
    )
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pw, ph = tw + 52, th + 30
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0 = (W - pw) // 2
    y0 = cy - ph // 2
    d.rounded_rectangle((x0, y0, x0 + pw, y0 + ph), radius=22, fill=(255, 255, 255, 235))
    draw_text(d, (W // 2, cy), text, size=size, fill=(18, 20, 24), rtl=True)
    canvas.alpha_composite(layer)


def paste_center(canvas: Image.Image, im: Image.Image, cy: int, max_w: int, max_h: int, scale: float = 1.0) -> None:
    im = fit_contain(im, int(max_w * scale), int(max_h * scale))
    x = (W - im.width) // 2
    y = cy - im.height // 2
    canvas.alpha_composite(im, (x, y))


def frame_at(i: int, assets: dict) -> Image.Image:
    t = i / FPS
    # Timing (expert: smash price faster)
    # 0.0-2.4 hook+deal | 2.4-4.0 old smash | 4.0-9.2 price hero | 9.2-12.4 chips | 12.4-16 CTA

    if t < 2.4:
        local = t / 2.4
        zoom = 1.0 + 0.04 * local
        canvas = Image.new("RGBA", (W, H), (8, 8, 10, 255))
        bg = fit_cover(assets["journey"].convert("RGBA"), W, H, zoom=zoom, pan=0.25 + 0.1 * local)
        bg = ImageEnhance.Brightness(bg).enhance(0.78)
        bg = ImageEnhance.Contrast(bg).enhance(1.12)
        grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(grad)
        for y in range(int(H * 0.48), H):
            a_g = int(230 * ((y - H * 0.48) / (H * 0.52)))
            gd.line((0, y, W, y), fill=(0, 0, 0, min(235, a_g)))
        canvas = Image.alpha_composite(canvas, bg)
        canvas = Image.alpha_composite(canvas, grad)
        d = ImageDraw.Draw(canvas)
        a = ease_out(min(1.0, t / 0.4))
        bounce = 1.0 + 0.03 * math.sin(min(1.0, t / 0.35) * math.pi) if t < 0.5 else 1.0
        if a > 0.05:
            pill(canvas, int(H * 0.58), COPY["hook"], size=36, scale=bounce)
            shadow_text(d, (W // 2, int(H * 0.68)), COPY["hook_mid"], size=52, fill=WHITE, stroke=2)
            # Deal visible in hook (expert: show numbers early)
            deal_a = ease_out(min(1.0, max(0.0, (t - 0.55) / 0.35)))
            if deal_a > 0.05:
                shadow_text(
                    d,
                    (W // 2, int(H * 0.78)),
                    COPY["hook_deal"],
                    size=58,
                    fill=GOLD,
                    stroke=2,
                    rtl=False,
                )
                shadow_text(
                    d,
                    (W // 2, int(H * 0.86)),
                    COPY["hook_save"],
                    size=40,
                    fill=SOFT_GOLD,
                    stroke=1,
                )
        return canvas.convert("RGB")

    if t < 4.0:
        # Short old-price smash (~1.6s)
        local = (t - 2.4) / 1.6
        canvas = dark_bg(assets["hero"], glow=(55, 20, 25), zoom=1.02 + 0.03 * local, brightness=0.26)
        d = ImageDraw.Draw(canvas)
        a = ease_out(min(1.0, local / 0.25))
        shake = int(8 * math.sin(local * 55)) if local > 0.55 else 0
        if a > 0.05:
            draw_text(d, (W // 2 + shake, int(H * 0.40)), COPY["before_note"], size=44, fill=GOLD)
            draw_text(d, (W // 2 + shake, int(H * 0.52)), "₪998", size=150, fill=WHITE, rtl=False, stroke=3)
            if local > 0.45:
                layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ld = ImageDraw.Draw(layer)
                cx, cy = W // 2 + shake, int(H * 0.52)
                s = 120
                ld.line((cx - s, cy - s, cx + s, cy + s), fill=(*RED, 235), width=16)
                ld.line((cx - s, cy + s, cx + s, cy - s), fill=(*RED, 235), width=16)
                canvas.alpha_composite(layer)
        return canvas.convert("RGB")

    if t < 9.2:
        # PRICE HERO — held longer
        local = (t - 4.0) / 5.2
        flash = 1.0 if local > 0.08 else ease_out(local / 0.08)
        glow = (30, 55, 50) if local > 0.12 else (80, 60, 30)
        canvas = dark_bg(None, glow=glow, zoom=1.0)
        # one-time teal/gold flash on cut
        if local < 0.12:
            flash_l = Image.new("RGBA", (W, H), (255, 200, 80, int(40 * (1 - local / 0.12))))
            canvas.alpha_composite(flash_l)

        pop_t = ease_out(min(1.0, local / 0.35))
        # scale 0.92 → 1.06 → 1.0
        if local < 0.35:
            pop = 0.92 + 0.14 * pop_t
        else:
            pop = 1.06 - 0.06 * ease_out(min(1.0, (local - 0.35) / 0.25))
            pop = max(1.0, pop)

        paste_center(canvas, assets["product"], int(H * 0.34), 820, 680, scale=pop)
        pill(canvas, int(H * 0.12), "BLACK FRIDAY", size=38)
        logo = fit_contain(assets["logo"], 110, 110)
        canvas.alpha_composite(logo, (W - 140, 36))

        d = ImageDraw.Draw(canvas)
        a = ease_out(min(1.0, max(0.0, (local - 0.15) / 0.3)))
        if a > 0.05:
            draw_text(d, (W // 2, int(H * 0.58)), COPY["now_tag"], size=42, fill=GOLD)
            # price bounce
            price_pop = 1.0
            if 0.15 < local < 0.55:
                pt = (local - 0.15) / 0.4
                price_pop = 0.92 + 0.14 * ease_out(pt) if pt < 0.7 else 1.06 - 0.06 * ((pt - 0.7) / 0.3)
            psz = int(148 * price_pop)
            draw_text(d, (W // 2, int(H * 0.68)), "₪758", size=psz, fill=WHITE, rtl=False, stroke=2)
            # ghost old price fade
            ghost = max(0.0, 1.0 - ease_out(min(1.0, max(0.0, (local - 0.35) / 0.45))))
            if ghost > 0.05:
                ox, oy = W // 2, int(H * 0.78)
                gfill = (int(MUTED[0] * ghost + 12 * (1 - ghost)),) * 3
                # approximate muted with alpha via darker blend
                draw_text(d, (ox, oy), "₪998", size=48, fill=(140, 145, 155), rtl=False)
                bb = d.textbbox((ox, oy), "₪998", font=font(48), anchor="mm")
                d.line((bb[0] - 8, (bb[1] + bb[3]) // 2, bb[2] + 8, (bb[1] + bb[3]) // 2), fill=RED, width=5)
            draw_text(d, (W // 2, int(H * 0.86)), COPY["save_line"], size=40, fill=SOFT_GOLD)
            draw_text(d, (W // 2, int(H * 0.93)), COPY["month_line"], size=34, fill=MUTED)
        return canvas.convert("RGB")

    if t < 12.4:
        # Two chips + footer (expert: less clutter)
        local = (t - 9.2) / 3.2
        canvas = dark_bg(None, glow=(28, 45, 55))
        paste_center(canvas, assets["product"], int(H * 0.30), 700, 540, scale=0.95)
        logo = fit_contain(assets["logo"], 100, 100)
        canvas.alpha_composite(logo, (W - 130, 36))
        for idx, text in enumerate((COPY["chip1"], COPY["chip2"])):
            appear = ease_out(min(1.0, max(0.0, (local - idx * 0.12) / 0.28)))
            if appear <= 0.05:
                continue
            cy = int(H * 0.58) + idx * 110 + int((1 - appear) * 22)
            chip(canvas, cy, text, size=42)
        foot_a = ease_out(min(1.0, max(0.0, (local - 0.35) / 0.3)))
        if foot_a > 0.05:
            d = ImageDraw.Draw(canvas)
            draw_text(d, (W // 2, int(H * 0.82)), COPY["chip_foot"], size=36, fill=SOFT_GOLD)
        return canvas.convert("RGB")

    # CTA — price restated, less clutter (no URL hero)
    local = (t - 12.4) / 3.6
    zoom = 1.0 + 0.03 * local
    canvas = dark_bg(assets["finale"], glow=(25, 40, 50), zoom=zoom, brightness=0.30, pan=0.4)
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 120))
    canvas.alpha_composite(veil)
    logo = fit_contain(assets["logo"], 120, 120)
    canvas.alpha_composite(logo, ((W - logo.width) // 2, 80))
    pill(canvas, 280, "BLACK FRIDAY", size=36)
    d = ImageDraw.Draw(canvas)
    a = ease_out(min(1.0, local / 0.3))
    if a > 0.05:
        draw_text(d, (W // 2, 420), COPY["cta_product"], size=46, fill=WHITE)
        draw_text(d, (W // 2, 560), "₪758", size=150, fill=WHITE, rtl=False, stroke=2)
        draw_text(d, (W // 2, 700), COPY["save_line"], size=38, fill=SOFT_GOLD)
        draw_text(d, (W // 2, 820), COPY["cta_urgency"], size=48, fill=GOLD)
        draw_text(d, (W // 2, 960), COPY["cta_action"], size=50, fill=WHITE)
    return canvas.convert("RGB")


def make_audio(path: Path) -> None:
    """Warm cinematic-retail BF bed @108 BPM — soft kick, bass, pad, muted pluck.
    No piercing sine hits / raw noise. Expert audio_spec (Composer + Grok).
    """
    sr = 44100
    n = int(sr * DUR)
    t = np.linspace(0, DUR, n, endpoint=False)
    rng = np.random.default_rng(42)
    bpm = 108.0
    beat = 60.0 / bpm

    def adsr(length, a=0.01, d=0.08, s=0.7, r=0.2):
        a_n = max(1, int(a * length))
        d_n = max(1, int(d * length))
        r_n = max(1, int(r * length))
        s_n = max(0, length - a_n - d_n - r_n)
        e = np.concatenate(
            [
                np.linspace(0, 1, a_n),
                np.linspace(1, s, d_n),
                np.full(s_n, s),
                np.linspace(s, 0, r_n),
            ]
        )
        return e[:length]

    # Soft 808-ish kick (low only)
    kick = np.zeros(n)
    for i, bt in enumerate(np.arange(0, DUR, beat)):
        i0 = int(bt * sr)
        length = int(0.24 * sr)
        if i0 + length > n:
            break
        tt = np.arange(length) / sr
        freq = 88 * np.exp(-16 * tt) + 38
        k = np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-8.5 * tt)
        amp = 0.26 if (i % 2 == 0) else 0.16
        kick[i0 : i0 + length] += amp * k

    # Warm D-minor-ish bass (D2=73.4, A=110, F=87.3, C=65.4)
    bass_notes = [73.42, 73.42, 87.31, 65.41]
    bass = np.zeros(n)
    bar = 4 * beat
    for bi, start in enumerate(np.arange(0, DUR, bar)):
        note = bass_notes[bi % len(bass_notes)]
        i0 = int(start * sr)
        length = int(bar * sr * 0.9)
        if i0 >= n:
            break
        length = min(length, n - i0)
        tt = np.arange(length) / sr
        wave_b = (
            0.6 * np.sin(2 * np.pi * note * tt)
            + 0.22 * np.sin(2 * np.pi * note * 2 * tt)
            + 0.08 * np.sin(2 * np.pi * note * 3 * tt)
        )
        pulse = 0.7 + 0.3 * (0.5 + 0.5 * np.sin(2 * np.pi * (bpm / 60) * tt - 0.4))
        bass[i0 : i0 + length] += 0.15 * wave_b * pulse * adsr(length, 0.04, 0.1, 0.85, 0.12)

    # Airy pad (D minor triad+7): D F A C — kept dark
    pad = np.zeros(n)
    for f in (146.83, 174.61, 220.0, 261.63):
        det = 1 + 0.0025 * rng.standard_normal()
        pad += np.sin(2 * np.pi * f * det * t)
        pad += 0.35 * np.sin(2 * np.pi * f * 0.5 * det * t)
    pad /= 5.2
    pad *= 0.085 * (0.78 + 0.22 * np.sin(2 * np.pi * 0.11 * t))
    pad = np.convolve(pad, np.ones(51) / 51, mode="same")
    # sidechain duck under kick grid
    duck = 1.0 - 0.18 * np.maximum(0, np.sin(2 * np.pi * (bpm / 60) * t))
    pad *= duck

    # Sparse muted plucks (cutoff-ish via few harmonics)
    melody = [
        (0.5, 293.66, 0.4),
        (2.0, 349.23, 0.35),
        (3.5, 261.63, 0.4),
        (5.0, 293.66, 0.35),
        (6.5, 392.0, 0.4),
        (8.0, 349.23, 0.35),
        (9.5, 440.0, 0.35),
        (11.0, 349.23, 0.4),
        (12.5, 293.66, 0.5),
        (14.0, 261.63, 0.55),
    ]
    pluck = np.zeros(n)
    for st, freq, length_s in melody:
        i0 = int(st * sr)
        length = int(length_s * sr)
        if i0 >= n:
            continue
        length = min(length, n - i0)
        tt = np.arange(length) / sr
        tone = np.sin(2 * np.pi * freq * tt) * np.exp(-2.6 * tt)
        tone += 0.2 * np.sin(2 * np.pi * freq * 2 * tt) * np.exp(-5.5 * tt)
        pluck[i0 : i0 + length] += 0.09 * tone

    # Soft whooshes + low thumps only on key cuts (hook/price/CTA)
    whoosh = np.zeros(n)
    hits = np.zeros(n)
    for wt, amp in ((0.04, 0.18), (4.0, 0.28), (12.4, 0.24)):
        i0 = int(wt * sr)
        length = int(0.32 * sr)
        if i0 >= n:
            continue
        length = min(length, n - i0)
        noise = rng.standard_normal(length)
        noise = np.convolve(noise, np.ones(140) / 140, mode="same")
        env = np.sin(np.linspace(0, np.pi, length)) ** 1.6
        whoosh[i0 : i0 + length] += 0.035 * noise * env
        tt = np.arange(length) / sr
        freq = 62 * np.exp(-11 * tt) + 32
        hits[i0 : i0 + length] += amp * np.sin(2 * np.pi * np.cumsum(freq) / sr) * np.exp(-6.5 * tt)

    # Light shaker on offbeats (very soft)
    shaker = np.zeros(n)
    for i, bt in enumerate(np.arange(beat / 2, DUR, beat)):
        i0 = int(bt * sr)
        length = int(0.04 * sr)
        if i0 + length > n:
            break
        burst = rng.standard_normal(length) * np.linspace(1, 0, length)
        burst = np.convolve(burst, np.ones(9) / 9, mode="same")
        shaker[i0 : i0 + length] += 0.018 * burst

    bed = kick + bass + pad + pluck + whoosh + hits + shaker
    # near-silence under first ~0.35s of hook text
    quiet = int(0.35 * sr)
    bed[:quiet] *= np.linspace(0.15, 1.0, quiet)

    peak = np.max(np.abs(bed)) + 1e-9
    bed = bed / peak * 0.70
    bed = np.tanh(bed * 1.1) * 0.88
    # gentle high shelf cut above ~6k via heavy smooth (darker phone mix)
    bed = np.convolve(bed, np.ones(7) / 7, mode="same")

    fade_in = int(0.2 * sr)
    fade_out = int(0.6 * sr)
    bed[:fade_in] *= np.linspace(0, 1, fade_in)
    bed[-fade_out:] *= np.linspace(1, 0, fade_out)

    audio = np.clip(bed, -1, 1)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<h", int(x * 30000)) for x in audio))


def render() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    frames = OUT / "frames"
    if frames.exists():
        shutil.rmtree(frames)
    frames.mkdir()

    product = soft_product(load_rgba(ASSETS / "rogaine-double-man.png"))
    assets = {
        "product": product,
        "logo": load_rgba(ASSETS / "main-logo.png"),
        "hero": load_rgba(ASSETS / "hero-life.png"),
        "journey": load_rgba(ASSETS / "journey-growth.jpg"),
        "finale": load_rgba(ASSETS / "finale-rogaine.jpg"),
    }

    print(f"Rendering {N} frames…")
    for i in range(N):
        im = frame_at(i, assets)
        im.save(frames / f"f_{i:05d}.png")
        if i % 60 == 0:
            print(f"  {i}/{N}")

    audio = OUT / "audio.wav"
    make_audio(audio)

    mp4 = OUT / "MinoxShop_BF_mirror_reel_16s.mp4"
    cmd = [
        "ffmpeg",
        "-y",
        "-framerate",
        str(FPS),
        "-i",
        str(frames / "f_%05d.png"),
        "-i",
        str(audio),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(mp4),
    ]
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    cover = frame_at(int(6.5 * FPS), assets)
    cover_path = OUT / "MinoxShop_BF_mirror_COVER.jpg"
    cover.save(cover_path, quality=95)

    ART.mkdir(parents=True, exist_ok=True)
    shutil.copy2(mp4, ART / "DOWNLOAD_MinoxShop_BF_mirror_reel_16s.mp4")
    shutil.copy2(cover_path, ART / "DOWNLOAD_MinoxShop_BF_mirror_COVER.jpg")
    shutil.copy2(mp4, ART / "bf_mirror_text_fix_demo.mp4")
    shutil.copy2(cover_path, ART / "bf_mirror_text_fix_cover.jpg")

    print("Wrote", mp4)
    print("Wrote", cover_path)
    return mp4


if __name__ == "__main__":
    render()
