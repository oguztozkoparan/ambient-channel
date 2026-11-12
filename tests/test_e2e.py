"""End to end: synth -> build -> qc, with synthetic inputs."""

import json
from pathlib import Path

from pipeline.cli import main


def test_synth_build_qc_all_pass(project: Path):
    assert main(["synth", str(project)]) == 0
    assert main(["build", str(project), "--duration", "30s"]) == 0
    assert main(["qc", "output/demo"]) == 0

    out = Path("output/demo")
    checks = json.loads((out / "qc.json").read_text())
    assert checks and all(c["pass"] for c in checks), [c for c in checks if not c["pass"]]

    meta = json.loads((out / "metadata.json").read_text())
    assert meta["description"].endswith("Subscribe for more.")
    assert meta["tags"] == ["demo", "ambience"]
    assert meta["short"]["cta"] == "Full 8h on @test"
    assert meta["build"]["total_s"] == 30


def test_qc_flags_chapter_outside_video(project: Path):
    from pipeline import qc

    meta = {
        "slug": "demo",
        "title": "Demo | 8 Hours",
        "description": "A demo description.",
        "chapters": [{"t": "00:00", "label": "a"}, {"t": "09:00:00", "label": "too late"}],
        "build": {
            "duration_overridden": False,
            "nominal_duration_s": 28800,
            "description_footer": "",
        },
    }
    by_name = {c["check"]: c for c in qc._metadata(meta)}
    assert by_name["chapters_within_duration"]["value"] == ["09:00:00"]
    assert not by_name["chapters_within_duration"]["pass"]
    assert by_name["title_duration_consistent"]["pass"]
