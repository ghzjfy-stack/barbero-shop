#!/usr/bin/env python3
"""Build scroll-stopping hook COVER for MM clipper reel v7.

v6 cover was a product BF card — weak vs the viral clipper hook we designed.
v7 cover = thinning scalp + red clipper + yellow «לגלח…?» + BF 375 chip
(IG center-safe). Also remuxes YT Shorts hold to the same hook thumb.
"""

from __future__ import annotations

import math
import os
import shutil
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

# Reuse v6 body renderer helpers by importing the module
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
V6 = ROOT / "scripts" / "mm_six_pack_audio_v6_reel.py"
spec = importlib.util.spec_from_file_location("mm_v6", V6)
mm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mm)

W, H, FPS = mm.W, mm.H, mm.FPS
COVER_HOLD_N = mm.COVER_HOLD_N
COVER_HOLD_SEC = mm.COVER_HOLD_SEC
ASSETS = Path(os.environ.get("MM_ASSETS", "/tmp/mm-reel"))
BODY_FRAMES = Path(os.environ.get("MM_BODY_FRAMES", "/tmp/mm-six-pack-v6/frames"))
BODY_AUDIO = Path(os.environ.get("MM_BODY_AUDIO", "/tmp/mm-six-pack-v6/audio.wav"))
BODY_MP4 = Path(os.environ.get("MM_BODY_MP4", "/tmp/mm-six-pack-v6/MinoxShop_MM_clipper_v6_17s.mp4"))
OUT = Path(os.environ.get("MM_OUT", "/tmp/mm-hook-cover-v7"))
ART = Path("/opt/cursor/artifacts")


def build_hook_cover(scalp: Image.Image) -> Image.Image:
    """Viral-pattern cover: clipper threat + BF price chip (center-safe)."""
    # Match mid-hook framing (~1.2s into body)
    plate = mm.cover_window(scalp, zoom=1.28, focus_x=0.50, focus_y=0.36)
    plate = mm.grade(plate, contrast=1.22, bright=0.88, color=1.08)
    canvas = plate.convert("RGBA")

    tip_y = H * 0.52
    mm.red_cut_path(canvas, 1.2, tip_y)
    mm.draw_red_clipper(canvas, W * 0.50, tip_y - 10, scale=1.65, buzz=0.9)

    # Yellow hook text — top, scroll-stop
    mm.chip_block(
        canvas,
        int(H * 0.08),
        ["לגלח את זה", "ולגמור עם זה?"],
        size=62,
        opacity=1.0,
        style="hook",
        pop=1.0,
    )

    # BF + price — IG center-safe band (~middle third), doesn't kill the scare
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    y = int(H * 0.72)

    def measure(text: str, size: int):
        bb = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), text, font=mm.font(size))
        return bb[2] - bb[0], bb[3] - bb[1]

    bf = "BLACK FRIDAY"
    ww, hh = measure(bf, 40)
    bfw, bfh = ww + 44, hh + 22
    bfx = (W - bfw) // 2
    d.rounded_rectangle((bfx, y, bfx + bfw, y + bfh), radius=12, fill=(196, 22, 32, 245))
    mm.draw_text(d, (W // 2, y + bfh // 2), bf, size=40, fill=(255, 255, 255, 255))
    y += bfh + 14

    price = "375₪"
    ww, hh = measure(price, 96)
    pw, ph = ww + 56, hh + 28
    px = (W - pw) // 2
    d.rounded_rectangle((px, y, px + pw, y + ph), radius=22, fill=(0, 0, 0, 245))
    mm.draw_text(d, (W // 2, y + ph // 2), price, size=96, fill=(255, 255, 255, 255))
    y += ph + 12
    mm.draw_text(d, (W // 2, y), "6 בקבוקים · טיפות", size=34, fill=(255, 220, 80, 255))

    canvas = Image.alpha_composite(canvas, layer)
    return canvas.convert("RGB")


def remux_yt(cover: Image.Image, yt_mp4: Path):
    if not BODY_FRAMES.exists() or not BODY_AUDIO.exists():
        print("Skip YT remux — body frames/audio missing")
        return
    yt_frames = OUT / "frames_yt"
    if yt_frames.exists():
        shutil.rmtree(yt_frames)
    yt_frames.mkdir(parents=True)
    for i in range(COVER_HOLD_N):
        cover.save(yt_frames / f"f_{i:05d}.png")
    # symlink/copy body frames
    n_body = len(list(BODY_FRAMES.glob("f_*.png")))
    for i in range(n_body):
        src = BODY_FRAMES / f"f_{i:05d}.png"
        dst = yt_frames / f"f_{COVER_HOLD_N + i:05d}.png"
        if src.exists():
            shutil.copy2(src, dst)
    with wave.open(str(BODY_AUDIO), "rb") as r:
        sr, sw, ch = r.getframerate(), r.getsampwidth(), r.getnchannels()
        body = r.readframes(r.getnframes())
    lead = b"\x00" * (int(COVER_HOLD_SEC * sr) * sw * ch)
    yt_audio = OUT / "audio_yt.wav"
    with wave.open(str(yt_audio), "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(sw)
        w.setframerate(sr)
        w.writeframes(lead + body)
    mm.encode_mp4(yt_frames, yt_audio, yt_mp4)
    print("Wrote", yt_mp4)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    scalp = mm.load_rgb(ASSETS / "scalp.jpg")
    cover = build_hook_cover(scalp)
    cover_path = OUT / "MinoxShop_MM_clipper_v7_COVER.jpg"
    cover.save(cover_path, quality=95)

    # IG/TT body already starts on hook — reuse v6 mp4
    ig_mp4 = OUT / "MinoxShop_MM_clipper_v7_17s.mp4"
    if BODY_MP4.exists():
        shutil.copy2(BODY_MP4, ig_mp4)
    else:
        print("WARN: body mp4 missing — cover only")

    yt_mp4 = OUT / "MinoxShop_MM_clipper_v7_YT.mp4"
    remux_yt(cover, yt_mp4)

    shutil.copy2(cover_path, ART / "DOWNLOAD_MinoxShop_MM_clipper_v7_COVER.jpg")
    cover.save(ART / "mm_v7_preview_cover.jpg", quality=92)
    if ig_mp4.exists():
        shutil.copy2(ig_mp4, ART / "DOWNLOAD_MinoxShop_MM_clipper_v7_17s.mp4")
        shutil.copy2(ig_mp4, ART / "mm_clipper_v7_demo.mp4")
    if yt_mp4.exists():
        shutil.copy2(yt_mp4, ART / "DOWNLOAD_MinoxShop_MM_clipper_v7_YT.mp4")

    # side-by-side compare: old product cover vs new hook
    print("Wrote", cover_path)


if __name__ == "__main__":
    main()
