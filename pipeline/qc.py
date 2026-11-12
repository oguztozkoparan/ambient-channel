"""output/<slug> için ölçülebilir QC kontrolleri -> qc.json ({check, value, threshold, pass})."""

import json
import re
import statistics
from pathlib import Path

import numpy as np

from pipeline import ffmpeg
from pipeline.config import _load

LICENSES = Path("assets/audio/LICENSES.md")
EPISODES = Path("episodes")


def _check(name: str, value: object, threshold: str, ok: bool) -> dict:
    return {"check": name, "value": value, "threshold": threshold, "pass": bool(ok)}


def _loudness(long: Path, build: dict) -> list[dict]:
    log = ffmpeg.ffmpeg(
        *["-t", 600, "-i", long, "-vn", "-af", "ebur128=peak=true:framelog=verbose"],
        *["-f", "null", "-"],
        loglevel="info",
    )
    summary = log[log.rindex("Summary:") :]
    integrated = float(re.search(r"I:\s+(-?[\d.]+) LUFS", summary)[1])
    peak = float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", summary)[1])
    target = build["target_lufs"]
    return [
        _check(
            "loudness_integrated_lufs", integrated, f"{target} ±1", abs(integrated - target) <= 1
        ),
        _check("true_peak_dbtp", peak, "<= -1.0", peak <= -1.0),
    ]


def _seam_visual(long: Path, build: dict, work: Path) -> dict:
    loop = build["loop_s"]
    if build["total_s"] < 2 * loop - 1e-6:
        return _check("seam_visual_ssim_drop", None, "tek loop, dikiş yok", True)
    stats = work / "qc_ssim.log"
    graph = (
        "[0:v]split[a][b];[b]trim=start_frame=1,setpts=PTS-STARTPTS[b1];"
        f"[a][b1]ssim=shortest=1:stats_file={stats}"
    )
    # ilk loop sınırının ±1 sn'sindeki ardışık frame çiftleri
    ffmpeg.ffmpeg("-ss", loop - 1, "-t", 2, "-i", long, "-an", "-lavfi", graph, "-f", "null", "-")
    values = [float(v) for v in re.findall(r"All:([\d.]+)", stats.read_text())]
    drop = round(statistics.median(values) - min(values), 4)
    return _check("seam_visual_ssim_drop", drop, "< 0.02", drop < 0.02)


def _seam_audio(long: Path, build: dict, work: Path) -> dict:
    loop = build["loop_s"]
    if build["total_s"] < 2 * loop - 1e-6:
        return _check("seam_audio_rms_jump_db", None, "tek loop, dikiş yok", True)
    raw = work / "qc_seam.f32"
    ffmpeg.ffmpeg(
        *["-ss", loop - 0.05, "-t", 0.1, "-i", long, "-vn"],
        *["-ac", 1, "-ar", 48000, "-f", "f32le", raw],
    )
    samples = np.fromfile(raw, dtype=np.float32)
    before, after = np.array_split(samples, 2)
    rms = [20 * np.log10(max(float(np.sqrt(np.mean(x**2))), 1e-9)) for x in (before, after)]
    jump = round(abs(rms[1] - rms[0]), 2)
    # shortcut: yalnızca RMS sıçraması; click tespiti yok, gerekirse örnek-farkı eşiği ekle
    return _check("seam_audio_rms_jump_db", jump, "< 3", jump < 3)


def _sleep(build: dict) -> list[dict]:
    if build["use_case"] != "sleep" or build["max_event_peak_db"] is None:
        return []
    over = round(build["max_event_peak_db"] - build["bed_rms_db"], 2)
    return [_check("sleep_event_peak_over_bed_db", over, "<= 10", over <= 10)]


def _short(short: Path) -> list[dict]:
    info = ffmpeg.probe(short)
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    size = f"{video['width']}x{video['height']}"
    dur = round(float(info["format"]["duration"]), 2)
    return [
        _check("short_resolution", size, "1080x1920", size == "1080x1920"),
        _check("short_duration_s", dur, "20–45", 20 <= dur <= 45),
    ]


def _words(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def _metadata(meta: dict) -> list[dict]:
    build = meta["build"]
    title = _words(meta["title"])
    # shortcut: "son 20" yerine tüm diğer episode'lar; episode'lara tarih alanı gelirse sırala
    others = [
        _load(p)
        for p in sorted(EPISODES.glob("*/episode.yaml"))
        if not p.parent.name.startswith("_")
    ]
    overlap = max(
        (
            len(title & _words(o.get("title", ""))) / max(len(title), 1)
            for o in others
            if o.get("slug") != meta["slug"]
        ),
        default=0.0,
    )
    checks = [
        _check("title_word_overlap", round(overlap, 2), "<= 0.70", overlap <= 0.70),
        _check(
            "description_filled",
            len(meta["description"]),
            "> 3 karakter",
            len(meta["description"].strip(" .\n")) > 3,
        ),
        _check("chapters_filled", len(meta["chapters"]), ">= 1", len(meta["chapters"]) >= 1),
    ]
    if not build["duration_overridden"]:
        nominal = build["nominal_duration_s"]
        hours = f"{nominal / 3600:g}"
        numbers = re.findall(r"\d+(?:\.\d+)?", meta["title"])
        ok = not numbers or hours in numbers
        checks.append(_check("title_duration_consistent", numbers, f"{hours} saat", ok))
        # "HH:MM:SS" / "MM:SS" -> sn; chapter videonun dışına düşmemeli
        stamps = [
            sum(float(x) * 60**i for i, x in enumerate(reversed(c["t"].split(":"))))
            for c in meta["chapters"]
        ]
        late = [c["t"] for c, t in zip(meta["chapters"], stamps, strict=True) if t >= nominal]
        checks.append(_check("chapters_within_duration", late, "süreyi aşan chapter yok", not late))
    footer = build["description_footer"].strip()
    if footer:
        ok = meta["description"].rstrip().endswith(footer)
        checks.append(_check("description_footer", ok, "brand footer ile biter", ok))
    return checks


def _licenses(build: dict) -> dict:
    rows = [
        line.split("|")[1].strip(" `") for line in LICENSES.read_text().splitlines() if "|" in line
    ]
    missing = sorted({Path(f).name for f in build["audio_files"]} - set(rows))
    return _check("audio_licenses_recorded", missing, "eksik dosya yok", not missing)


def run(out: Path) -> int:
    meta = json.loads((out / "metadata.json").read_text())
    build = meta["build"]
    long, short, work = out / "long.mp4", out / "short.mp4", out / "work"
    work.mkdir(exist_ok=True)

    measured = round(ffmpeg.duration(long), 2)
    target = build["target_duration_s"]
    # 20 ms: kap süresi yuvarlaması
    checks = [_check("long_duration_s", measured, f">= {target:g}", measured >= target - 0.02)]
    checks += _loudness(long, build)
    checks += [_seam_visual(long, build, work), _seam_audio(long, build, work)]
    checks += _sleep(build)
    checks += _short(short)
    checks += _metadata(meta)
    checks.append(_licenses(build))

    (out / "qc.json").write_text(json.dumps(checks, indent=2, ensure_ascii=False) + "\n")
    for c in checks:
        print(f"{'pass' if c['pass'] else 'FAIL'}  {c['check']}: {c['value']} ({c['threshold']})")
    failed = [c["check"] for c in checks if not c["pass"]]
    print(f"{out}/qc.json: " + ("tüm kontroller pass" if not failed else f"FAIL: {failed}"))
    return 1 if failed else 0
