#!/usr/bin/env python3
"""MinoxShop MONSTER offer-close v3 — REAL-BOX ANSWER.

Day-2 after scare reel: hard cuts on real Kirkland photos, spoken Hebrew,
price on the product — no black title card, no white catalog card, no AI.
~11s 9:16 silent for CapCut music.
"""
from __future__ import annotations

import math
import shutil
import subprocess
import wave
from array import array
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path("/tmp/monster-trust-v3")
ASSETS = ROOT / "assets"
FRAMES = ROOT / "frames"
PLATES = Path("/tmp/monster-v3-plates")
EXPORTS = Path("/agent/repos/barbero-shop/exports")
ARTIFACTS = Path("/opt/cursor/artifacts")
for p in (FRAMES, ASSETS, EXPORTS, ARTIFACTS):
    p.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1920
FPS = 30
DURATION = 11.0
N = int(DURATION * FPS)

INK = (9, 9, 9)
IVORY = (248, 246, 240)
GOLD = (198, 161, 91)
GOLD_SOFT = (228, 210, 162)
MUTED = (168, 162, 150)
NAVY = (8, 12, 22)

# DejaVu has Hebrew + Latin punctuation (NotoSansHebrew tofus periods/middots).
FONT_HE_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_HE_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_LAT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size: int, bold: bool = True, he: bool = True):
    if he:
        return ImageFont.truetype(FONT_HE_B if bold else FONT_HE_R, size)
    return ImageFont.truetype(FONT_LAT_B, size)


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 0.5 * (1 - math.cos(math.pi * t))


def ease_out_back(t: float) -> float:
    t = max(0.0, min(1.0, t))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def line_u(t: float, start: float, end: float, fi: float = 0.18, fo: float = 0.18) -> float:
    if t < start or t > end:
        return 0.0
    u = 1.0
    if t < start + fi:
        u = ease_out((t - start) / fi)
    if t > end - fo:
        u *= max(0.0, 1.0 - (t - (end - fo)) / fo)
    return u


def is_latin_glyph(ch: str) -> bool:
    """Only ASCII letters/digits/currency need Latin path — keep HE punctuation in HE runs."""
    o = ord(ch)
    if ch in "₪$€£":
        return True
    if 48 <= o <= 57 or 65 <= o <= 90 or 97 <= o <= 122:
        return True
    return False


def text_bb(draw, text, fnt, language=None):
    kw = {"language": language} if language else {}
    bb = draw.textbbox((0, 0), text, font=fnt, **kw)
    return bb[2] - bb[0], bb[3] - bb[1], bb


def measure_mixed(draw, text: str, size: int, bold: bool = True):
    f_he = font(size, bold, True)
    f_lat = font(size, bold, False)
    total = 0
    i = 0
    while i < len(text):
        lat = is_latin_glyph(text[i])
        j = i + 1
        while j < len(text) and is_latin_glyph(text[j]) == lat:
            j += 1
        chunk = text[i:j]
        fnt = f_lat if lat else f_he
        tw, _, _ = text_bb(draw, chunk, fnt, None if lat else "he")
        total += tw
        i = j
    _, th, _ = text_bb(draw, "א", f_he, "he")
    return total, th


def draw_mixed_at(layer, text: str, x_left: int, y: int, size: int, fill, alpha: int = 255, bold: bool = True):
    d = ImageDraw.Draw(layer)
    f_he = font(size, bold, True)
    f_lat = font(size, bold, False)
    runs = []
    i = 0
    while i < len(text):
        lat = is_latin_glyph(text[i])
        j = i + 1
        while j < len(text) and is_latin_glyph(text[j]) == lat:
            j += 1
        runs.append((text[i:j], lat))
        i = j
    x = x_left
    for chunk, lat in reversed(runs):
        fnt = f_lat if lat else f_he
        tw, th, bb = text_bb(d, chunk, fnt, None if lat else "he")
        color = (*fill, alpha) if len(fill) == 3 else fill
        xy = (x - bb[0], y - bb[1])
        if lat:
            d.text(xy, chunk, font=fnt, fill=color)
        else:
            d.text(xy, chunk, font=fnt, fill=color, language="he")
        x += tw


