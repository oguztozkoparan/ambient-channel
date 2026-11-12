---
name: new-episode
description: Creates a new episode folder and episode.yaml. Use when the user wants to add a new video/theme.
argument-hint: "[slug] [theme description]"
---
1. Copy `episodes/_template/episode.yaml` to `episodes/$0/episode.yaml`.
2. Theme: $ARGUMENTS. Delegate filling in the fields to the concept-planner subagent. It composes from the audio files and Unity presets that already exist where it can, and reports anything new as assets to source.
3. Warn if the theme/preset/title clashes with the last 20 episodes.
4. Run `uv run python -m pipeline check episodes/$0`. Fix any config error it reports. Report the missing inputs it lists as "assets to source": each clip, audio file or preset with its planned path. Say plainly that these paths are planned, not existing. Do not create placeholder files.
5. Tell the user the next step: `/build-episode $0` once the assets exist, or `/build-episode $0 --trial` to try the flow with synthetic inputs.
