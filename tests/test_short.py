from types import SimpleNamespace

import pytest

from pipeline import short
from pipeline.ffmpeg import duration, ffmpeg, probe
from tests.test_video import make_ep, vstream


def test_pick_window():
    assert short.pick_window([], 60, 20) == 0
    assert short.pick_window([5, 40, 41, 42], 60, 20) == 40
    assert short.pick_window([55, 56, 57], 60, 20) == 40  # does not run past the end of the audio
    assert short.pick_window([1, 30], 60, 20) == 0  # earliest on a tie (the 0 window covers 1)


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    d = tmp_path_factory.mktemp("short")
    clip = d / "c16.mp4"
    ffmpeg(
        "-f", "lavfi", "-i", "smptehdbars=s=1920x1080:r=30", "-t", 4, "-pix_fmt", "yuv420p", clip
    )
    c9 = d / "c9.mp4"
    ffmpeg("-f", "lavfi", "-i", "testsrc=s=1080x1920:r=30", "-t", 4, "-pix_fmt", "yuv420p", c9)
    aud = d / "a.m4a"
    ffmpeg("-f", "lavfi", "-i", "anoisesrc=d=60:a=0.05:seed=1", "-c:a", "aac", aud)
    return d, clip, c9, aud


def run(env, name, **over):
    d, clip, c9, aud = env
    ep = make_ep(d, clip, **over)
    ev = [SimpleNamespace(t=t, duration=1) for t in (5, 40, 41, 42)]
    out = d / f"{name}.mp4"
    info = short.build_short(ep, SimpleNamespace(path=aud, events=ev), out, d / name)
    return out, info


def check(out):
    s = vstream(out)
    assert (s["width"], s["height"], s["pix_fmt"]) == (1080, 1920, "yuv420p")
    assert abs(duration(out) - 20) <= 0.1
    assert any(x["codec_type"] == "audio" for x in probe(out)["streams"])


def test_center_crop(env):
    out, info = run(env, "crop", short={**make_short(), "line2": "second: line"})
    check(out)
    assert info["audio_start_s"] == 40


def test_9x16_clip(env):
    d, _, c9, _ = env
    out, _ = run(
        env, "nine", visual={"unity_preset": "p", "clip_16x9": str(env[1]), "clip_9x16": str(c9)}
    )
    check(out)


def test_watermark(env):
    d = env[0]
    wm = d / "wm.png"
    ffmpeg("-f", "lavfi", "-i", "color=red:s=100x100", "-frames:v", 1, wm)
    out, _ = run(env, "wm", watermark={"file": str(wm)})
    check(out)


def make_short():
    from tests.test_video import FONT

    return {
        "duration_s": 20, "font": str(FONT), "hook": "POV: it's 3am: don't sleep",
        "cta": "Full 8h: watch", "text_color": "white", "outline_color": "black",
    }  # fmt: skip
