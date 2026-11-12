"""Generates the episode's missing clip/audio inputs with ffmpeg lavfi.

Only for trying out the setup; real episodes use a Unity render and licensed audio.
Does not touch existing files.
"""

from pathlib import Path

from pipeline.config import Episode, event_files
from pipeline.ffmpeg import ffmpeg

FPS = 30


def _clip(path: Path, size: str, loop_s: float) -> None:
    # fixed pattern + periodic hue cycle; seamless since the loop is an exact multiple of the period
    period = loop_s / max(1, round(loop_s / 10))
    source = f"smptehdbars=s={size}:r={FPS},hue=H=2*PI*t/{period}"
    ffmpeg(
        *["-f", "lavfi", "-i", source, "-t", loop_s],
        *["-c:v", "libx264", "-crf", 18, "-pix_fmt", "yuv420p", path],
    )


def run(ep: Episode) -> int:
    made: list[Path] = []

    for path, size in ((ep.visual.clip_16x9, "1920x1080"), (ep.visual.clip_9x16, "1080x1920")):
        if path and not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            _clip(path, size, ep.loop_seconds)
            made.append(path)

    for i, bed in enumerate(ep.audio.beds):
        if not bed.file.exists():
            bed.file.parent.mkdir(parents=True, exist_ok=True)
            noise = f"anoisesrc=d=30:c=brown:r=48000:a=0.3:s={ep.seed + i}"
            ffmpeg("-f", "lavfi", "-i", noise, "-ac", 2, bed.file)
            made.append(bed.file)

    for i, event in enumerate(ep.audio.events):
        if event_files(event.file):
            continue
        for n in (1, 2):
            path = Path(event.file.replace("*", str(n)))
            if path.exists():
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            tone = f"sine=f={110 * (i + 1) * n}:d=2:r=48000"
            fade = "afade=t=in:d=0.05,afade=t=out:st=0.4:d=1.6"
            ffmpeg("-f", "lavfi", "-i", tone, "-af", fade, "-ac", 2, path)
            made.append(path)

    for path in made:
        print(f"synthetic: {path}")
    print(f"{len(made)} files generated" if made else "no missing inputs")
    return 0
