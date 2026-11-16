#!/usr/bin/env python3
"""Remux women foam double v10 picture with dread pressure bed (v13)."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SRC_VID = ROOT / "exports/women-foam-double/MinoxShop-WOMEN-foam-double-v10-16s.mp4"
BED = ROOT / "assets/audio/women-shed-dread-bed.wav"
OUT = ROOT / "exports/women-foam-double/MinoxShop-WOMEN-foam-double-v13-16s.mp4"

def main():
    assert SRC_VID.exists(), SRC_VID
    assert BED.exists(), BED
    OUT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.check_call([
        "ffmpeg", "-y",
        "-i", str(SRC_VID),
        "-i", str(BED),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        str(OUT),
    ])
    print("wrote", OUT)

if __name__ == "__main__":
    main()
