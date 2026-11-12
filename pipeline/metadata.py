"""metadata.json (upload texts + build record) and events.json."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

from pipeline.config import Episode

if TYPE_CHECKING:
    from pipeline.audio import AudioResult


def write(
    ep: Episode,
    episode_dir: Path,
    out: Path,
    rendered: "AudioResult",
    loop_s: float,
    total_s: float,
    short_info: dict,
) -> None:
    footer = ep.description_footer.strip()
    peaks = [e.peak_db for e in rendered.events]
    meta = {
        "slug": ep.slug,
        "title": ep.title,
        "description": ep.description.strip() + (f"\n\n{footer}" if footer else ""),
        "tags": list(dict.fromkeys([*ep.tags, *ep.default_tags])),
        "chapters": [c.model_dump() for c in ep.chapters],
        "language": ep.channel.language,
        "disclosure": ep.disclosure.model_dump(),
        "short": {"hook": ep.short.hook, "line2": ep.short.line2, "cta": ep.short.cta},
        "build": {
            "episode_dir": str(episode_dir),
            "use_case": ep.use_case,
            "variant_of": ep.variant_of,
            "seed": ep.seed,
            "target_duration_s": ep.duration_s,
            "nominal_duration_s": ep.nominal_duration_s,
            "duration_overridden": ep.duration_overridden,
            "loop_s": loop_s,
            "total_s": total_s,
            "target_lufs": ep.audio.target_lufs,
            "true_peak": ep.audio.true_peak,
            "overlay": ep.overlay,
            "description_footer": ep.description_footer,
            "audio_files": rendered.files,
            "bed_rms_db": rendered.bed_rms_db,
            "event_count": len(rendered.events),
            "max_event_peak_db": max(peaks) if peaks else None,
            "short_audio_start_s": short_info["audio_start_s"],
        },
    }
    # no timestamp: same config + seed = same file
    (out / "metadata.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
    events = [asdict(e) for e in rendered.events]
    (out / "events.json").write_text(json.dumps(events, indent=2) + "\n")
