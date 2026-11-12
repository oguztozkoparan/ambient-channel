from pathlib import Path

from pipeline.ffmpeg import _out_time_s, ffmpeg


def test_out_time_reads_last_value(tmp_path: Path):
    state = tmp_path / "progress"
    assert _out_time_s(state) == 0.0  # file not written yet
    state.write_text("out_time_us=N/A\nprogress=continue\nout_time_us=1500000\nprogress=continue\n")
    assert _out_time_s(state) == 1.5


def test_ffmpeg_with_progress_reports_and_returns(tmp_path: Path, capsys):
    out = tmp_path / "tone.wav"
    ffmpeg("-f", "lavfi", "-i", "sine=d=2", out, progress=("test step", 2.0))
    assert out.stat().st_size > 0
    err = capsys.readouterr().err
    assert "test step" in err and "100%" in err
