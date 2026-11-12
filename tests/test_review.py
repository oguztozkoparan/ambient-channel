"""Regression tests for bugs found in the code review."""

import json
import shutil
from pathlib import Path

import pytest

from pipeline import qc
from pipeline.cli import main
from pipeline.config import Event, load_episode


def _edit(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    assert old in text
    path.write_text(text.replace(old, new))


def _failed(slug: str = "demo") -> list[str]:
    checks = json.loads(Path(f"output/{slug}/qc.json").read_text())
    return [c["check"] for c in checks if not c["pass"]]


def test_special_characters_in_short_text_and_stale_qc(project: Path):
    _edit(project / "episode.yaml", "POV: it's a test", "100% rain, no\\\\thunder: it's a test")
    stale = Path("output/demo/qc.json")
    stale.parent.mkdir(parents=True)
    stale.write_text("[]")
    assert main(["build", str(project), "--trial", "--duration", "30s"]) == 0
    assert not stale.exists()  # a rebuild must not leave the previous verdict behind


def test_apostrophe_in_project_path_and_45s_short(project: Path, tmp_path, monkeypatch):
    _edit(project / "episode.yaml", "duration_s: 20", "duration_s: 45")
    root = tmp_path.parent / f"{tmp_path.name} o'brien"
    shutil.copytree(tmp_path, root)
    monkeypatch.chdir(root)
    assert main(["build", str(project), "--trial", "--duration", "50s"]) == 0
    main(["qc", "output/demo"])
    assert _failed() == []


@pytest.mark.parametrize("every_s", [[0, 0], [-5, -1], [5, 1]])
def test_event_interval_that_never_advances_is_rejected(every_s):
    with pytest.raises(ValueError):
        Event(file="x_*.wav", every_s=every_s, gain_db=[-10, -5])


def test_unknown_cta_placeholder_gives_message(project: Path, capsys):
    _edit(Path("config/brand.yaml"), "Full {hours}h on {handle}", "Full {hourz}h on {handle}")
    assert main(["check", str(project)]) == 2
    assert "hourz" in capsys.readouterr().err


def test_episode_can_turn_brand_watermark_off(project: Path):
    _edit(Path("config/brand.yaml"), "file: null", "file: assets/brand/logo.png")
    assert load_episode(project).watermark.file == Path("assets/brand/logo.png")
    with (project / "episode.yaml").open("a") as f:
        f.write("watermark: {file: null}\n")
    assert load_episode(project).watermark.file is None


def _meta(title: str, variant_of: str | None = None) -> dict:
    build = {"trial": True, "variant_of": variant_of, "description_footer": ""}
    return {
        "slug": "demo",
        "title": title,
        "description": "A demo.",
        "chapters": [],
        "build": build,
    }


def _overlap(meta: dict) -> dict:
    return next(c for c in qc._metadata(meta) if c["check"] == "title_word_overlap")


def test_title_overlap_ignores_shared_suffix_and_variant_source(project: Path):
    suffix = "Ambience for Sleep, Study & Relaxation"
    _edit(Path("config/use_cases.yaml"), 'title_suffix: "Ambience"', f'title_suffix: "{suffix}"')
    other = Path("episodes/other")
    other.mkdir()
    other_title = f"Gale Against a Lighthouse Lamp Room | 8 Hours Coastal {suffix}"
    (other / "episode.yaml").write_text(f'slug: other\ntitle: "{other_title}"\n')

    assert _overlap(_meta(f"Rainy Cabin | 8 Hours Cozy {suffix}"))["pass"]  # distinct scene
    assert not _overlap(_meta(f"Gale Against a Lighthouse Lamp Room | 8 Hours Stormy {suffix}"))[
        "pass"
    ]
    variant = _meta("Gale Against a Lighthouse Lamp Room | 10 Hours Coastal Sleep", "other")
    assert _overlap(variant)["pass"]  # a variant shares its source's scene by design
