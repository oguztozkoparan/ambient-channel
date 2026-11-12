"""Measurable QC checks for output/<slug> -> qc.json ({check, value, threshold, pass})."""

import json
import re
import statistics
from pathlib import Path

import numpy as np

from pipeline import ffmpeg
from pipeline.config import CONFIG, _load

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
        return _check("seam_visual_ssim_drop", None, "single loop, no seam", True)
    stats = work / "qc_ssim.log"
    graph = (
        "[0:v]split[a][b];[b]trim=start_frame=1,setpts=PTS-STARTPTS[b1];"
        f"[a][b1]ssim=shortest=1:stats_file={stats}"
    )
    # consecutive frame pairs within ±1 s of the first loop boundary
    ffmpeg.ffmpeg("-ss", loop - 1, "-t", 2, "-i", long, "-an", "-lavfi", graph, "-f", "null", "-")
    values = [float(v) for v in re.findall(r"All:([\d.]+)", stats.read_text())]
    drop = round(statistics.median(values) - min(values), 4)
    return _check("seam_visual_ssim_drop", drop, "< 0.02", drop < 0.02)


def _seam_audio(long: Path, build: dict, work: Path) -> dict:
    loop = build["loop_s"]
    if build["total_s"] < 2 * loop - 1e-6:
        return _check("seam_audio_rms_jump_db", None, "single loop, no seam", True)
    raw = work / "qc_seam.f32"
    ffmpeg.ffmpeg(
        *["-ss", loop - 0.05, "-t", 0.1, "-i", long, "-vn"],
        *["-ac", 1, "-ar", 48000, "-f", "f32le", raw],
    )
    samples = np.fromfile(raw, dtype=np.float32)
    before, after = np.array_split(samples, 2)
    rms = [20 * np.log10(max(float(np.sqrt(np.mean(x**2))), 1e-9)) for x in (before, after)]
    jump = round(abs(rms[1] - rms[0]), 2)
    # shortcut: RMS jump only; no click detection, add a sample-diff threshold if needed
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


def _thumbnail(path: Path) -> dict:
    if not path.is_file():
        return _check("thumbnail", None, "1280x720, <= 2 MB", False)
    image = ffmpeg.probe(path)["streams"][0]
    value = f"{image['width']}x{image['height']}, {path.stat().st_size / 1e6:.2f} MB"
    ok = (image["width"], image["height"]) == (1280, 720) and path.stat().st_size <= 2_000_000
    return _check("thumbnail", value, "1280x720, <= 2 MB", ok)


def _words(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def _metadata(meta: dict) -> list[dict]:
    build = meta["build"]
    # the use-case suffix and the duration number are shared by design, not repetition
    suffixes = (uc.get("title_suffix", "") for uc in _load(CONFIG / "use_cases.yaml").values())
    boilerplate = set().union(*map(_words, suffixes))

    def scene(text: str) -> set[str]:
        return {w for w in _words(text) if w not in boilerplate and not w.isdigit()}

    title = scene(meta["title"])
    # shortcut: all other episodes instead of "last 20"; sort if episodes get a date field
    others = [
        _load(p)
        for p in sorted(EPISODES.glob("*/episode.yaml"))
        if not p.parent.name.startswith("_")
    ]
    overlap = max(
        (
            len(title & scene(o.get("title", ""))) / max(len(title), 1)
            for o in others
            if o.get("slug") != meta["slug"]
            # a variant shares its source's scene by design
            and o.get("slug") != build.get("variant_of")
            and o.get("variant_of") != meta["slug"]
        ),
        default=0.0,
    )
    checks = [
        _check("title_word_overlap", round(overlap, 2), "<= 0.70", overlap <= 0.70),
        _check(
            "description_filled",
            len(meta["description"]),
            "> 3 characters",
            len(meta["description"].strip(" .\n")) > 3,
        ),
        _check("chapters_filled", len(meta["chapters"]), ">= 1", len(meta["chapters"]) >= 1),
    ]
    if not build.get("trial"):  # a trial keeps full-length texts on a shortened video
        target = build["target_duration_s"]
        hours = f"{target / 3600:g}"
        numbers = re.findall(r"\d+(?:\.\d+)?", meta["title"])
        ok = not numbers or hours in numbers
        checks.append(_check("title_duration_consistent", numbers, f"{hours} hours", ok))
        # "HH:MM:SS" / "MM:SS" -> s; a chapter must not fall outside the video
        stamps = [
            sum(float(x) * 60**i for i, x in enumerate(reversed(c["t"].split(":"))))
            for c in meta["chapters"]
        ]
        late = [c["t"] for c, t in zip(meta["chapters"], stamps, strict=True) if t >= target]
        checks.append(_check("chapters_within_duration", late, "no chapter past end", not late))
    footer = build["description_footer"].strip()
    if footer:
        ok = meta["description"].rstrip().endswith(footer)
        checks.append(_check("description_footer", ok, "ends with brand footer", ok))
    return checks


def _licenses(build: dict) -> dict:
    rows = [
        line.split("|")[1].strip(" `") for line in LICENSES.read_text().splitlines() if "|" in line
    ]
    missing = sorted({Path(f).name for f in build["audio_files"]} - set(rows))
    return _check("audio_licenses_recorded", missing, "no missing files", not missing)


def run(out: Path) -> int:
    meta = json.loads((out / "metadata.json").read_text())
    build = meta["build"]
    long, short, work = out / "long.mp4", out / "short.mp4", out / "work"
    work.mkdir(exist_ok=True)

    measured = round(ffmpeg.duration(long), 2)
    target = build["target_duration_s"]
    # 20 ms: container duration rounding
    checks = [_check("long_duration_s", measured, f">= {target:g}", measured >= target - 0.02)]
    checks += _loudness(long, build)
    checks += [_seam_visual(long, build, work), _seam_audio(long, build, work)]
    checks += _sleep(build)
    checks += _short(short)
    checks.append(_thumbnail(out / "thumbnail.jpg"))
    checks += _metadata(meta)
    if not build.get("trial"):  # synthetic trial inputs have no license to record
        checks.append(_licenses(build))

    (out / "qc.json").write_text(json.dumps(checks, indent=2, ensure_ascii=False) + "\n")
    for c in checks:
        print(f"{'pass' if c['pass'] else 'FAIL'}  {c['check']}: {c['value']} ({c['threshold']})")
    if build.get("trial"):
        print("TRIAL build: synthetic inputs and/or shortened duration; not for upload")
    failed = [c["check"] for c in checks if not c["pass"]]
    print(f"{out}/qc.json: " + ("all checks pass" if not failed else f"FAIL: {failed}"))
    return 1 if failed else 0
