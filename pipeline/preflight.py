"""Input check before a build: lists every missing file at once instead of failing one by one."""

from pathlib import Path

from pipeline.config import Episode, event_files


def problems(ep: Episode) -> list[str]:
    found: list[str] = []

    def need(path: Path | None, what: str) -> None:
        if path and not path.is_file():
            found.append(f"{what}: {path}")

    need(ep.visual.clip_16x9, "16:9 loop clip (Unity render)")
    need(ep.visual.clip_9x16, "9:16 loop clip (Unity render, or remove visual.clip_9x16)")
    for bed in ep.audio.beds:
        need(bed.file, "audio bed")
    for event in ep.audio.events:
        if not event_files(event.file):
            found.append(f"audio event (no file matches): {event.file}")
    need(ep.short.font, "Short font")
    need(ep.watermark.file, "watermark")
    if ep.overlay == "pomodoro" and not ep.pomodoro:
        found.append("overlay: pomodoro needs a `pomodoro` block (config/use_cases.yaml)")
    return found
