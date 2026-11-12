---
name: new-episode
description: Creates a new episode folder and episode.yaml. Use when the user wants to add a new video/theme.
argument-hint: "[slug] [theme description]"
---
1. Copy `episodes/_template/episode.yaml` to `episodes/$0/episode.yaml`.
2. Theme: $ARGUMENTS. Delegate filling in the fields to the concept-planner subagent.
3. Warn if the theme/preset/title clashes with the last 20 episodes.
4. If required audio layers or the Unity preset are missing, list them; do not write made-up file paths.
