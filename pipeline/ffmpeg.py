"""All ffmpeg/ffprobe calls go through here: -hide_banner -loglevel error -nostats."""

import json
import re
import subprocess
import tempfile
import time
from pathlib import Path

from pipeline.progress import Progress


def ffmpeg(
    *args: object, loglevel: str = "error", progress: tuple[str, float] | None = None
) -> str:
    """Runs ffmpeg, returns stderr. Measurement filters (ebur128, loudnorm): loglevel="info".

    progress=(label, total_seconds): draws a progress bar from ffmpeg's -progress file.
    """
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", loglevel, "-nostats", "-y"]
    if not progress:
        p = subprocess.run([*cmd, *map(str, args)], capture_output=True, text=True)
        code, stderr = p.returncode, p.stderr
    else:
        label, total_s = progress
        bar = Progress(label)
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "progress"
            cmd += ["-progress", str(state), *map(str, args)]
            # stderr goes to a file: a pipe could fill up while we poll
            with open(Path(tmp) / "stderr", "w+") as err:
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=err)
                while proc.poll() is None:
                    time.sleep(0.5)
                    bar.update(_out_time_s(state) / total_s)
                err.seek(0)
                code, stderr = proc.returncode, err.read()
        if not code:
            bar.done()
    if code:
        raise RuntimeError(f"ffmpeg failed ({code}): {' '.join(cmd)}\n{stderr[-2000:]}")
    return stderr


def _out_time_s(state: Path) -> float:
    """Last out_time reported in an ffmpeg -progress file, in seconds."""
    try:
        with open(state, "rb") as f:
            f.seek(max(0, state.stat().st_size - 2048))
            tail = f.read().decode(errors="replace")
    except FileNotFoundError:
        return 0.0
    hits = re.findall(r"out_time_us=(\d+)", tail)
    return int(hits[-1]) / 1e6 if hits else 0.0


def probe(path: Path) -> dict:
    cmd = ["ffprobe", "-hide_banner", "-loglevel", "error", "-show_format", "-show_streams"]
    p = subprocess.run([*cmd, "-of", "json", str(path)], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(f"ffprobe failed: {path}\n{p.stderr[-2000:]}")
    return json.loads(p.stdout)


def duration(path: Path) -> float:
    return float(probe(path)["format"]["duration"])
