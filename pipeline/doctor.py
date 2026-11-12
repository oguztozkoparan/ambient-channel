"""Üretime hazırlık kontrolü: build (pipeline çalışır mı) ve production (gerçek üretim)."""

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
    build: list[tuple[bool, str, str]] = []  # (ok, ad, eksikse yapılacak)
    production: list[tuple[bool, str, str]] = []

    for tool in ("ffmpeg", "ffprobe"):
        build.append((bool(shutil.which(tool)), tool, "brew install ffmpeg-full"))
    if shutil.which("ffmpeg"):
        fix = (
            "drawtext için libfreetype'lı build: brew install ffmpeg-full && brew link ffmpeg-full"
        )
        filters, encoders = _ffmpeg_list("-filters"), _ffmpeg_list("-encoders")
        build += [(f in filters, f"ffmpeg filtresi: {f}", fix) for f in FILTERS]
        build += [(e in encoders, f"ffmpeg encoder: {e}", fix) for e in ENCODERS]

    brand = load_brand()
    font = Path(brand["short"]["font"])
    build.append((font.exists(), f"Short fontu: {font}", "fontu ekle veya /brand-setup"))
    logo = (brand.get("watermark") or {}).get("file")
    if logo:
        build.append((Path(logo).exists(), f"watermark: {logo}", "dosyayı ekle veya null yap"))

    licenses = Path("assets/audio/LICENSES.md")
    build.append((licenses.exists(), str(licenses), "lisans kayıt dosyasını geri yükle"))

    handle = brand["channel"]["handle"]
    production += [
        (handle != PLACEHOLDER_HANDLE, f"marka: {handle}", "/brand-setup"),
        (Path(".git").exists(), "git deposu", "git init"),
        (bool(shutil.which("jq")), "jq (ruff hook'u)", "brew install jq"),
        (bool(shutil.which("unity")), "Unity CLI", "brew install --cask unity-cli"),
        (
            Path("unity/ProjectSettings").exists(),
            "Unity projesi (unity/)",
            "unity projects create ile oluştur, sahne kitini kur",
        ),
        (
            any(not p.parent.name.startswith("_") for p in Path("episodes").glob("*/episode.yaml")),
            "en az bir episode",
            "/new-episode <slug> <tema>",
        ),
    ]

    for title, rows in (("Build", build), ("Gerçek üretim", production)):
        print(f"\n{title}")
        for ok, name, fix in rows:
            print(f"  {'ok   ' if ok else 'EKSİK'}  {name}" + ("" if ok else f"  ->  {fix}"))

    build_ok = all(ok for ok, _, _ in build)
    prod_ok = build_ok and all(ok for ok, _, _ in production)
    print(f"\nDeneme build'i (pipeline synth + build): {'hazır' if build_ok else 'HAZIR DEĞİL'}")
    print(f"Gerçek üretim: {'hazır' if prod_ok else 'HAZIR DEĞİL'}")
    return 0 if build_ok else 1
