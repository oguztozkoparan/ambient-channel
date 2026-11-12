"""Self-contained mini project: tests do not depend on the repo's brand.yaml (fork-safe)."""

import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

BRAND = """
channel:
  name: "Test Channel"
  handle: "@test"
  niche: "test"
  language: en
  voice: "calm"
metadata:
  description_footer: "Subscribe for more."
  default_tags: [ambience]
short:
  font: assets/fonts/font.ttf
  cta: "Full {hours}h on {handle}"
  text_color: white
  outline_color: black
watermark:
  file: null
"""

USE_CASES = """
general:
  duration: 8h
  target_lufs: -20
  event_density: 1.0
  event_max_gain_db: -4
  overlay: none
  title_suffix: "Ambience"
"""

EPISODE = """
slug: demo
seed: 7
use_case: general
title: "Demo Scene | 8 Hours Test Ambience"
description: |
  A synthetic demo scene used by the test suite.
tags: [demo]
chapters:
  - {t: "00:00", label: "Start"}
loop_seconds: 10
visual:
  unity_preset: Demo
  clip_16x9: assets/clips/demo/loop_16x9.mp4
audio:
  beds:
    - {file: assets/audio/bed.wav, gain_db: 0}
  events:
    - {file: "assets/audio/ping_*.wav", every_s: [3, 6], gain_db: [-14, -8]}
short:
  duration_s: 20
  hook: "POV: it's a test"
  line2: "nothing to see"
"""

LICENSES = """
| File | Source | License | Note |
|---|---|---|---|
| bed.wav | synthetic | CC0 | |
| ping_1.wav | synthetic | CC0 | |
| ping_2.wav | synthetic | CC0 | |
"""


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Sets up a mini project under tmp_path, chdirs into it, returns the episode directory."""
    fonts = sorted((REPO / "assets/fonts").glob("*.ttf"))
    if not fonts:
        pytest.skip("no .ttf under assets/fonts")
    for sub in ("config", "episodes/demo", "assets/fonts", "assets/audio"):
        (tmp_path / sub).mkdir(parents=True)
    (tmp_path / "config/brand.yaml").write_text(BRAND)
    (tmp_path / "config/use_cases.yaml").write_text(USE_CASES)
    (tmp_path / "episodes/demo/episode.yaml").write_text(EPISODE)
    (tmp_path / "assets/audio/LICENSES.md").write_text(LICENSES)
    shutil.copy(fonts[0], tmp_path / "assets/fonts/font.ttf")
    monkeypatch.chdir(tmp_path)
    return Path("episodes/demo")
