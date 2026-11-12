from pathlib import Path

import pytest

from pipeline.config import load_episode, parse_duration


def test_parse_duration():
    assert parse_duration("8h") == 28800
    assert parse_duration("10m") == 600
    assert parse_duration("90s") == 90
    assert parse_duration(45) == 45.0
    with pytest.raises(ValueError):
        parse_duration("ten minutes")


def test_use_case_and_brand_defaults(project: Path):
    ep = load_episode(project)
    assert ep.duration_s == 8 * 3600 and not ep.duration_overridden
    assert ep.audio.target_lufs == -20  # use_case default
    assert ep.short.cta == "Full 8h on @test"  # brand template
    assert ep.short.duration_s == 20  # episode field
    assert ep.description_footer == "Subscribe for more."


def test_duration_override_keeps_nominal_texts(project: Path):
    ep = load_episode(project, "30s")
    assert ep.duration_s == 30 and ep.duration_overridden
    assert ep.short.cta == "Full 8h on @test"


def test_episode_overrides_use_case_and_brand(project: Path):
    path = project / "episode.yaml"
    path.write_text(
        path.read_text().replace("  beds:", "  target_lufs: -23\n  beds:")
        + '  cta: "Custom"\nduration: 3h\n'
    )
    ep = load_episode(project)
    assert (ep.audio.target_lufs, ep.short.cta, ep.duration_s) == (-23, "Custom", 3 * 3600)


def test_brand_local_overrides_brand_per_field(project: Path):
    Path("config/brand.local.yaml").write_text('channel: {handle: "@fork"}\n')
    ep = load_episode(project)
    assert ep.channel.handle == "@fork"
    assert ep.channel.name == "Test Channel"  # a field that is not overridden is kept
    assert ep.short.cta == "Full 8h on @fork"


def test_unknown_field_is_rejected(project: Path):
    path = project / "episode.yaml"
    path.write_text(path.read_text() + "typo_field: 1\n")
    with pytest.raises(ValueError):
        load_episode(project)
