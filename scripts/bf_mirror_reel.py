#!/usr/bin/env python3
"""MinoxShop Black Friday mirror reel — 16s 1080x1920.

Fixes: mixed Hebrew/Latin font (Arimo), RTL via libraqm, fuller natural copy.
Assets: MINOX_ASSETS env or /tmp/minox-mp
"""

from __future__ import annotations

import math
import os
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H, FPS, DUR = 1080, 1920, 30, 16
N = FPS * DUR

ASSETS = Path(os.environ.get("MINOX_ASSETS", "/tmp/minox-mp"))
OUT = Path(os.environ.get("BF_OUT", "/tmp/bf-mirror-reel-v2"))
ART = Path("/opt/cursor/artifacts")

FONT = "/usr/share/fonts/truetype/croscore/Arimo-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/croscore/Arimo-Regular.ttf"

# Synthesized from multi-model Hebrew copy (Grok + Composer), expanded for screen story.
COPY = {
    # Keep Latin brands on their own LTR lines so RTL doesn't flip word order.
    # Final lines blend Grok/Composer variants + late Grok punch-ups.
    "hook": "BLACK FRIDAY",
    "hook_mid": "Rogaine מארז כפול",
    "hook_sub": "במחיר שלא חוזר",
    "before_tag": "היה",
    "before_note": "מחיר מלא",
    "now_tag": "עכשיו רק",
    "save_line": "חוסכים ₪240 על המארז",
    "chip1": "מקורי מארה״ב",
    "chip2": "מארז כפול לשישה חודשים",
    "chip3": "קצף 5% לגברים",
    "chip4": "משלוח מהיר עד הבית",
    "cta_product": "Rogaine קצף 5% · מארז כפול",
    "cta_urgency": "המחיר הזה עד סוף השבוע",
    "cta_action": "הקישור בפרופיל",
    "cta_brand": "MinoxShop",
    "site": "minox-shop.co.il",
}

TEAL = (64, 224, 208)
RED = (220, 40, 50)
WHITE = (255, 255, 255)
MUTED = (180, 185, 195)
GOLD = (255, 210, 120)


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


def fit_cover(im: Image.Image, tw: int, th: int) -> Image.Image:
    scale = max(tw / im.width, th / im.height)
    nw, nh = int(im.width * scale), int(im.height * scale)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - tw) // 2
    y = (nh - th) // 2
    return im.crop((x, y, x + tw, y + th))


def fit_contain(im: Image.Image, tw: int, th: int) -> Image.Image:
    scale = min(tw / im.width, th / im.height)
    nw, nh = max(1, int(im.width * scale)), max(1, int(im.height * scale))
    return im.resize((nw, nh), Image.Resampling.LANCZOS)


def dark_bg(base: Image.Image | None = None, glow: tuple[int, int, int] = (20, 60, 70)) -> Image.Image:
    canvas = Image.new("RGBA", (W, H), (12, 14, 18, 255))
    if base is not None:
        bg = fit_cover(base.convert("RGBA"), W, H)
        bg = ImageEnhance.Brightness(bg).enhance(0.28)
        bg = ImageEnhance.Color(bg).enhance(0.55)
        bg = bg.filter(ImageFilter.GaussianBlur(18))
        canvas = Image.alpha_composite(canvas, bg)
    # soft center glow
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    cx, cy = W // 2, int(H * 0.42)
    for r, a in ((520, 55), (360, 80), (220, 100)):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*glow, a))
    overlay = overlay.filter(ImageFilter.GaussianBlur(40))
    return Image.alpha_composite(canvas, overlay)


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
    """Draw mixed Hebrew/Latin safely with Arimo + libraqm RTL when needed."""
    f = font(size, bold=bold)
    kwargs = dict(font=f, fill=fill, anchor=anchor)
    if stroke:
        kwargs["stroke_width"] = stroke
        kwargs["stroke_fill"] = stroke_fill
    # Hebrew-primary lines use RTL; pure ASCII/prices stay default.
    has_he = any("\u0590" <= ch <= "\u05FF" for ch in text)
    if rtl and has_he:
        kwargs["direction"] = "rtl"
        kwargs["language"] = "he"
    draw.text(xy, text, **kwargs)


