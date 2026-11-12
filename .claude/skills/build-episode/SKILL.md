---
name: build-episode
description: Builds an episode and runs it through QC. Use when the user wants to produce or rebuild a video, or to try the flow end to end with `--trial`.
argument-hint: "[slug] [--trial | --duration 10m]"
disable-model-invocation: true
---
Arguments: $ARGUMENTS. The first is the slug; pass everything after it to the build command unchanged.

`--trial` proves the flow without real assets or hours of waiting: the build generates any missing clips/audio synthetically (color bars, noise) and produces a 10-minute video instead of the full duration, through the same steps and QC checks. A trial output is never uploaded.

1. Run `uv run python -m pipeline check episodes/$0`. If it reports config errors, fix them (or delegate to concept-planner) before going on.
2. If it lists missing inputs and this is not a `--trial` run:
   - Clips are missing and a Unity project exists (`unity/ProjectSettings`): render them with unity-scene-builder.
   - Otherwise stop and give the user the list: which file must be rendered or sourced to which path, and that every audio file also needs a row in `assets/audio/LICENSES.md`. Offer `--trial` as the way to test the flow in the meantime. Do not invent or substitute files.
3. Run `uv run python -m pipeline build episodes/$0` with the remaining arguments.
4. Run the qc-reviewer subagent; tell it if the build is a trial.
5. If anything fails, delegate the fix to the relevant agent, then build + QC again. At most 2 rounds; then report and stop.
6. Result: output paths (long, short, thumbnail), duration, LUFS, QC summary. For a trial, say clearly that it is a trial and what real assets are still needed.
