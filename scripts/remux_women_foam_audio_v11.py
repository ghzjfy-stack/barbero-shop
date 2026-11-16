#!/usr/bin/env python3
"""Remux women foam v10 picture with men's soft-fun bed (v34/v39 style).

Same bed family as men's foam: soft 112BPM pluck + kick + pad.
NOT the early synthetic beep beds.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "exports" / "women-foam-double"
SRC_VIDEO = EXPORT / "MinoxShop-WOMEN-foam-double-v10-16s.mp4"
BED_SRC = ROOT / "assets" / "audio" / "men-foam-soft-fun-112bpm.wav"
WORK = Path("/tmp/women-foam-v11")
OUT = EXPORT / "MinoxShop-WOMEN-foam-double-v11-16s.mp4"
DURATION = 16.0


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    bed = WORK / "bed_women_v11.wav"
    if not BED_SRC.exists():
        raise SystemExit(f"missing men's bed: {BED_SRC}")
    if not SRC_VIDEO.exists():
        raise SystemExit(f"missing picture: {SRC_VIDEO}")
    subprocess.run(
        [
            "ffmpeg", "-y", "-stream_loop", "1", "-i", str(BED_SRC),
            "-af",
            f"atrim=0:{DURATION+0.2},afade=t=in:st=0:d=0.45,afade=t=out:st={DURATION-0.8}:d=0.95,volume=0.82,aresample=48000",
            "-ac", "2", str(bed),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(SRC_VIDEO), "-i", str(bed),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
            "-movflags", "+faststart", str(OUT),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    print("DONE", OUT)


if __name__ == "__main__":
    main()
