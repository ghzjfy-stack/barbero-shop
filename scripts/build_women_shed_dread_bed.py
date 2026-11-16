#!/usr/bin/env python3
"""Build darker dread pressure bed for women shed reel (not soft-fun)."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/audio/women-shed-dread-bed.wav"

# Sources expected in /tmp from prior foam/scrubber builds
CANDIDATES = {
    "full_pro": [
        Path("/tmp/foam-v28/sfx/full_pro.wav"),
        Path("/tmp/women-foam-v10/sfx/full_pro.wav"),
    ],
    "cinema": [
        Path("/tmp/foam-v24/bed_cinema.wav"),
        Path("/tmp/foam-v23/bed_cinema.wav"),
    ],
    "punch": [
        Path("/tmp/scrubber-v4/sfx/bed_punch.wav"),
        Path("/tmp/scrubber-v5/sfx/bed_punch.wav"),
    ],
}

def pick(key: str) -> Path:
    for p in CANDIDATES[key]:
        if p.exists():
            return p
    raise FileNotFoundError(f"missing source for {key}")

def main():
    full_pro, cinema, punch = pick("full_pro"), pick("cinema"), pick("punch")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    raw = Path("/tmp/women-shed-dread-raw.wav")
    subprocess.check_call([
        "ffmpeg", "-y",
        "-i", str(full_pro),
        "-i", str(cinema),
        "-i", str(punch),
        "-filter_complex",
        "[0:a]asetrate=48000*0.88,aresample=48000,atempo=1.136,volume=1.0[a0];"
        "[1:a]asetrate=48000*0.86,aresample=48000,atempo=1.163,volume=0.45[a1];"
        "[2:a]asetrate=48000*0.92,aresample=48000,atempo=1.087,volume=0.35[a2];"
        "[a0][a1][a2]amix=inputs=3:duration=longest:normalize=0,"
        "apad=pad_dur=16.5,atrim=0:16.5,"
        "highpass=f=35,lowpass=f=4200,"
        "bass=g=7:f=85:w=0.55,"
        "treble=g=-5:f=2800:w=0.5,"
        "afade=t=in:st=0:d=0.25,"
        "afade=t=out:st=15.5:d=0.9,"
        "volume=1.85,"
        "aresample=48000,aformat=sample_fmts=s16:channel_layouts=stereo",
        str(raw),
    ])
    # Level toward ~-26 dB mean when muxed
    subprocess.check_call([
        "ffmpeg", "-y", "-i", str(raw), "-af", "volume=0.42", str(OUT),
    ])
    print("wrote", OUT)

if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
