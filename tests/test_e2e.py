"""End to end: synth -> build -> qc, with synthetic inputs."""

import json
from pathlib import Path

from pipeline.cli import main


def test_synth_build_qc_all_pass(project: Path):
    assert main(["check", str(project)]) == 1  # nothing rendered or recorded yet
    assert main(["build", str(project), "--trial", "--duration", "30s"]) == 0
    assert main(["check", str(project)]) == 0
    assert main(["qc", "output/demo"]) == 0

    out = Path("output/demo")
    checks = json.loads((out / "qc.json").read_text())
    assert checks and all(c["pass"] for c in checks), [c for c in checks if not c["pass"]]

    meta = json.loads((out / "metadata.json").read_text())
    assert meta["description"].endswith("Subscribe for more.")
    assert meta["tags"] == ["demo", "ambience"]
    assert meta["short"]["cta"] == "Full 8h on @test"
    assert meta["build"]["total_s"] == 30
    assert meta["build"]["trial"] is True
    assert (out / "thumbnail.jpg").stat().st_size > 0


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


def test_build_lists_every_missing_input_at_once(project: Path, capsys):
    assert main(["build", str(project)]) == 1
    err = capsys.readouterr().err
    for expected in ("loop_16x9.mp4", "bed.wav", "ping_*.wav", "--trial"):
        assert expected in err


def test_user_mistakes_give_messages_not_tracebacks(project: Path, capsys):
    assert main(["check", "episodes/nope"]) == 2
    assert "episode not found" in capsys.readouterr().err
    path = project / "episode.yaml"
    path.write_text(path.read_text().replace("loop_seconds:", "loop_secs:"))
    assert main(["check", str(project)]) == 2
    err = capsys.readouterr().err
    assert "loop_secs" in err and "loop_seconds" in err


def test_older_brand_without_new_fields_still_loads(project: Path):
    from pipeline.config import load_episode

    brand = Path("config/brand.yaml")
    brand.write_text(brand.read_text().replace("  text_color: white\n  outline_color: black\n", ""))
    assert load_episode(project).short.text_color == "white"
