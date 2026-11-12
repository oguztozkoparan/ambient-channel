---
name: build-episode
description: Builds an episode and runs it through QC. Use when the user wants to produce or rebuild a video.
argument-hint: "[slug] [--duration 10m]"
disable-model-invocation: true
---
1. Check that `episodes/$0/episode.yaml` exists and matches the schema.
2. If the Unity clips (`assets/clips/$0/`) are missing, render them with unity-scene-builder.
3. Run `uv run python -m pipeline build episodes/$0 $1`.
4. Run the qc-reviewer subagent.
5. If anything fails, delegate the fix to the relevant agent, then build + QC again. At most 2 rounds; then report and stop.
6. Result: output paths, duration, LUFS, QC summary.
