"""Short: 1080x1920, event yoğun pencereden ses, hook/line2/CTA metni, fade in/out."""

import textwrap
from pathlib import Path
from typing import TYPE_CHECKING

from pipeline.config import Episode
from pipeline.ffmpeg import duration, ffmpeg
from pipeline.video import fesc, watermark_graph

if TYPE_CHECKING:
    from pipeline.audio import AudioResult

W, H = 1080, 1920
FADE_S = 0.5
HOOK_S = 2.0
CTA_S = 3.0
WRAP = 18  # satır başına karakter (punto oranıyla birlikte 1080 genişliğe sığar)
HOOK_SIZE, LINE2_SIZE, CTA_SIZE = 80, 56, 52
LINE_SPACING = 12


def pick_window(starts: list[float], audio_len: float, dur: float) -> float:
    """En çok event başlangıcı içeren [s, s+dur) penceresi; eşitlikte en erken."""
    last = max(0.0, audio_len - dur)
    cands = sorted({0.0, *(min(t, last) for t in starts)})
    best, best_n = 0.0, -1
    for s in cands:
        n = sum(s <= t < s + dur for t in starts)
        if n > best_n:
            best, best_n = s, n
    return best


def build_short(ep: Episode, audio: "AudioResult", out: Path, work: Path) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    dur = ep.short.duration_s
    start = pick_window([e.t for e in audio.events], duration(audio.path), dur)

    sh = ep.short
    texts = [("hook", sh.hook, HOOK_SIZE, "h*0.16", f"lt(t,{HOOK_S:g})")]
    if sh.line2:
        # line2, hook'un gerçek satır sayısının altına yerleşir (uzun hook'ta üst üste binmesin)
        hook_h = (textwrap.fill(sh.hook, WRAP).count("\n") + 1) * (HOOK_SIZE + LINE_SPACING)
        texts.append(("line2", sh.line2, LINE2_SIZE, f"h*0.16+{hook_h + 50}", f"lt(t,{HOOK_S:g})"))
    texts.append(("cta", sh.cta, CTA_SIZE, "h*0.78", f"gte(t,{dur - CTA_S:g})"))

    chain = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"
    wm = ep.watermark.file
    graph = f"[0:v]{chain}[b0];" + (
        watermark_graph(ep, "b0", 2, "b1") + ";" if wm else "[b0]null[b1];"
    )
    draws = []
    for name, text, size, y, enable in texts:
        f = work / f"short_{name}.txt"
        f.write_text(textwrap.fill(text, WRAP))  # metin dosyadan: ':' ve "'" kaçışı gerekmez
        draws.append(
            f"drawtext=textfile='{fesc(f)}':fontfile='{fesc(sh.font)}':fontsize={size}"
            f":fontcolor={sh.text_color}:borderw=4:bordercolor={sh.outline_color}"
            f":line_spacing={LINE_SPACING}:text_align=C:x=(w-text_w)/2:y={y}:enable='{enable}'"
        )
    graph += (
        f"[b1]{','.join(draws)},fade=t=in:d={FADE_S},fade=t=out:st={dur - FADE_S:g}:d={FADE_S}[v];"
        f"[1:a]afade=t=in:d={FADE_S},afade=t=out:st={dur - FADE_S:g}:d={FADE_S}[a]"
    )
    clip = ep.visual.clip_9x16 or ep.visual.clip_16x9
    inputs = ["-stream_loop", -1, "-i", clip, "-ss", start, "-t", dur, "-i", audio.path]
    if wm:
        inputs += ["-i", wm]
    ffmpeg(
        *inputs, "-filter_complex", graph, "-map", "[v]", "-map", "[a]", "-t", dur,
        "-c:v", "libx264", "-crf", ep.visual.crf, "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", out,
    )  # fmt: skip
    return {"audio_start_s": start}
