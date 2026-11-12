# ambient-channel

Production pipeline for a YouTube ambient channel: `episode.yaml` → long video + Short + metadata + QC. The channel identity comes from `config/brand.yaml`; you can fork or clone the repo and use it with your own brand. Upload is manual (YouTube Studio).

Supported platform: macOS (Apple Silicon tested). Linux and Windows are untested.

## Setup (once per clone)
1. Prerequisites: `uv`, `jq` and an ffmpeg with drawtext. macOS:
   `brew install uv jq ffmpeg-full && brew link ffmpeg-full`
   (Homebrew's plain `ffmpeg` package does not include drawtext; Short texts and the pomodoro timer use it.)
2. `./bootstrap.sh` — installs Python dependencies, hooks up optional tools (graphify, rtk, Unity CLI skill) if present, and runs the readiness check.
3. Brand: in Claude Code, `/brand-setup` → `config/brand.yaml` (fork) or `/brand-setup --local` → `config/brand.local.yaml` (not committed).
4. Trial build (no Unity or real audio needed; inputs are generated synthetically):
   ```sh
   uv run python -m pipeline synth episodes/_template
   uv run python -m pipeline build episodes/_template --duration 10m
   uv run python -m pipeline qc output/example-outpost-night
   ```
   If all checks in `qc.json` are `pass`, the pipeline works.

At any time, `uv run python -m pipeline doctor` tells you what is ready and what is missing.

## Extra setup for real production
- Unity CLI: `brew install --cask unity-cli`, `unity auth login`, `unity install lts`. Open the project: `unity open unity`. With the Editor open, `unity pipeline install`; check: `unity pipeline list` → "Pipeline: Installed". Add the Unity Recorder package (`com.unity.recorder`).
- Audio: files go under `assets/audio/` (not tracked in git), each recorded in `assets/audio/LICENSES.md` with its source and license. Replace the synthetic placeholder rows from the template with real records.
- fal.ai MCP is optional (thumbnail background / concept image; every generation spends fal credits). Defined in `.mcp.json`; OAuth via `/mcp` on first use. Not used for the main loop visual.
- The Unity scene kit is not part of this repo: each user builds their own under `unity/`. `docs/KICKOFF.md` is a ready-made session prompt for that.

Agent instructions are in `AGENTS.md` (shared by Claude Code, Codex, Cursor, etc.); `CLAUDE.md` imports it.

## Weekly use
`/weekly-batch` → theme approval → build + QC → `output/week-XX/upload-checklist.md` → schedule in Studio.
Single video: `/new-episode <slug> <theme>` → `/build-episode <slug>`.

## Build times
Long steps draw a progress bar with a time estimate (one line per 10% when not on a terminal).

Measured on an Apple M1 (60 s 1080p loop, synthetic input):
- 10-minute trial build: ~47 s total (loop encode ~12 s, the rest is audio + Short).
- 10-hour build (estimate, not measured): ~50 min. Almost all of it is two-pass loudnorm (~13x real time); loop encode once ~12 s, concat + mux ~15 s. Needs ~14 GB of free disk for the temporary audio file.
- `focus` (pomodoro, full encode): ~6.8x real time with VideoToolbox; a 3-hour build is ~26 min encode + ~15 min audio (estimate).

## License
Code and config: MIT (`LICENSE`). Out of scope: `assets/fonts/` (SIL OFL 1.1, `assets/fonts/OFL.txt`), `.claude/skills/ffmpeg/` (MIT, its own `LICENSE` file) and the audio, clips and logos you add, along with the videos produced from them; these are subject to their own licenses.
