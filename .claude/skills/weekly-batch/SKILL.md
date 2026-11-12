---
name: weekly-batch
description: Plans and builds the weekly episode batch (count from config/brand.yaml) and produces the upload checklist.
disable-model-invocation: true
---
1. If `config/brand.yaml` `channel.handle` is a placeholder, run `/brand-setup` first. With concept-planner, propose `cadence.longs_per_week` distinct themes (mostly `general`, at most `cadence.max_variants_per_week` `sleep`/`focus` variants); show them to the user as a single list and get approval (this is the only approval point).
2. For each approved theme, follow the `/new-episode` steps.
3. For each episode, follow the `/build-episode` steps in order; do not wait for approval.
4. Write `output/week-<ISO week>/upload-checklist.md`: suggested publish day/time (spread across the week), title, description, tags, chapters, thumbnail path, short path and the answer to the "Altered or synthetic content" question (Unity render → no; if there is an exception, the reason).