def pill(
    canvas: Image.Image,
    cy: int,
    text: str,
    *,
    fill=(200, 30, 40, 235),
    text_fill=WHITE,
    size: int = 42,
    pad_x: int = 36,
    pad_y: int = 16,
) -> None:
    f = font(size)
    tmp = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    bbox = td.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pw, ph = tw + pad_x * 2, th + pad_y * 2
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0 = (W - pw) // 2
    y0 = cy - ph // 2
    d.rounded_rectangle((x0, y0, x0 + pw, y0 + ph), radius=ph // 2, fill=fill)
    draw_text(d, (W // 2, cy), text, size=size, fill=text_fill, rtl=False)
    canvas.alpha_composite(layer)


def chip(
    canvas: Image.Image,
    cy: int,
    text: str,
    *,
    size: int = 44,
    fill=(255, 255, 255, 235),
    text_fill=(18, 20, 24),
) -> None:
    f = font(size)
    bbox = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox(
        (0, 0), text, font=f, direction="rtl", language="he"
    )
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pw, ph = tw + 48, th + 28
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x0 = (W - pw) // 2
    y0 = cy - ph // 2
    d.rounded_rectangle((x0, y0, x0 + pw, y0 + ph), radius=22, fill=fill)
    draw_text(d, (W // 2, cy), text, size=size, fill=text_fill, rtl=True)
    canvas.alpha_composite(layer)


def paste_center(canvas: Image.Image, im: Image.Image, cy: int, max_w: int, max_h: int, scale: float = 1.0) -> None:
    im = fit_contain(im, int(max_w * scale), int(max_h * scale))
    x = (W - im.width) // 2
    y = cy - im.height // 2
    canvas.alpha_composite(im, (x, y))


def shadow_text(draw, xy, text, **kwargs):
    x, y = xy
    shadow_kwargs = dict(kwargs)
    shadow_kwargs["fill"] = (0, 0, 0)
    shadow_kwargs["stroke"] = 0
    draw_text(draw, (x + 3, y + 4), text, **shadow_kwargs)
    draw_text(draw, xy, text, **kwargs)


def frame_at(i: int, assets: dict) -> Image.Image:
    t = i / FPS
    # --- scene timing ---
    # 0.0-2.8 hook | 2.8-5.5 before | 5.5-9.2 price | 9.2-12.8 chips | 12.8-16 cta

    if t < 2.8:
        # HOOK — thinning scalp + punchy BF line (keep face readable)
        canvas = Image.new("RGBA", (W, H), (8, 8, 10, 255))
        bg = fit_cover(assets["journey"].convert("RGBA"), W, H)
        bg = ImageEnhance.Brightness(bg).enhance(0.72)
        bg = ImageEnhance.Contrast(bg).enhance(1.15)
        # bottom gradient for text
        grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(grad)
        for y in range(int(H * 0.55), H):
            a_g = int(220 * ((y - H * 0.55) / (H * 0.45)))
            gd.line((0, y, W, y), fill=(0, 0, 0, min(230, a_g)))
        canvas = Image.alpha_composite(canvas, bg)
        canvas = Image.alpha_composite(canvas, grad)
        d = ImageDraw.Draw(canvas)
        a = ease_out(t / 0.55)
        y0 = int(H * 0.68 + (1 - a) * 36)
        y1 = int(H * 0.76 + (1 - a) * 40)
        y2 = int(H * 0.84 + (1 - a) * 50)
        if a > 0.05:
            shadow_text(d, (W // 2, y0), COPY["hook"], size=52, fill=RED, stroke=2, rtl=False)
            shadow_text(d, (W // 2, y1), COPY["hook_mid"], size=56, fill=WHITE, stroke=2)
            shadow_text(d, (W // 2, y2), COPY["hook_sub"], size=42, fill=TEAL, stroke=1)
        return canvas.convert("RGB")

    if t < 5.5:
        # BEFORE PRICE smash setup
        local = (t - 2.8) / 2.7
        canvas = dark_bg(assets["hero"], glow=(50, 20, 30))
        d = ImageDraw.Draw(canvas)
        a = ease_out(min(1.0, local / 0.35))
        # shake near end
        shake = 0
        if local > 0.75:
            shake = int(10 * math.sin(local * 60))
        if a > 0.05:
            draw_text(d, (W // 2 + shake, int(H * 0.38)), COPY["before_note"], size=46, fill=GOLD)
            draw_text(d, (W // 2 + shake, int(H * 0.48)), COPY["before_tag"], size=56, fill=MUTED)
            draw_text(
                d,
                (W // 2 + shake, int(H * 0.58)),
                "₪998",
                size=140,
                fill=WHITE,
                rtl=False,
                stroke=3,
            )
            if local > 0.82:
                # red X
                layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ld = ImageDraw.Draw(layer)
                cx, cy = W // 2, int(H * 0.58)
                s = 110
                ld.line((cx - s, cy - s, cx + s, cy + s), fill=(*RED, 230), width=18)
                ld.line((cx - s, cy + s, cx + s, cy - s), fill=(*RED, 230), width=18)
                canvas.alpha_composite(layer)
        return canvas.convert("RGB")

    if t < 9.2:
        # PRICE REVEAL
        local = (t - 5.5) / 3.7
        canvas = dark_bg(None, glow=(20, 70, 75))
        pop = 0.85 + 0.15 * ease_out(min(1.0, local / 0.4))
        paste_center(canvas, assets["product"], int(H * 0.38), 820, 700, scale=pop)
        pill(canvas, int(H * 0.14), "BLACK FRIDAY", size=40)
        d = ImageDraw.Draw(canvas)
        a = ease_out(min(1.0, max(0.0, (local - 0.25) / 0.35)))
        if a > 0.05:
            draw_text(d, (W // 2, int(H * 0.62)), COPY["now_tag"], size=44, fill=TEAL)
            draw_text(d, (W // 2, int(H * 0.72)), "₪758", size=150, fill=WHITE, rtl=False, stroke=3)
            # struck old
            ox, oy = W // 2, int(H * 0.82)
            draw_text(d, (ox, oy), "₪998", size=52, fill=MUTED, rtl=False)
            bb = d.textbbox((ox, oy), "₪998", font=font(52), anchor="mm")
            d.line((bb[0] - 8, (bb[1] + bb[3]) // 2, bb[2] + 8, (bb[1] + bb[3]) // 2), fill=RED, width=5)
            draw_text(d, (W // 2, int(H * 0.90)), COPY["save_line"], size=42, fill=TEAL)
        # logo corner
        logo = fit_contain(assets["logo"], 120, 120)
        canvas.alpha_composite(logo, (W - 150, 40))
        return canvas.convert("RGB")

    if t < 12.8:
        # TRUST CHIPS — fuller copy
        local = (t - 9.2) / 3.6
        canvas = dark_bg(None, glow=(25, 55, 65))
        paste_center(canvas, assets["product"], int(H * 0.30), 720, 560, scale=0.95)
        logo = fit_contain(assets["logo"], 110, 110)
        canvas.alpha_composite(logo, (W - 140, 36))
        chips = [COPY["chip1"], COPY["chip2"], COPY["chip3"], COPY["chip4"]]
        # stagger reveal
        base_y = int(H * 0.58)
        for idx, text in enumerate(chips):
            appear = ease_out(min(1.0, max(0.0, (local - idx * 0.14) / 0.28)))
            if appear <= 0.05:
                continue
            cy = base_y + idx * 95 + int((1 - appear) * 24)
            chip(canvas, cy, text, size=40 if idx != 1 else 36)
        return canvas.convert("RGB")

    # CTA
    local = (t - 12.8) / 3.2
    canvas = dark_bg(assets["finale"], glow=(20, 50, 60))
    # darken for readability
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 110))
    canvas.alpha_composite(veil)
    logo = fit_contain(assets["logo"], 130, 130)
    canvas.alpha_composite(logo, ((W - logo.width) // 2, 70))
    pill(canvas, 280, "BLACK FRIDAY", size=38)
    d = ImageDraw.Draw(canvas)
    a = ease_out(min(1.0, local / 0.35))
    if a > 0.05:
        draw_text(d, (W // 2, 400), COPY["cta_product"], size=48, fill=WHITE)
        draw_text(d, (W // 2, 540), "₪758", size=140, fill=WHITE, rtl=False, stroke=3)
        draw_text(d, (W // 2, 680), COPY["cta_urgency"], size=48, fill=GOLD)
        draw_text(d, (W // 2, 800), COPY["cta_action"], size=46, fill=WHITE)
        draw_text(d, (W // 2, 900), COPY["cta_brand"], size=44, fill=WHITE, rtl=False)
        draw_text(d, (W // 2, 1020), COPY["site"], size=40, fill=TEAL, rtl=False)
        draw_text(d, (W // 2, 1140), COPY["save_line"], size=36, fill=MUTED)
    return canvas.convert("RGB")


def make_audio(path: Path) -> None:
    """Simple BF bed: soft pulse + hits on beat changes."""
    sr = 44100
    n = int(sr * DUR)
    t = np.linspace(0, DUR, n, endpoint=False)
    # warm low pulse
    bed = 0.12 * np.sin(2 * np.pi * 55 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 1.5 * t))
    bed += 0.04 * np.sin(2 * np.pi * 110 * t)
    # soft noise texture
    rng = np.random.default_rng(7)
    bed += 0.015 * rng.standard_normal(n)
    # hits at scene starts
    for hit_t, amp in ((0.05, 0.35), (2.8, 0.4), (5.5, 0.55), (9.2, 0.3), (12.8, 0.45)):
        i0 = int(hit_t * sr)
        env = np.exp(-np.linspace(0, 18, int(0.18 * sr)))
        tone = amp * np.sin(2 * np.pi * 180 * np.arange(len(env)) / sr) * env
        tone += 0.5 * amp * np.sin(2 * np.pi * 90 * np.arange(len(env)) / sr) * env
        i1 = min(n, i0 + len(tone))
        bed[i0:i1] += tone[: i1 - i0]
    # fade out
    fade = int(0.4 * sr)
    bed[-fade:] *= np.linspace(1, 0, fade)
    audio = np.clip(bed, -1, 1)
    # write wav
    import wave
    import struct

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

    assets = {
        "product": load_rgba(ASSETS / "rogaine-double-man.png"),
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
        "128k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(mp4),
    ]
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # cover = mid price frame
    cover = frame_at(int(7.2 * FPS), assets)
    cover_path = OUT / "MinoxShop_BF_mirror_COVER.jpg"
    cover.save(cover_path, quality=95)

    ART.mkdir(parents=True, exist_ok=True)
    art_mp4 = ART / "DOWNLOAD_MinoxShop_BF_mirror_reel_16s.mp4"
    art_cover = ART / "DOWNLOAD_MinoxShop_BF_mirror_COVER.jpg"
    shutil.copy2(mp4, art_mp4)
    shutil.copy2(cover_path, art_cover)
    # also demo copies for walkthrough skill naming
    shutil.copy2(mp4, ART / "bf_mirror_text_fix_demo.mp4")
    shutil.copy2(cover_path, ART / "bf_mirror_text_fix_cover.jpg")

    print("Wrote", mp4)
    print("Wrote", cover_path)
    return mp4


if __name__ == "__main__":
    render()