def draw_mixed_centered(layer, text: str, y: int, size: int, fill, alpha: int = 255, bold: bool = True):
    d = ImageDraw.Draw(layer)
    tw, _ = measure_mixed(d, text, size, bold)
    draw_mixed_at(layer, text, (W - tw) // 2, y, size, fill, alpha, bold)


def load_rgba(path: Path) -> Image.Image:
    return Image.open(path).convert("RGBA")


def stage_bg(warm: float = 0.0) -> Image.Image:
    """Dark premium stage — subtle radial, not flat void."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, H * 0.42
    r = np.sqrt(((xx - cx) / (W * 0.55)) ** 2 + ((yy - cy) / (H * 0.48)) ** 2)
    glow = np.clip(1.0 - r, 0, 1) ** 1.6
    base = np.zeros((H, W, 3), dtype=np.float32)
    base[:, :, 0] = 7 + 18 * glow + 10 * warm * glow
    base[:, :, 1] = 9 + 22 * glow + 6 * warm * glow
    base[:, :, 2] = 16 + 34 * glow
    # soft top vignette
    top = np.clip((yy / H - 0.08) / 0.2, 0, 1)
    base *= (0.72 + 0.28 * top)[:, :, None]
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


def load_logo() -> Image.Image | None:
    for p in (PLATES / "logo.png", Path("/tmp/minox-brand/main-logo.png"), Path("/tmp/two-boxes-v4/assets/main-logo.png")):
        if p.exists():
            logo = load_rgba(p)
            logo.thumbnail((260, 110), Image.Resampling.LANCZOS)
            return logo
    return None


def prep_plate(name: str) -> Image.Image:
    return load_rgba(PLATES / name)


LOGO = load_logo()
DOUBLE = prep_plate("pack_trim.png")  # proven two-box hero from two-boxes v4
PACK = prep_plate("pack_trim.png")
KIT = prep_plate("kit_studio.png")  # vendor packshot kept as studio plate (no jagged key)
LABEL = prep_plate("label_crop.png")
BOX = prep_plate("box_clean.png")
BOTTLE = prep_plate("bottle_crop.png")
SINGLE = prep_plate("box_clean.png")


def apply_logo(im: Image.Image, alpha: float, y: int = 58):
    if LOGO is None or alpha < 0.04:
        return
    logo = LOGO.copy()
    logo.putalpha(logo.split()[-1].point(lambda a: int(a * alpha)))
    im.alpha_composite(logo, ((W - logo.size[0]) // 2, y))


def caption(im, text, y, size, fill, u, bold: bool = True):
    if u < 0.04:
        return
    a = int(255 * min(1.0, u * 1.25))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_mixed_centered(shadow, text, y + 3, size, (0, 0, 0), int(a * 0.65), bold)
    shadow = shadow.filter(ImageFilter.GaussianBlur(5))
    im.alpha_composite(shadow)
    # soft dark bar behind text for readability on product
    dprobe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tw, th = measure_mixed(dprobe, text, size, bold)
    bar = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bar)
    pad_x, pad_y = 36, 18
    x0 = (W - tw) // 2 - pad_x
    y0 = y - pad_y
    bd.rounded_rectangle([x0, y0, x0 + tw + 2 * pad_x, y0 + th + 2 * pad_y], 18, fill=(6, 8, 14, int(150 * u)))
    im.alpha_composite(bar)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_mixed_centered(layer, text, y, size, fill, a, bold)
    im.alpha_composite(layer)


def place_hero(im: Image.Image, src: Image.Image, max_w: int, y_center: int, zoom: float = 1.0, alpha: float = 1.0, shadow: bool = True):
    if alpha < 0.02:
        return
    p = src.copy()
    p.thumbnail((int(max_w * zoom), int(max_w * zoom * 1.15)), Image.Resampling.LANCZOS)
    p = ImageEnhance.Contrast(p).enhance(1.03)
    p = ImageEnhance.Sharpness(p).enhance(1.06)
    pw, ph = p.size
    px = (W - pw) // 2
    py = int(y_center - ph / 2)
    if shadow:
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sh)
        sd.ellipse(
            [px + int(pw * 0.12), py + ph - 18, px + int(pw * 0.88), py + ph + 36],
            fill=(0, 0, 0, int(110 * alpha)),
        )
        sh = sh.filter(ImageFilter.GaussianBlur(22))
        im.alpha_composite(sh)
    if alpha < 0.99:
        p = p.copy()
        p.putalpha(p.split()[-1].point(lambda a: int(a * alpha)))
    im.alpha_composite(p, (px, py))


def place_studio_plate(im: Image.Image, src: Image.Image, zoom: float = 1.0):
    """Edge-to-edge studio packshot — white floor becomes the scene, not a floating card."""
    p = src.convert("RGB")
    # cover full width; bias crop toward product
    scale = max(W / p.size[0], (H * 0.62) / p.size[1]) * zoom
    nw, nh = int(p.size[0] * scale), int(p.size[1] * scale)
    p = p.resize((nw, nh), Image.Resampling.LANCZOS)
    x0 = (nw - W) // 2
    y0 = max(0, int((nh - int(H * 0.62)) * 0.15))
    crop = p.crop((x0, y0, x0 + W, y0 + int(H * 0.62)))
    # soft fade into dark stage at bottom of plate
    arr = np.asarray(crop).astype(np.float32)
    fade = np.linspace(0, 1, arr.shape[0], dtype=np.float32)[:, None, None]
    fade = np.clip((fade - 0.78) / 0.22, 0, 1)
    dark = np.array(NAVY, dtype=np.float32)
    arr = arr * (1 - fade) + dark * fade
    plate = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    im.alpha_composite(plate, (0, int(H * 0.12)))


def price_on_photo(im, u: float, strike_u: float = 1.0):
    if u < 0.05:
        return
    a = int(255 * min(1.0, u * 1.2))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # frosted panel
    panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle([90, 1180, W - 90, 1460], 28, fill=(8, 10, 16, int(175 * u)))
    pd.rounded_rectangle([90, 1180, W - 90, 1460], 28, outline=(*GOLD, int(70 * u)), width=2)
    im.alpha_composite(panel)
    draw_mixed_centered(layer, "₪1050", 1210, 36, MUTED, int(a * 0.9), True)
    d = ImageDraw.Draw(layer)
    tw, _ = measure_mixed(d, "₪1050", 36, True)
    x0 = (W - tw) // 2
    sw = max(0.0, min(1.0, strike_u))
    d.line([(x0, 1230), (x0 + int(tw * sw), 1230)], fill=(*MUTED, a), width=3)
    pop = 0.90 + 0.10 * ease_out_back(min(1.0, u))
    draw_mixed_centered(layer, "₪765", 1270, int(92 * pop), GOLD, a, True)
    draw_mixed_centered(layer, "שתי קופסאות לשנה שלמה", 1385, 34, IVORY, a, True)
    im.alpha_composite(layer)


def cta_block(im, u: float, t: float = 0.0):
    if u < 0.05:
        return
    a = int(255 * min(1.0, u * 1.2))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bw, bh = 820, 100
    y0 = 1520
    pulse = 1.0 + 0.025 * (0.5 + 0.5 * math.sin((t - 8.6) * 2 * math.pi / 0.85))
    enter = 0.94 + 0.06 * ease_out_back(min(1.0, u))
    scale = enter * pulse
    bw2, bh2 = int(bw * scale), int(bh * scale)
    x0 = (W - bw2) // 2
    y0p = y0 - (bh2 - bh) // 2
    d.rounded_rectangle([x0, y0p, x0 + bw2, y0p + bh2], 24, fill=(*GOLD, a))
    draw_mixed_centered(layer, "הזמנה בוואטסאפ", y0p + 14, 40, INK, a, True)
    draw_mixed_centered(layer, "הקישור בפרופיל", y0p + bh2 + 22, 32, GOLD_SOFT, a, True)
    im.alpha_composite(layer)


# Beat windows (hard cuts)
# 0.0–1.8  double compose — bridge from Day-1
# 1.8–3.5  kit (box+bottle+dropper)
# 3.5–5.1  label crop
# 5.1–6.7  pack_trim / bottle variety
# 6.7–8.8  double + price
# 8.8–11   hold + CTA


def render_frame(i: int) -> Image.Image:
    t = i / FPS
    warm = 0.15 if t >= 6.7 else 0.0
    im = stage_bg(warm=warm)
    logo_a = min(1.0, t / 0.25) if t < DURATION - 0.15 else max(0.0, (DURATION - t) / 0.15)

    # Ken Burns helpers
    def kb(start, end, z0, z1):
        if t < start or t > end:
            return z0
        u = ease_in_out((t - start) / max(0.01, end - start))
        return z0 + (z1 - z0) * u

    if t < 1.8:
        z = kb(0.0, 1.8, 1.0, 1.10)
        place_hero(im, DOUBLE, 1000, 760, zoom=z)
        apply_logo(im, logo_a * 0.95)
        caption(im, "אתמול ראית לאן זה הולך", 1480, 42, IVORY, line_u(t, 0.15, 1.75, 0.22, 0.18))
        return im.convert("RGB")

    if t < 3.5:
        z = kb(1.8, 3.5, 1.0, 1.06)
        place_studio_plate(im, KIT, zoom=z)
        apply_logo(im, logo_a)
        caption(im, "היום הקופסאות האמיתיות", 1520, 42, IVORY, line_u(t, 1.9, 3.45, 0.2, 0.16))
        return im.convert("RGB")

    if t < 5.1:
        z = kb(3.5, 5.1, 1.04, 1.14)
        place_hero(im, LABEL, 1040, 700, zoom=z)
        apply_logo(im, logo_a)
        caption(im, "קירקלנד חמישה אחוז נוזל", 1480, 42, GOLD_SOFT, line_u(t, 3.6, 5.05, 0.2, 0.16))
        return im.convert("RGB")

    if t < 6.7:
        if t < 5.9:
            z = kb(5.1, 5.9, 1.0, 1.08)
            place_hero(im, PACK, 1000, 700, zoom=z)
            caption(im, "שתי קופסאות לשנה שלמה", 1480, 44, IVORY, line_u(t, 5.2, 5.85, 0.18, 0.14))
        else:
            z = kb(5.9, 6.7, 1.0, 1.09)
            place_hero(im, SINGLE, 780, 720, zoom=z)
            caption(im, "מקורי מארה״ב", 1480, 40, GOLD_SOFT, line_u(t, 6.0, 6.65, 0.16, 0.12))
        apply_logo(im, logo_a)
        return im.convert("RGB")

    # offer + CTA
    z = kb(6.7, 11.0, 1.0, 1.06)
    place_hero(im, DOUBLE, 920, 600, zoom=z)
    apply_logo(im, logo_a)
    strike = ease_out(min(1.0, max(0.0, (t - 6.9) / 0.28)))
    price_on_photo(im, line_u(t, 6.75, 11.0, 0.22, 0.08), strike_u=strike)
    if t >= 8.75:
        cta_block(im, line_u(t, 8.75, 11.0, 0.22, 0.1), t=t)
    else:
        caption(im, "במקום ₪1050 רק ₪765", 1600, 38, IVORY, line_u(t, 7.0, 8.7, 0.2, 0.15))
    return im.convert("RGB")


def write_silent_audio(path: Path, duration: float, sr: int = 44100):
    n = int(sr * duration)
    pcm = array("h", [0] * n)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def main():
    print(f"rendering monster offer-close v3 REAL-BOX {N} frames…")
    for f in FRAMES.glob("*.jpg"):
        f.unlink()
    cover = None
    # cover at ~7.4s — double + price visible
    cover_i = int(7.4 * FPS)
    for i in range(N):
        frame = render_frame(i)
        frame.save(FRAMES / f"f_{i:04d}.jpg", quality=93, subsampling=0)
        if i == cover_i:
            cover = frame.copy()
        if i % 30 == 0:
            print(f"  {i}/{N}")
    if cover is None:
        cover = Image.open(FRAMES / f"f_{cover_i:04d}.jpg")

    wav = ROOT / "audio.wav"
    write_silent_audio(wav, DURATION)

    mp4_name = "MinoxShop-MONSTER-offer-close-v3-11s.mp4"
    cover_name = "MinoxShop-MONSTER-offer-close-v3-COVER.jpg"
    out_mp4 = EXPORTS / mp4_name
    out_cover = EXPORTS / cover_name
    cover.save(out_cover, quality=94, subsampling=0)
    cover.save(ARTIFACTS / cover_name, quality=94, subsampling=0)

    pattern = str(FRAMES / "f_%04d.jpg")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", pattern,
        "-i", str(wav),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "fast",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest", "-movflags", "+faststart",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.copy(out_mp4, ARTIFACTS / mp4_name)
    # QA stills at beat cuts
    qa = ROOT / "qa"
    qa.mkdir(exist_ok=True)
    for label, sec in [("hook", 0.9), ("kit", 2.6), ("label", 4.2), ("year", 5.4), ("price", 7.4), ("cta", 9.5)]:
        shutil.copy(FRAMES / f"f_{int(sec * FPS):04d}.jpg", qa / f"{label}.jpg")
        shutil.copy(qa / f"{label}.jpg", ARTIFACTS / f"monster-v3-{label}.jpg")
    print("OK", out_mp4, out_mp4.stat().st_size)


if __name__ == "__main__":
    main()
