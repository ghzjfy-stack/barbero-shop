#!/usr/bin/env python3
"""MinoxShop CLOSE reel — double pack year offer → WA.

Short conversion closer after the feed post: hook → product+dropper →
clear ₪765 math → WhatsApp CTA. ~10.5s, 9:16.

Audio v2: ~96 BPM kick pulse, cut whooshes, price ding, louder master
for TikTok/Reels retention (same picture cut).
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

ROOT = Path("/tmp/close-reel-765")
ASSETS = ROOT / "assets"
FRAMES = ROOT / "frames"
EXPORTS = Path("/agent/repos/barbero-shop/exports")
ARTIFACTS = Path("/opt/cursor/artifacts")
for p in (FRAMES, ASSETS, EXPORTS, ARTIFACTS):
    p.mkdir(parents=True, exist_ok=True)

# Sources
LIQ = Path("/tmp/ig-ok/liq2048.png")
LOGO_CANDIDATES = [
    Path("/tmp/minox-brand/main-logo.png"),
    Path("/tmp/two-boxes-v4/assets/main-logo.png"),
    Path("/tmp/two-boxes-v2/assets/main-logo.png"),
]

W, H = 1080, 1920
FPS = 30
DURATION = 10.5
N = int(DURATION * FPS)

INK = (9, 9, 9)
IVORY = (244, 241, 234)
GOLD = (198, 161, 91)
GOLD_SOFT = (228, 210, 162)
MUTED = (163, 158, 147)
CARD = (252, 250, 247)

FONT_HE_B = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Bold.ttf"
FONT_HE_R = "/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf"
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


def line_u(t: float, start: float, end: float, fi: float = 0.22, fo: float = 0.25) -> float:
    if t < start or t > end:
        return 0.0
    u = 1.0
    if t < start + fi:
        u = ease_out((t - start) / fi)
    if t > end - fo:
        u *= max(0.0, 1.0 - (t - (end - fo)) / fo)
    return u


def is_latin_glyph(ch: str) -> bool:
    o = ord(ch)
    if ch in "?!.·|:;,/\\-+*=#%&@'\"₪$€£()[]{}<>—–":
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
    if alpha < 8:
        return 0
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
    widths = []
    for chunk, lat in reversed(runs):
        fnt = f_lat if lat else f_he
        tw, th, bb = text_bb(d, chunk, fnt, None if lat else "he")
        widths.append((chunk, lat, fnt, tw, th, bb))
    x = x_left
    a = int(max(0, min(255, alpha)))
    color = (*fill[:3], a)
    for chunk, lat, fnt, tw, th, bb in widths:
        xy = (x - bb[0], y - bb[1])
        if lat:
            d.text(xy, chunk, font=fnt, fill=color)
        else:
            d.text(xy, chunk, font=fnt, fill=color, language="he")
        x += tw
    return sum(w[3] for w in widths)


def draw_mixed_centered(layer, text: str, y: int, size: int, fill, alpha: int = 255, bold: bool = True):
    if alpha < 8:
        return
    d = ImageDraw.Draw(layer)
    tw, _ = measure_mixed(d, text, size, bold)
    draw_mixed_at(layer, text, (W - tw) // 2, y, size, fill, alpha, bold)


def bg(t: float = 0.0) -> Image.Image:
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - W * 0.88) / 780) ** 2 + ((yy + 60) / 520) ** 2)
    glow = np.clip(1 - r, 0, 1) ** 2 * (0.10 + 0.02 * math.sin(t * 1.4))
    base = np.array(INK, np.float32)
    gold = np.array(GOLD, np.float32)
    return Image.fromarray(
        np.clip(base + (gold - base) * glow[:, :, None], 0, 255).astype(np.uint8), "RGB"
    ).convert("RGBA")


def load_logo() -> Image.Image | None:
    for p in LOGO_CANDIDATES:
        if p.exists():
            logo = Image.open(p).convert("RGBA")
            a = np.asarray(logo).copy()
            rgb = a[:, :, :3].astype(np.float32)
            mn, mx = rgb.min(2), rgb.max(2)
            bgm = (mn > 195) & ((mx - mn) < 35) & (rgb.mean(2) > 215)
            a[:, :, 3] = np.where(bgm, 0, a[:, :, 3]).astype(np.uint8)
            logo = Image.fromarray(a, "RGBA")
            logo.thumbnail((110, 110), Image.Resampling.LANCZOS)
            return logo
    return None


def prep_product() -> Image.Image:
    """Keep studio white — place later on an ivory card (no jagged knockout)."""
    src = Image.open(LIQ).convert("RGBA")
    arr = np.asarray(src)
    rgb = arr[:, :, :3]
    mask = ~((rgb[:, :, 0] > 248) & (rgb[:, :, 1] > 248) & (rgb[:, :, 2] > 248))
    ys, xs = np.where(mask)
    pad = 56
    prod = src.crop(
        (
            max(0, xs.min() - pad),
            max(0, ys.min() - pad),
            min(src.size[0], xs.max() + pad),
            min(src.size[1], ys.max() + pad),
        )
    )
    # Fill any residual alpha holes with ivory so edges stay clean
    solid = Image.new("RGBA", prod.size, (*CARD, 255))
    solid.alpha_composite(prod)
    solid = ImageEnhance.Sharpness(solid).enhance(1.45)
    solid = ImageEnhance.Contrast(solid).enhance(1.06)
    return solid


LOGO = load_logo()
PROD = prep_product()


def place_product(im: Image.Image, max_w: int, y_center: int, pop: float, alpha: float = 1.0):
    if pop < 0.02 or alpha < 0.02:
        return
    p = PROD.copy()
    # Fit product into card with internal margin
    inner = max_w - 48
    p.thumbnail((inner, int(inner * 0.95)), Image.Resampling.LANCZOS)
    scale = 0.90 + 0.10 * ease_out_back(min(1.0, pop))
    pw = max(1, int(p.size[0] * scale))
    ph = max(1, int(p.size[1] * scale))
    pp = p.resize((pw, ph), Image.Resampling.LANCZOS)

    card_w = min(W - 80, pw + 56)
    card_h = ph + 48
    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    aa = pop * alpha
    cd.rounded_rectangle([0, 0, card_w - 1, card_h - 1], 22, fill=(*CARD, int(255 * aa)))
    cd.rounded_rectangle([1, 1, card_w - 2, card_h - 2], 21, outline=(*GOLD, int(50 * aa)), width=1)
    card.alpha_composite(pp, ((card_w - pw) // 2, (card_h - ph) // 2))
    # x2 badge — clarifies double pack while keeping dropper hero
    bw, bh = 92, 44
    badge = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    bd = ImageDraw.Draw(badge)
    bd.rounded_rectangle([0, 0, bw - 1, bh - 1], 10, fill=(9, 9, 9, int(240 * aa)), outline=(*GOLD, int(220 * aa)), width=2)
    bf = font(22, True, False)
    bb = bd.textbbox((0, 0), "x2", font=bf)
    bd.text(((bw - (bb[2] - bb[0])) // 2 - bb[0], (bh - (bb[3] - bb[1])) // 2 - bb[1] - 1), "x2", font=bf, fill=(*GOLD, int(255 * aa)))
    card.alpha_composite(badge, (16, 14))

    px = (W - card_w) // 2
    py = int(y_center - card_h / 2)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.ellipse(
        [px + 40, py + card_h - 12, px + card_w - 40, py + card_h + 28],
        fill=(0, 0, 0, int(80 * aa)),
    )
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    im.alpha_composite(sh)
    im.alpha_composite(card, (px, py))


def pill_caption(im, text, y, size, fill, u, pad=22):
    if u < 0.04:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    scale = 0.92 + 0.08 * ease_out_back(min(1.0, u * 1.3))
    sz = max(20, int(size * scale))
    tw, th = measure_mixed(d, text, sz, True)
    bw, bh = tw + pad * 2, th + int(pad * 0.85)
    x0 = (W - bw) // 2
    yy = y - int(16 * (1 - u))
    a = int(255 * min(1.0, u * 1.15))
    d.rounded_rectangle([x0, yy, x0 + bw, yy + bh], 20, fill=(0, 0, 0, int(a * 0.78)))
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_mixed_centered(tmp, text, yy + (bh - th) // 2, sz, fill, a, True)
    layer.alpha_composite(tmp)
    im.alpha_composite(layer)


def price_block(im, u: float):
    if u < 0.05:
        return
    a = int(255 * min(1.0, u * 1.2))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # strike
    draw_mixed_centered(layer, "₪1050", 1180, 34, MUTED, int(a * 0.85), True)
    # strike line
    d = ImageDraw.Draw(layer)
    tw, _ = measure_mixed(d, "₪1050", 34, True)
    x0 = (W - tw) // 2
    d.line([(x0, 1198), (x0 + tw, 1198)], fill=(*MUTED, a), width=3)
    # big price
    pop = 0.9 + 0.1 * ease_out_back(min(1.0, u))
    draw_mixed_centered(layer, "₪765", 1240, int(92 * pop), GOLD, a, True)
    draw_mixed_centered(layer, "₪64 לחודש  כולל משלוח", 1360, 34, IVORY, a, True)
    draw_mixed_centered(layer, "חיסכון ₪285", 1415, 30, GOLD_SOFT, a, True)
    im.alpha_composite(layer)


def cta_block(im, u: float):
    if u < 0.05:
        return
    a = int(255 * min(1.0, u * 1.2))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # gold CTA bar
    bw, bh = 780, 96
    x0, y0 = (W - bw) // 2, 1480
    scale = 0.94 + 0.06 * ease_out_back(min(1.0, u))
    bw2, bh2 = int(bw * scale), int(bh * scale)
    x0 = (W - bw2) // 2
    d.rounded_rectangle([x0, y0, x0 + bw2, y0 + bh2], 22, fill=(*GOLD, a))
    draw_mixed_centered(layer, "הזמנה בוואטסאפ", y0 + 22, 40, INK, a, True)
    draw_mixed_centered(layer, "הקישור בפרופיל", y0 + bh2 + 28, 30, GOLD_SOFT, a, True)
    im.alpha_composite(layer)


def apply_logo(im, alpha: float, y: int = 48):
    if LOGO is None or alpha < 0.05:
        return
    logo = LOGO.copy()
    logo.putalpha(logo.split()[-1].point(lambda a: int(a * alpha)))
    im.alpha_composite(logo, ((W - logo.size[0]) // 2, y))


def render_frame(i: int) -> Image.Image:
    t = i / FPS
    im = bg(t)
    apply_logo(im, min(1.0, t / 0.4) if t < DURATION - 0.3 else max(0.0, (DURATION - t) / 0.3))

    # Beat A — hook 0–2.2
    u_hook = line_u(t, 0.12, 2.25, 0.22, 0.28)
    if u_hook > 0:
        pill_caption(im, "שנה שלמה בבית", 780, 58, IVORY, u_hook)
        pill_caption(im, "מארז כפול  שתי קופסאות", 900, 36, GOLD, u_hook * 0.95)

    # Beat B — product hero 1.7–5.5
    u_prod = line_u(t, 1.7, 5.55, 0.32, 0.28)
    if u_prod > 0:
        y = 580 + int(6 * math.sin(t * 2.0))
        place_product(im, 900, y, pop=u_prod, alpha=1.0)
        u_lab = line_u(t, 2.4, 5.4, 0.22, 0.25)
        if u_lab > 0:
            pill_caption(im, "נוזל Kirkland  מקורי מארה״ב", 1280, 34, IVORY, u_lab)

    # Beat C — offer math 5.3–8.1 (product smaller on top)
    u_price = line_u(t, 5.3, 8.15, 0.28, 0.22)
    if u_price > 0:
        place_product(im, 640, 500, pop=u_price, alpha=1.0)
        price_block(im, u_price)

    # Beat D — WA close 7.9–10.5
    u_cta = line_u(t, 7.9, 10.5, 0.26, 0.12)
    if u_cta > 0:
        place_product(im, 560, 460, pop=1.0, alpha=0.95)
        price_block(im, max(u_price, 0.9))
        cta_block(im, u_cta)

    return im.convert("RGB")


def write_soft_audio(path: Path, duration: float, sr: int = 44100):
    """Retention audio v2 — ~96 BPM pulse + whooshes + ticks + price ding.

    Hit map locked to picture: 0.20 open · 1.70–1.80 product · 5.30–5.60 price · 7.90–8.00 CTA.
    Target louder than v1 (~−18 dBFS RMS) without clipping.
    """
    n = int(sr * duration)
    beat = 60.0 / 96.0  # 0.625s
    samples = [0.0] * n

    def add(i: int, v: float):
        if 0 <= i < n:
            samples[i] += v

    # Precompute noise for whooshes
    rng = np.random.default_rng(42)
    noise = rng.standard_normal(n).astype(np.float64)

    for i in range(n):
        t = i / sr
        # --- kick pulse every beat ---
        kick = 0.0
        # phase within beat
        kphase = (t % beat)
        if kphase < 0.08:
            # decaying thump 60 Hz
            kick_amp = 0.22 - 0.10 * (t / max(duration, 0.01))  # 0.22 → ~0.12
            kick = kick_amp * math.exp(-kphase * 55) * math.sin(2 * math.pi * 62 * kphase)
        # duck pad under kick
        duck = 0.55 if kphase < 0.05 else (0.55 + 0.45 * min(1.0, (kphase - 0.05) / 0.12) if kphase < 0.17 else 1.0)

        # --- warm pad (quieter under kicks) ---
        breathe = 0.6 + 0.4 * math.sin(2 * math.pi * 0.35 * t)
        pad = (0.055 * math.sin(2 * math.pi * 110 * t) + 0.028 * math.sin(2 * math.pi * 164.8 * t)) * breathe * duck

        # --- shimmer (more present) ---
        shim = 0.03 * math.sin(2 * math.pi * 990 * t) * (0.5 + 0.5 * math.sin(2 * math.pi * 0.5 * t))

        # CTA swell 7.85–8.40
        swell = 1.0
        if 7.85 <= t <= 10.2:
            swell = 1.0 + 0.55 * ease_in_out(min(1.0, (t - 7.85) / 0.55))

        samples[i] = (pad + shim) * swell + kick

    # --- whooshes (band-ish noise bursts) ---
    for at, amp in ((1.70, 0.20), (5.30, 0.22), (7.90, 0.24)):
        for j in range(int(0.12 * sr)):
            tt = j / sr
            idx = int(at * sr) + j
            if idx >= n:
                break
            env = math.exp(-tt * 22) * (1 - abs(tt - 0.04) / 0.08 if tt < 0.08 else 0.0)
            # cheap BP feel: difference of two smoothings via sine AM mid
            who = amp * env * noise[idx] * math.sin(2 * math.pi * 900 * tt)
            samples[idx] += who
            # brief pad duck around whoosh
            for k in range(int(0.05 * sr)):
                di = idx + k
                if di < n:
                    samples[di] *= 0.55 + 0.45 * (k / max(1, int(0.05 * sr)))

    # --- tick accents ---
    for at, amp in ((0.20, 0.28), (1.80, 0.30), (5.60, 0.34), (8.00, 0.36)):
        for j in range(int(0.08 * sr)):
            tt = j / sr
            idx = int(at * sr) + j
            if idx >= n:
                break
            body = amp * math.exp(-tt * 40) * math.sin(2 * math.pi * 260 * tt)
            click = amp * 0.55 * math.exp(-tt * 90) * math.sin(2 * math.pi * 2800 * tt)
            samples[idx] += body + click

    # --- price ding 5.55–5.70 ---
    for j in range(int(0.10 * sr)):
        tt = j / sr
        idx = int(5.55 * sr) + j
        if idx >= n:
            break
        ding = 0.18 * math.exp(-tt * 28) * (
            math.sin(2 * math.pi * 880 * tt) + 0.45 * math.sin(2 * math.pi * 1760 * tt)
        )
        samples[idx] += ding

    # master envelope + peak normalize to ~-1 dBTP with loudness lift
    out = array("h")
    peak = 1e-9
    for i, s in enumerate(samples):
        t = i / sr
        env = 1.0
        if t < 0.08:
            env = t / 0.08
        if t > 10.15:
            env *= max(0.0, (duration - t) / max(0.01, duration - 10.15))
        samples[i] = s * env
        peak = max(peak, abs(samples[i]))
    # aim louder: scale so peak ~0.89 (−1 dBTP-ish)
    gain = 0.89 / peak
    for s in samples:
        out.append(int(max(-1.0, min(1.0, s * gain)) * 32767))

    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(out.tobytes())


def main():
    print(f"rendering {N} frames @ {FPS}fps ({DURATION}s)…")
    # clear old frames
    for f in FRAMES.glob("*.jpg"):
        f.unlink()
    cover = None
    for i in range(N):
        frame = render_frame(i)
        frame.save(FRAMES / f"f_{i:04d}.jpg", quality=93, subsampling=0)
        if i == int(2.8 * FPS):
            cover = frame.copy()
        if i % 30 == 0:
            print(f"  {i}/{N}")
    if cover is None:
        cover = Image.open(FRAMES / "f_0084.jpg")

    wav = ROOT / "audio.wav"
    write_soft_audio(wav, DURATION)

    mp4_name = "MinoxShop-CLOSE-double-765-10s.mp4"
    cover_name = "MinoxShop-CLOSE-double-765-COVER.jpg"
    out_mp4 = EXPORTS / mp4_name
    out_cover = EXPORTS / cover_name
    cover.save(out_cover, quality=95, subsampling=0)
    cover.save(ARTIFACTS / cover_name, quality=95, subsampling=0)

    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES / "f_%04d.jpg"),
        "-i", str(wav),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-shortest",
        "-movflags", "+faststart",
        str(out_mp4),
    ]
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    shutil.copy2(out_mp4, ARTIFACTS / mp4_name)
    print("OK", out_mp4, out_mp4.stat().st_size)
    print("COVER", out_cover)


if __name__ == "__main__":
    main()
