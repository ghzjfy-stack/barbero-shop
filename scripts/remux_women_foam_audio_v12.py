#!/usr/bin/env python3
"""v12: same men's soft-fun bed as v11, louder to match men's foam levels."""
from __future__ import annotations
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "exports" / "women-foam-double"
SRC = EXPORT / "MinoxShop-WOMEN-foam-double-v10-16s.mp4"
BED = ROOT / "assets" / "audio" / "men-foam-soft-fun-112bpm.wav"
OUT = EXPORT / "MinoxShop-WOMEN-foam-double-v12-16s.mp4"
WORK = Path("/tmp/women-foam-v12"); WORK.mkdir(parents=True, exist_ok=True)
bed = WORK / "bed.wav"
subprocess.run(["ffmpeg","-y","-stream_loop","1","-i",str(BED),"-af","atrim=0:16.2,afade=t=in:st=0:d=0.45,afade=t=out:st=15.2:d=0.95,volume=1.45,aresample=48000","-ac","2",str(bed)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
subprocess.run(["ffmpeg","-y","-i",str(SRC),"-i",str(bed),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",str(OUT)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
print("DONE", OUT)
