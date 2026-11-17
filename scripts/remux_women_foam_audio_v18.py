#!/usr/bin/env python3
"""Remux women foam v17 picture with world-class dread bed (v18)."""
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "exports/women-foam-double/MinoxShop-WOMEN-foam-double-v17-16s.mp4"
BED = ROOT / "assets/audio/women-shed-world-dread-bed.wav"
OUT = ROOT / "exports/women-foam-double/MinoxShop-WOMEN-foam-double-v18-16s.mp4"
def main():
    subprocess.check_call([
        "ffmpeg","-y","-i",str(SRC),"-i",str(BED),
        "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k",
        "-shortest","-movflags","+faststart",str(OUT),
    ])
    print("wrote", OUT)
if __name__ == "__main__":
    main()
