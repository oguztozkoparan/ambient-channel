"""Production readiness check: build (does the pipeline run) and production (real production)."""

import shutil
import subprocess
from pathlib import Path

from pipeline.config import PLACEHOLDER_HANDLE, load_brand

FILTERS = ("drawtext", "loudnorm", "ebur128", "ssim", "overlay")
ENCODERS = ("libx264", "aac")


def _ffmpeg_list(flag: str) -> set[str]:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostats", flag]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    return {parts[1] for line in out.splitlines() if len(parts := line.split()) > 1}


def run() -> int:
    build: list[tuple[bool, str, str]] = []  # (ok, name, fix if missing)
    production: list[tuple[bool, str, str]] = []

    for tool in ("ffmpeg", "ffprobe"):
        build.append((bool(shutil.which(tool)), tool, "brew install ffmpeg-full"))
    if shutil.which("ffmpeg"):
        fix = (
            "build with libfreetype for drawtext: brew install ffmpeg-full && brew link ffmpeg-full"
        )
        filters, encoders = _ffmpeg_list("-filters"), _ffmpeg_list("-encoders")
        build += [(f in filters, f"ffmpeg filter: {f}", fix) for f in FILTERS]
        build += [(e in encoders, f"ffmpeg encoder: {e}", fix) for e in ENCODERS]

    brand = load_brand()
    font = Path(brand["short"]["font"])
    build.append((font.exists(), f"Short font: {font}", "add the font or /brand-setup"))
    logo = (brand.get("watermark") or {}).get("file")
    if logo:
        build.append((Path(logo).exists(), f"watermark: {logo}", "add the file or set it to null"))

    licenses = Path("assets/audio/LICENSES.md")
    build.append((licenses.exists(), str(licenses), "restore the license record file"))

    handle = brand["channel"]["handle"]
    production += [
        (handle != PLACEHOLDER_HANDLE, f"brand: {handle}", "/brand-setup"),
        (Path(".git").exists(), "git repository", "git init"),
        (bool(shutil.which("jq")), "jq (ruff hook)", "brew install jq"),
        (bool(shutil.which("unity")), "Unity CLI", "brew install --cask unity-cli"),
        (
            Path("unity/ProjectSettings").exists(),
            "Unity project (unity/)",
            "create it with unity projects create, set up the scene kit",
        ),
        (
            any(not p.parent.name.startswith("_") for p in Path("episodes").glob("*/episode.yaml")),
            "at least one episode",
            "/new-episode <slug> <theme>",
        ),
    ]

    for title, rows in (("Build", build), ("Real production", production)):
        print(f"\n{title}")
        for ok, name, fix in rows:
            print(f"  {'ok     ' if ok else 'MISSING'}  {name}" + ("" if ok else f"  ->  {fix}"))

    build_ok = all(ok for ok, _, _ in build)
    prod_ok = build_ok and all(ok for ok, _, _ in production)
    print(f"\nTrial build (pipeline build --trial): {'ready' if build_ok else 'NOT READY'}")
    print(f"Real production: {'ready' if prod_ok else 'NOT READY'}")
    return 0 if build_ok else 1
