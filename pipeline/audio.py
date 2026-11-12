"""Ses pipeline'ı: bed + seed'li event'ler, chunk'lı render, two-pass loudnorm."""

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf

from pipeline.config import Episode, event_files
from pipeline.ffmpeg import ffmpeg
from pipeline.progress import Progress

SR = 48000
CHUNK_S = 30
CROSSFADE_S = 3.0  # bed loop dikişi; bed'in dörtte birinden uzun olamaz
FADE_S = 0.01  # event kenarlarında tık önleyici
# shortcut: bed RMS ilk 10 dk'dan ölçülür; bed'ler periyodik olduğundan yeterli
BED_RMS_WINDOW_S = 600
SLEEP_EVENT_HEADROOM_DB = 10.0


@dataclass
class EventHit:
    t: float
    duration: float
    gain_db: float
    peak_db: float
    file: str


@dataclass
class AudioResult:
    path: Path
    events: list[EventHit]
    bed_rms_db: float
    files: list[str]


def _db(x: float) -> float:
    return 20 * math.log10(max(x, 1e-9))


def _load(src: Path, work: Path) -> np.ndarray:
    """Kaynağı 48 kHz stereo float32'ye çevirip okur."""
    if not src.is_file():
        raise FileNotFoundError(f"ses dosyası bulunamadı: {src}")
    wav = work / f"src_{hashlib.sha1(str(src.resolve()).encode()).hexdigest()[:12]}.wav"
    ffmpeg("-i", src, "-ar", SR, "-ac", 2, "-c:a", "pcm_f32le", wav)
    data, _ = sf.read(wav, dtype="float32", always_2d=True)
    wav.unlink()
    return data


def _loop_unit(x: np.ndarray, fade: int) -> np.ndarray:
    """Kuyruğu başa equal-power crossfade ile bağlar; birim kendi üzerine seamless döner."""
    fade = min(fade, len(x) // 4)
    if fade < 1:
        raise ValueError("bed çok kısa: loop crossfade için en az 4 örnek gerekir")
    theta = np.linspace(0, np.pi / 2, fade, dtype=np.float32)[:, None]
    head = x[:fade] * np.sin(theta) + x[len(x) - fade :] * np.cos(theta)
    return np.concatenate([head, x[fade : len(x) - fade]])


def _bed_chunk(units: list[tuple[np.ndarray, float]], start: int, n: int) -> np.ndarray:
    idx = np.arange(start, start + n)
    out = np.zeros((n, 2), dtype=np.float32)
    for unit, gain in units:
        out += np.take(unit, idx, axis=0, mode="wrap") * np.float32(gain)
    return out


def _prep_event(x: np.ndarray) -> np.ndarray:
    x = x.copy()
    f = min(int(FADE_S * SR), len(x) // 2)
    if f:
        ramp = np.linspace(0, 1, f, dtype=np.float32)[:, None]
        x[:f] *= ramp
        x[len(x) - f :] *= ramp[::-1]
    return x


def _plan_events(ep: Episode, work: Path, total: int, bed_rms_db: float):
    """Tüm event'leri baştan planlar (chunk'tan bağımsız). [(start_frame, src, scale, EventHit)]."""
    plan = []
    cache: dict[Path, np.ndarray] = {}
    if ep.event_density <= 0:
        return plan
    for i, spec in enumerate(ep.audio.events):
        files = event_files(spec.file)
        if not files:
            raise FileNotFoundError(f"event glob'u dosya bulamadı: {spec.file}")
        rng = np.random.default_rng([ep.seed, i])
        t = 0.0
        while True:
            t += rng.uniform(*spec.every_s) / ep.event_density
            start = round(t * SR)
            if start >= total:
                break
            f = files[int(rng.integers(len(files)))]
            gain = float(rng.uniform(*spec.gain_db))
            pan = float(rng.uniform(-spec.pan_jitter, spec.pan_jitter))
            if f not in cache:
                cache[f] = _prep_event(_load(f, work))
            src = cache[f]
            ang = (pan + 1) * np.pi / 4
            lr = np.array([np.cos(ang), np.sin(ang)], dtype=np.float32) * np.float32(math.sqrt(2))
            if not spec.pan_jitter:
                lr = np.ones(2, dtype=np.float32)
            gain = min(gain, ep.event_max_gain_db)
            p0 = _db(float((np.abs(src).max(axis=0) * lr).max()))
            if ep.use_case == "sleep":
                gain = min(gain, bed_rms_db + SLEEP_EVENT_HEADROOM_DB - p0)
            hit = EventHit(start / SR, len(src) / SR, gain, p0 + gain, str(f))
            # örnekler kopyalanmaz, ölçek mix anında uygulanır: 10 saatte yüzlerce event var
            plan.append((start, src, lr * np.float32(10 ** (gain / 20)), hit))
    plan.sort(key=lambda p: p[0])
    return plan


def _loudnorm(ep: Episode, raw: Path, out: Path, duration_s: float) -> None:
    a = ep.audio
    base = f"loudnorm=I={a.target_lufs}:TP={a.true_peak}"
    log = ffmpeg(
        *["-i", raw, "-af", f"{base}:print_format=json", "-f", "null", "-"],
        loglevel="info",
        progress=("loudnorm 1/2", duration_s),
    )
    m = json.loads(log[log.rindex("{") : log.rindex("}") + 1])
    # hedef LRA >= ölçülen LRA: aksi hâlde loudnorm linear yerine dinamik (pompalayan) moda düşer
    lra = min(max(math.ceil(float(m["input_lra"])), 1), 50)
    second = (
        f"{base}:LRA={lra}:measured_I={m['input_i']}:measured_LRA={m['input_lra']}"
        f":measured_TP={m['input_tp']}:measured_thresh={m['input_thresh']}"
        f":offset={m['target_offset']}:linear=true"
    )
    ffmpeg(
        *["-i", raw, "-af", second, "-ar", SR, "-ac", 2, "-c:a", "aac", "-b:a", "192k", out],
        progress=("loudnorm 2/2", duration_s),
    )


def render(ep: Episode, work: Path, duration_s: float) -> AudioResult:
    work.mkdir(parents=True, exist_ok=True)
    units = [
        (_loop_unit(_load(b.file, work), int(CROSSFADE_S * SR)), 10 ** (b.gain_db / 20))
        for b in ep.audio.beds
    ]
    total = math.ceil(duration_s * SR)

    probe = _bed_chunk(units, 0, min(total, BED_RMS_WINDOW_S * SR))
    bed_rms_db = 10 * math.log10(max(float(np.mean(probe.astype(np.float64) ** 2)), 1e-18))
    del probe

    plan = _plan_events(ep, work, total, bed_rms_db)
    raw = work / "audio_raw.w64"
    bar = Progress("audio render")
    with sf.SoundFile(raw, "w", SR, 2, format="W64", subtype="FLOAT") as w:
        for c0 in range(0, total, CHUNK_S * SR):
            n = min(CHUNK_S * SR, total - c0)
            buf = _bed_chunk(units, c0, n)
            for start, src, scale, _ in plan:
                a, b = max(start, c0), min(start + len(src), c0 + n)
                if a < b:
                    buf[a - c0 : b - c0] += src[a - start : b - start] * scale
            w.write(buf)
            bar.update((c0 + n) / total)
    bar.done()

    out = work / "audio.m4a"
    try:
        _loudnorm(ep, raw, out, total / SR)
    finally:
        raw.unlink(missing_ok=True)
    hits = [h for *_, h in plan]
    files = sorted({str(b.file) for b in ep.audio.beds} | {h.file for h in hits})
    return AudioResult(out, hits, bed_rms_db, files)
