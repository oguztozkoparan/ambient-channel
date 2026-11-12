---
name: qc-checklist
description: Measurable QC checks and commands for episode output. Use for QC, verification or "is the video ready" questions.
user-invocable: false
---
`uv run python -m pipeline qc output/<slug>` runs the measurable checks and writes `{check, value, threshold, pass}` to `output/<slug>/qc.json`; qc.json is never written by hand. The list below is the full spec. Items the command cannot measure (pomodoro phase change, hook/CTA visibility, text language, watermark, click) are verified by hand by the reviewer: extract a frame at the relevant moment with `ffmpeg -ss <t> -frames:v 1` and look at it.

- Duration: `ffprobe -v error -show_entries format=duration -of csv=p=0 long.mp4` ≥ target.
- Loudness: `ffmpeg -hide_banner -nostats -i long.mp4 -t 600 -af ebur128=peak=true:framelog=verbose -f null -` → integrated target ±1 LU, true peak ≤ -1.0 dBTP.
- Loop seam (visual): extract frames from ±1 s around the loop boundary; the SSIM drop between consecutive frames must be < 0.02.
- Loop seam (audio): RMS jump < 3 dB in a ±50 ms window around the boundary, no click.
- use_case: the duration and LUFS target are resolved from `config/use_cases.yaml` + episode overrides. `sleep`: no event peak above the bed RMS by more than +10 dB. `focus`: pomodoro phase changes match the minutes in config within ±1 s.
- Short spec: 1080x1920, 20–45 s, hook visible within 0–2 s, CTA in the last 3 s.
- Thumbnail: `thumbnail.jpg` is 1280x720 and at most 2 MB.
- Metadata: the title has no more than 70% word overlap with any of the last 20 episodes; description and chapters are filled; the duration in the title matches the real duration; no chapter exceeds the video duration.
- Brand: texts are in the `config/brand.yaml` `channel.language` language; the description ends with `metadata.description_footer`; the Short CTA comes from the `short.cta` template (or the episode override); if `watermark.file` is set, it is visible in the long and the short.
- Audio sources: every file used is recorded in `assets/audio/LICENSES.md`.
- Trial builds (`build.trial: true` in `metadata.json`): synthetic inputs and a shortened duration are intended; the title-duration, chapter and audio-license checks are skipped. A trial that passes proves the flow, not the episode: it is never uploaded.
