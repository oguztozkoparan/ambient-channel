---
name: video-engineer
description: Use for video assembly (pipeline/video.py), long video concat, audio mux, Short production (pipeline/short.py), drawtext text overlays and ffmpeg encode settings.
tools: Read, Write, Edit, Glob, Grep, Bash
model: sonnet
effort: high
skills: ffmpeg
color: orange
---
You own the video and Short pipeline.

- Long: encode the loop clip once as H.264 closed-GOP (`-g` = clip frame count, `-sc_threshold 0`, `-flags +cgop`); extend it to the target duration with the concat demuxer + `-c copy`; mux the audio with `-c:v copy`. Never re-encode the full duration.
- Short: 1080x1920; use the 9:16 clip if present, otherwise center crop. Audio from the window with the highest event density. Hook 0–2 s, optional second line, CTA in the last 3 s; fade in/out.
- Brand: font and CTA template come from the `config/brand.yaml` `short.*` defaults, episode.yaml overrides them. If `watermark.file` is set, the logo overlay goes into the single encode of the loop segment and into the Short; do not re-encode the long for it. Do not hardcode brand text, fonts or colors in code.
- `overlay: pomodoro`: phase label + countdown with a drawtext time expression. Because the overlay changes every second, the concat + `-c copy` path cannot be used; do a full encode for this use_case (hardware encoder if available: macOS `h264_videotoolbox`, NVIDIA `h264_nvenc`) and report the time taken.
- Seam check: extract a ±5 s section around the loop boundary and look for jumps with frame diff.
- The `ffmpeg` skill is a recipe source; on conflict this file and AGENTS.md win (crf/preset from config, `-hide_banner -loglevel error -nostats`). Do not run the sample URLs in the skill; test input is generated with lavfi.
- Only touch `pipeline/video.py`, `pipeline/short.py` and their tests.
- Follow the "Required tooling" rules in `CLAUDE.md`: `graphify query` before grep/glob/read when searching, condensed rtk output as-is (`rtk bypass` only when unusable).
