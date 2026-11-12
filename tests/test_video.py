import re
from pathlib import Path

import numpy as np
import pytest

from pipeline import video
from pipeline.config import Episode
from pipeline.ffmpeg import duration, ffmpeg, probe

FONT = Path("assets/fonts/SpaceGrotesk-Medium.ttf").resolve()
LOOP_S, REPEATS = 4, 3


def make_ep(tmp, clip, **over):
    d = {
        "slug": "t", "seed": 1, "use_case": "general", "title": "t", "description": "d",
        "duration_s": LOOP_S * REPEATS, "nominal_duration_s": LOOP_S * REPEATS,
        "loop_seconds": LOOP_S, "event_density": 1.0, "event_max_gain_db": 0.0,
        "visual": {"unity_preset": "p", "clip_16x9": str(clip), "crf": 20},
        "audio": {"target_lufs": -20, "beds": [{"file": "b.wav"}]},
        "short": {"duration_s": 20, "font": str(FONT), "hook": "h", "cta": "c",
                  "text_color": "white", "outline_color": "black"},
        "channel": {"name": "n", "handle": "@h", "niche": "n", "language": "en", "voice": "v"},
    }  # fmt: skip
    d.update(over)
    return Episode.model_validate(d)


def vstream(path):
    return next(s for s in probe(path)["streams"] if s["codec_type"] == "video")


def frame(path, t, crop="iw:ih:0:0"):
    raw = path.parent / f"{path.stem}_{t}.raw"
    ffmpeg(
        "-ss",
        t,
        "-i",
        path,
        "-frames:v",
        1,
        "-vf",
        f"crop={crop},format=gray",
        "-f",
        "rawvideo",
        raw,
    )
    return np.fromfile(raw, np.uint8).astype(float)


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    d = tmp_path_factory.mktemp("video")
    src = d / "src.mp4"
    ffmpeg("-f", "lavfi", "-i", "smptehdbars=s=1920x1080:r=30,hue=H=2*PI*t/2", "-t", LOOP_S,
           "-c:v", "libx264", "-crf", 12, "-pix_fmt", "yuv420p", src)  # fmt: skip
    aud = d / "a.m4a"
    ffmpeg("-f", "lavfi", "-i", f"anoisesrc=d={LOOP_S * REPEATS}:a=0.05:seed=1", "-c:a", "aac", aud)
    ep = make_ep(d, src)
    loop = video.encode_loop(ep, d / "work")
    long = d / "long.mp4"
    video.build_long(ep, loop, aud, LOOP_S * REPEATS, long)
    return d, src, aud, ep, loop, long


def test_encode_loop(env):
    _, src, _, _, loop, _ = env
    s = vstream(loop)
    assert (s["width"], s["height"], s["pix_fmt"]) == (1920, 1080, "yuv420p")
    assert s["nb_frames"] == vstream(src)["nb_frames"]
    assert all(x["codec_type"] == "video" for x in probe(loop)["streams"])


def test_build_long_copy(env):
    _, _, _, _, loop, long = env
    assert abs(duration(long) - LOOP_S * REPEATS) <= 1 / 30 + 0.02
    assert int(vstream(long)["nb_frames"]) == REPEATS * int(vstream(loop)["nb_frames"])
    assert vstream(long)["codec_name"] == "h264"
    assert any(s["codec_type"] == "audio" for s in probe(long)["streams"])


def test_seam_ssim(env):
    d, _, _, _, loop, long = env
    n = int(vstream(loop)["nb_frames"])
    stats = d / "ssim.txt"

    def pair(a):
        return f"trim=start_frame={a}:end_frame={a + 2 * n},setpts=PTS-STARTPTS,scale=480:270"

    graph = f"[0:v]{pair(0)}[a];[0:v]{pair(1)}[b];[a][b]ssim=stats_file={stats}"
    ffmpeg("-i", long, "-filter_complex", graph, "-f", "null", "-")
    ss = [float(m) for m in re.findall(r"All:([\d.]+)", stats.read_text())]
    neighbours = [ss[i] for i in (n - 3, n - 2, n, n + 1)]
    assert ss[n - 1] >= min(neighbours) - 0.02, (ss[n - 1], neighbours)


def test_pomodoro(env):
    d, src, aud, ep, loop, long = env
    pomo = {"work_min": 1 / 60, "break_min": 2 / 60, "work_label": "Focus", "break_label": "Break"}
    pep = make_ep(d, src, overlay="pomodoro", pomodoro=pomo)
    out = d / "pomo.mp4"
    video.build_long(pep, loop, aud, LOOP_S * REPEATS, out)
    assert abs(duration(out) - LOOP_S * REPEATS) <= 0.1
    crop = "700:300:60:60"
    base, with_overlay = frame(long, 0.5, crop), frame(out, 0.5, crop)
    assert np.abs(base - with_overlay).mean() > 3
    # faz değişince (work -> break) overlay değişir; arka plan t+4 sn'de aynı
    assert np.abs(frame(out, 0.5, crop) - frame(out, 4.5, crop)).mean() > 1


def test_watermark(env):
    d, src, _, _, loop, _ = env
    wm = d / "wm.png"
    ffmpeg("-f", "lavfi", "-i", "color=red:s=200x100", "-frames:v", 1, wm)
    wep = make_ep(d, src, watermark={"file": str(wm), "position": "bottom-right", "opacity": 0.8})
    out = video.encode_loop(wep, d / "wm_work")
    corner = "300:200:iw-300:ih-200"
    assert np.abs(frame(out, 1, corner) - frame(loop, 1, corner)).mean() > 5
    tl = "300:200:0:0"
    assert np.abs(frame(out, 1, tl) - frame(loop, 1, tl)).mean() < 2
