import re

import numpy as np
import pytest

from pipeline import audio
from pipeline.config import Episode
from pipeline.ffmpeg import duration, ffmpeg

DUR = 60.0


@pytest.fixture(scope="module")
def assets(tmp_path_factory):
    d = tmp_path_factory.mktemp("assets")
    ffmpeg("-f", "lavfi", "-i", "anoisesrc=d=8:r=44100:a=0.05:c=pink:seed=3", d / "bed.wav")
    for n in ("a", "b"):
        f = 440 if n == "a" else 660
        ffmpeg("-f", "lavfi", "-i", f"sine=f={f}:d=1:r=44100", "-ac", "1", d / f"ev_{n}.wav")
    return d


def make_ep(assets, seed=1, use_case="general", ev_gain=(-12, -4), max_gain=0.0):
    return Episode.model_validate(
        {
            "slug": "t", "seed": seed, "use_case": use_case, "title": "t", "description": "d",
            "duration_s": DUR, "nominal_duration_s": DUR, "loop_seconds": 8,
            "event_density": 1.0, "event_max_gain_db": max_gain,
            "visual": {"unity_preset": "p", "clip_16x9": "x.mp4"},
            "audio": {
                "target_lufs": -20, "true_peak": -1.5,
                "beds": [{"file": str(assets / "bed.wav"), "gain_db": 0}],
                "events": [{
                    "file": str(assets / "ev_*.wav"), "every_s": [3, 6],
                    "gain_db": list(ev_gain), "pan_jitter": 0.5,
                }],
            },
            "short": {
                "font": "f.ttf", "hook": "h", "cta": "c",
                "text_color": "white", "outline_color": "black",
            },
            "channel": {"name": "n", "handle": "h", "niche": "n", "language": "en", "voice": "v"},
        }
    )  # fmt: skip


@pytest.fixture(scope="module")
def base(assets, tmp_path_factory):
    return audio.render(make_ep(assets), tmp_path_factory.mktemp("w1"), DUR)


def test_determinism(assets, base, tmp_path):
    same = audio.render(make_ep(assets), tmp_path / "a", DUR)
    other = audio.render(make_ep(assets, seed=2), tmp_path / "b", DUR)
    assert same.events == base.events and base.events
    assert other.events != base.events


def test_length(base):
    assert DUR <= duration(base.path) <= DUR + 0.05
    assert not list(base.path.parent.glob("audio_raw*"))


def test_loudness(base):
    log = ffmpeg(
        "-i", base.path, "-af", "ebur128=peak=true:framelog=verbose", "-f", "null", "-",
        loglevel="info",
    )  # fmt: skip
    summary = log[log.rindex("Summary:") :]
    lufs = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summary)[1])
    tp = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summary)[1])
    print(f"integrated={lufs} LUFS true_peak={tp} dBTP")
    assert abs(lufs - -20) <= 1
    assert tp <= -1.0


def test_bed_loop_seam(assets, tmp_path):
    x = audio._load(assets / "bed.wav", tmp_path)
    unit = audio._loop_unit(x, int(audio.CROSSFADE_S * audio.SR))
    w = audio.SR // 10
    rms = lambda a: 10 * np.log10(np.mean(a**2))  # noqa: E731
    assert abs(rms(unit[-w:]) - rms(unit[:w])) < 3
    seam = np.concatenate([unit[-w:], unit[:w]])
    assert abs(rms(seam[:w]) - rms(seam[w:])) < 3


def test_sleep_cap(assets, tmp_path):
    ep = make_ep(assets, use_case="sleep", ev_gain=(0, 0))
    res = audio.render(ep, tmp_path, DUR)
    assert res.events
    assert all(h.peak_db <= res.bed_rms_db + 10 + 1e-6 for h in res.events)
    assert any(h.gain_db < 0 for h in res.events)  # kısma gerçekten devreye girdi


def test_errors(assets, tmp_path):
    ep = make_ep(assets)
    ep.audio.beds[0].file = tmp_path / "yok.wav"
    with pytest.raises(FileNotFoundError):
        audio.render(ep, tmp_path / "w", 10)
    ep = make_ep(assets)
    ep.audio.events[0].file = str(tmp_path / "none_*.wav")
    with pytest.raises(FileNotFoundError):
        audio.render(ep, tmp_path / "w2", 10)
