# ambient-channel

Production pipeline for a YouTube ambient channel: `episode.yaml` → long video + Short + metadata + QC. The channel identity comes from `config/brand.yaml`; you can fork or clone the repo and use it with your own brand. Upload is manual (YouTube Studio).

Supported platform: macOS (Apple Silicon tested). Linux and Windows are untested.

## Setup (once per clone)
1. Prerequisites: `uv`, `jq` and an ffmpeg with drawtext. macOS:
   `brew install uv jq ffmpeg-full && brew link ffmpeg-full`
   (Homebrew's plain `ffmpeg` package does not include drawtext; Short texts and the pomodoro timer use it.)
2. AI tooling (required; it saves tokens and keeps a knowledge graph of the project, and the agent rules in `CLAUDE.md` depend on it): `pip install graphifyy && graphify install`, install rtk and run `rtk init -g`, and accept the caveman and ponytail plugins when Claude Code offers them on first open.
3. `./bootstrap.sh` — installs Python dependencies, hooks up graphify and rtk for this clone, builds the knowledge graph and runs the readiness check.
4. Brand: in Claude Code, `/brand-setup` → `config/brand.yaml` (fork) or `/brand-setup --local` → `config/brand.local.yaml` (not committed).
5. Trial build (no Unity or real audio needed):
   ```sh
   uv run python -m pipeline build episodes/_template --trial
   uv run python -m pipeline qc output/example-outpost-night
   ```
   `--trial` generates any missing clips/audio synthetically (color bars, noise) and builds a 10-minute video instead of the full 8 hours, through the same steps and checks. If all checks in `qc.json` are `pass`, the pipeline works. A trial output is never uploaded.

At any time, `uv run python -m pipeline doctor` tells you what is ready and what is missing, and `uv run python -m pipeline check episodes/<slug>` lists every input an episode still needs.

## Extra setup for real production
- Unity CLI: `brew install --cask unity-cli`, `unity auth login`, `unity install lts`. Open the project: `unity open unity`. With the Editor open, `unity pipeline install`; check: `unity pipeline list` → "Pipeline: Installed". Add the Unity Recorder package (`com.unity.recorder`).
- Audio: files go under `assets/audio/` (not tracked in git), each recorded in `assets/audio/LICENSES.md` with its source and license. A real build fails QC for any audio file without a row there, including leftover synthetic files from a trial.
- fal.ai MCP is optional (thumbnail background / concept image; every generation spends fal credits). Defined in `.mcp.json`; OAuth via `/mcp` on first use. Not used for the main loop visual.
- The Unity scene kit is not part of this repo: each user builds their own under `unity/`. `docs/KICKOFF.md` is a ready-made session prompt for that.

Agent instructions are in `AGENTS.md` (shared by Claude Code, Codex, Cursor, etc.); `CLAUDE.md` imports it.

## Weekly use
`/weekly-batch` → theme approval → build + QC → `output/week-XX/upload-checklist.md` → schedule in Studio.
Single video: `/new-episode <slug> <theme>` → `/build-episode <slug>`.
Add `--trial` to `/build-episode` or `/weekly-batch` to run the same flow on synthetic inputs first.

## Agent effort levels
Each agent definition (`.claude/agents/*.md`) pins its reasoning effort. The agents also pin their model, and Claude Code applies your session's effort level only to subagents on the session's own model, so without an explicit `effort` the level would not be yours to control and results would vary by setup.

| Agent | Effort | Why |
|---|---|---|
| `audio-engineer` | `high` | Agentic coding. Its mistakes surface late, in 8–10 hour builds. |
| `video-engineer` | `high` | Agentic coding. ffmpeg filter escaping is easy to get subtly wrong. |
| `unity-scene-builder` | `high` | Terminal-driven, multi-step work against a live Editor, with a CLI whose syntax must be checked each time. |
| `concept-planner` | `medium` | Constrained text and YAML. `low` is clearly worse; `high` adds tokens without better output for this kind of work. |
| `qc-reviewer` | `medium` | Read-only, checklist-driven measurement. |

Basis (November 2026): for Sonnet 5.5, Anthropic reports 62.7% at `medium` against 77.8% at `high` on its internal agentic-coding benchmark, and about 7 points on a SWE-bench Pro subset for about 59% of the cost ([source](https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence)); third-party measurements put tokens per task at roughly 1.8x. `xhigh` and `max` cost several times more and are not warranted for modules this small; if `unity-scene-builder` struggles at `high`, it is the one candidate for `xhigh`. The `unity-scene-builder` level is an estimate (it has not been run in this repo yet), and there is no per-effort benchmark for the Haiku-based `qc-reviewer`.

## Build times
Long steps draw a progress bar with a time estimate (one line per 10% when not on a terminal).

Measured on an Apple M1 (60 s 1080p loop, synthetic input):
- 10-minute trial build: ~47 s total (loop encode ~12 s, the rest is audio + Short).
- 10-hour build (estimate, not measured): ~50 min. Almost all of it is two-pass loudnorm (~13x real time); loop encode once ~12 s, concat + mux ~15 s. Needs ~14 GB of free disk for the temporary audio file.
- `focus` (pomodoro, full encode): ~6.8x real time with VideoToolbox; a 3-hour build is ~26 min encode + ~15 min audio (estimate).

## License
Code and config: MIT (`LICENSE`). Out of scope: `assets/fonts/` (SIL OFL 1.1, `assets/fonts/OFL.txt`), `.claude/skills/ffmpeg/` (MIT, its own `LICENSE` file) and the audio, clips and logos you add, along with the videos produced from them; these are subject to their own licenses.
