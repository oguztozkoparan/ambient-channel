"""Tüm ffmpeg/ffprobe çağrıları buradan geçer: -hide_banner -loglevel error -nostats."""

import json
import subprocess
from pathlib import Path


def ffmpeg(*args: object, loglevel: str = "error") -> str:
    """ffmpeg çalıştırır, stderr döner. Ölçüm filtreleri (ebur128, loudnorm): loglevel="info"."""
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", loglevel, "-nostats", "-y", *map(str, args)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"ffmpeg failed ({p.returncode}): {' '.join(cmd)}\n{p.stderr[-2000:]}")
    return p.stderr


def probe(path: Path) -> dict:
    cmd = ["ffprobe", "-hide_banner", "-loglevel", "error", "-show_format", "-show_streams"]
    p = subprocess.run([*cmd, "-of", "json", str(path)], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"ffprobe failed: {path}\n{p.stderr[-2000:]}")
    return json.loads(p.stdout)


def duration(path: Path) -> float:
    return float(probe(path)["format"]["duration"])
