"""Long video: loop'u bir kez encode et, concat + -c copy ile uzat, sesi mux et."""

import sys
import time
from pathlib import Path

from pipeline.config import Episode
from pipeline.ffmpeg import duration, ffmpeg, probe

W, H = 1920, 1080
WM_MARGIN = 40
POMO_SIZE = 72  # overlay punto/konum oranları: layout sabiti, marka değil
POMO_MARGIN = 60


def fesc(value: object) -> str:
    """Filter argümanı için kaçış (yol/metin): \\ ' ve : ."""
    return str(value).replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:")


def watermark_graph(ep: Episode, src: str, wm_input: int, out: str) -> str:
    """`src` etiketine logo bindirir (wm_input: logo girdi indeksi); filter_complex parçası."""
    v, h = ep.watermark.position.split("-")
    x = f"x={WM_MARGIN}" if h == "left" else f"x=W-w-{WM_MARGIN}"
    y = f"y={WM_MARGIN}" if v == "top" else f"y=H-h-{WM_MARGIN}"
    return (
        f"[{wm_input}:v]format=rgba,colorchannelmixer=aa={ep.watermark.opacity}[wm];"
        f"[{src}][wm]overlay={x}:{y}:format=auto[{out}]"
    )


def _frames(clip: Path) -> int:
    s = next(s for s in probe(clip)["streams"] if s["codec_type"] == "video")
    if s.get("nb_frames", "N/A").isdigit():
        return int(s["nb_frames"])
    num, den = map(int, s["r_frame_rate"].split("/"))
    return round(float(s.get("duration") or duration(clip)) * num / den)


def encode_loop(ep: Episode, work: Path) -> Path:
    work.mkdir(parents=True, exist_ok=True)
    out = work / "loop.mp4"
    clip = ep.visual.clip_16x9
    scale = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,format=yuv420p"
    )
    wm = ep.watermark.file
    inputs: list[object] = ["-i", clip]
    if wm:
        inputs += ["-i", wm]
        graph = f"[0:v]{scale}[b];" + watermark_graph(ep, "b", 1, "v")
    else:
        graph = f"[0:v]{scale}[v]"
    ffmpeg(
        *inputs, "-filter_complex", graph, "-map", "[v]", "-an",
        "-c:v", "libx264", "-crf", ep.visual.crf, "-pix_fmt", "yuv420p",
        # -bf 0: B-frame gecikmesi/edit list olmadan her tekrar tam N frame ve temiz pts verir
        "-bf", 0, "-g", _frames(clip), "-sc_threshold", 0, "-flags", "+cgop",
        "-movflags", "+faststart", out,
    )  # fmt: skip
    return out


def _concat_list(loop: Path, repeats: int, path: Path) -> Path:
    path.write_text("".join(f"file '{loop.resolve()}'\n" for _ in range(repeats)))
    return path


def _pomodoro_filter(ep: Episode, work: Path) -> str:
    p, s = ep.pomodoro, ep.short
    assert p, "overlay=pomodoro için pomodoro config'i gerekli"
    wsec, cyc = p.work_min * 60, (p.work_min + p.break_min) * 60
    ph = f"mod(t,{cyc:g})"
    style = (
        f"fontfile='{fesc(s.font)}':fontsize={POMO_SIZE}:fontcolor={s.text_color}"
        f":borderw=3:bordercolor={s.outline_color}"
    )
    parts = []
    for name, label, rem, en in (
        ("work", p.work_label, f"ceil({wsec:g}-{ph})", f"lt({ph},{wsec:g})"),
        ("break", p.break_label, f"ceil({cyc:g}-{ph})", f"gte({ph},{wsec:g})"),
    ):
        (work / f"pomo_{name}_label.txt").write_text(label)
        # textfile'da %{eif} açılımı çalışır; ':' kaçışsız yazılır
        (work / f"pomo_{name}_time.txt").write_text(
            f"%{{eif:floor({rem}/60):d:2}}:%{{eif:mod({rem},60):d:2}}"
        )
        for kind, y in (
            ("label", f"y={POMO_MARGIN}"),
            ("time", f"y={POMO_MARGIN + POMO_SIZE + 10}"),
        ):
            f = fesc(work / f"pomo_{name}_{kind}.txt")
            parts.append(f"drawtext=textfile='{f}':{style}:x={POMO_MARGIN}:{y}:enable='{en}'")
    return ",".join(parts)


def _encoders(ep: Episode) -> list[list[object]]:
    crf = ep.visual.crf
    # shortcut: VideoToolbox'ta CRF yok, sabit bitrate; kalite yetmezse config'e bitrate alanı ekle
    hw = [["-c:v", "h264_videotoolbox", "-b:v", "8M"], ["-c:v", "h264_nvenc", "-cq", crf]]
    return [*hw, ["-c:v", "libx264", "-crf", crf]]


def build_long(ep: Episode, loop: Path, audio: Path, total_s: float, out: Path) -> None:
    loop_s = duration(loop)
    repeats = round(total_s / loop_s)
    out.parent.mkdir(parents=True, exist_ok=True)
    work = out.parent / "work"
    work.mkdir(exist_ok=True)
    lst = _concat_list(loop, repeats, work / "concat.txt")
    src = ["-f", "concat", "-safe", 0, "-i", lst, "-i", audio]
    tail = ["-map", "0:v", "-map", "1:a", "-c:a", "copy", "-t", total_s, "-movflags", "+faststart"]
    try:
        if ep.overlay == "none":
            ffmpeg(*src, *tail, "-c:v", "copy", out)
            return
        vf = _pomodoro_filter(ep, work)
        t0, errs = time.monotonic(), []
        for enc in _encoders(ep):
            try:
                ffmpeg(*src, "-vf", vf, *enc, "-pix_fmt", "yuv420p", *tail, out)
                break
            except RuntimeError as e:
                errs.append(str(e))
        else:
            raise RuntimeError("tüm encoder'lar başarısız:\n" + "\n".join(errs))
        el = time.monotonic() - t0
        print(
            f"pomodoro tam encode ({enc[1]}): {el:.1f} sn, gerçek zamanın {total_s / el:.1f}x'i",
            file=sys.stderr,
        )
    finally:
        lst.unlink(missing_ok=True)
