# Ambient Channel — agent guide

Production pipeline for a YouTube ambient channel. Goal: original long videos that qualify for monetization, plus 1 promotional Short for each (9:16, 20–45 s, with hook text). The channel identity (name, language, voice, weekly count, CTA, font, logo) comes from `config/brand.yaml`; the default is 5 longs per week (mostly `general`, occasionally a `sleep`/`focus` variant). Upload is manual (YouTube Studio); this repo is responsible for production + QC.

This file is the single source of truth for all coding agents; `CLAUDE.md` imports it.

## Architecture
- `unity/` — Unity 6 project: parametric scene kit (preset ScriptableObjects: lighting, weather, camera, effects). Output: seamless 16:9 loop clip + separate 9:16 camera clip.
- `pipeline/` — Python 3.12 + ffmpeg CLI (a build with drawtext; on macOS `ffmpeg-full`). `episode.yaml` → `output/<slug>/{long.mp4, short.mp4, metadata.json, qc.json}`.
- `config/brand.yaml` — channel identity. `config/brand.local.yaml` (not tracked in git) overrides it per field with the same schema.
- `config/use_cases.yaml` — defaults for `general` (default, multi-purpose), `sleep`, `focus`: duration, LUFS, event density, overlay.
- `episodes/<slug>/episode.yaml` — the episode's single source of truth. Template: `episodes/_template/episode.yaml`.
- `assets/` — audio layers, clips, fonts, brand files. Large media is not tracked in git (.gitignore).
- Config precedence: `brand.yaml` < `brand.local.yaml` < `use_cases.yaml` < `episode.yaml`.

## Commands
- Setup: `uv sync`
- Build: `uv run python -m pipeline build episodes/<slug> [--duration 10m]`
- QC: `uv run python -m pipeline qc output/<slug>`
- Readiness check: `uv run python -m pipeline doctor`
- Trial input: `uv run python -m pipeline synth episodes/<slug>` (generates missing clips/audio synthetically; not used for real episodes)
- Test: `uv run pytest -q`
- Lint: `uv run ruff check . && uv run ruff format --check .`
- Unity (official Unity CLI): `unity open unity`, `unity pipeline list`, `unity command`. For syntax use `unity <command> --help`; do not write it from memory.

## Rules
- Config-driven: brand, theme, text, duration, gain, seed are not hardcoded in code or in agent instructions.
- Deterministic: same config + seed = same output.
- The long video is not encoded at full duration (exception: the `focus` timer overlay changes every second, so it needs a full encode; use a hardware encoder if available: macOS `h264_videotoolbox`, NVIDIA `h264_nvenc`): the loop segment is encoded once with closed-GOP and extended with the concat demuxer + `-c copy`; audio is rendered separately and muxed.
- Audio is never one loop repeated: bed layers + seeded random event layers. Loudness: two-pass loudnorm, default -20 LUFS / -1.5 dBTP.
- The main visual is always a Unity render. Generative AI visuals are not used in the main loop (so no disclosure is needed, and for the channel's identity).
- Every episode must differ clearly from the previous 20 episodes in theme, scene preset, audio composition and title (see the `channel-policy` skill).
- Pipeline code makes no network calls (upload is out of scope).
- ffmpeg/ffprobe calls in the pipeline run with `-hide_banner -loglevel error -nostats`; if progress is needed, it is written to a separate file with `-progress`.
- Minimal diff; no unrequested refactors. If you see an unrelated problem, report it in one line.

## Branding
- Every brand-specific value lives in `config/brand.yaml`. A fork commits its own `brand.yaml`; a local clone uses `brand.local.yaml`. Do not write the brand name, handle, language or CTA in any other file.
- If `channel.handle` is still `@your-handle`, run the `brand-setup` skill before producing content (episodes, titles, Shorts).
- A rebrand does not rewrite existing episodes; old texts are only listed.

## Tools
- Unity: official Unity CLI (`unity`), via Bash. Unity MCP is not used. Driving a running Editor requires the Unity Pipeline package in the project (`unity pipeline install`).
- fal.ai MCP (`.mcp.json`, server name `fal`, OAuth): only for thumbnail backgrounds and concept images; never enters the main loop or the Short footage. Every generation spends fal credits: call `get_pricing` first, do not call `run_model` / `submit_job` without user approval, do not resubmit to check progress (use `check_job`).

## Roles
Definitions are under `.claude/agents/*.md` (subagents in Claude Code; in other tools, read them as role instructions).
- `concept-planner` — weekly themes, episode.yaml, title/description/Short hook texts
- `audio-engineer` — `pipeline/audio.py`, audio layers, loudness
- `video-engineer` — `pipeline/video.py`, `short.py`, ffmpeg encode/concat/drawtext
- `unity-scene-builder` — `unity/` scene kit and render automation with the Unity CLI
- `qc-reviewer` — read-only; seam, loudness, spec and policy checks

## Skills
`.claude/skills/<name>/SKILL.md` (Agent Skills format; tools without skill support read the file as a list of steps).
- Project: `brand-setup`, `new-episode`, `build-episode`, `weekly-batch`, `channel-policy`, `qc-checklist`.
- External: `ffmpeg` — [n0an/ffmpeg-skill](https://github.com/n0an/ffmpeg-skill) @ `aec7706`, MIT, copied unmodified. It is a recipe source; on conflict the rules in this file win. Remote URLs in its examples are not run; test input is generated with lavfi.
- External: Unity CLI skill — installed with `unity skill install <agent>` (`bootstrap.sh`).
- When adding a new external skill: read its contents, record its commit SHA here, do not add one that contains scripts or network calls.

## Definition of done (per episode)
All checks in `qc.json` are `pass`; long ≥ target duration, no visual/audio jump at the loop seam, LUFS within ±1 of the target, short 1080x1920 and 20–45 s, no metadata repetition, texts and CTA consistent with `config/brand.yaml`.
