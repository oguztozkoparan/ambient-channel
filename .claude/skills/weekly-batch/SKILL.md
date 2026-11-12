---
name: weekly-batch
description: Plans and builds the weekly episode batch (count from config/brand.yaml) and produces the upload checklist. With `--trial`, runs the whole flow on synthetic inputs to prove it works.
argument-hint: "[--trial]"
disable-model-invocation: true
---
Arguments: $ARGUMENTS.

`--trial`: every build runs as a trial (missing inputs generated synthetically, 10-minute videos instead of full length). Use it to prove the flow before investing in scenes, sounds and hours of build time. Nothing from a trial is uploaded.

1. If `config/brand.yaml` `channel.handle` is a placeholder, run `/brand-setup` first. With concept-planner, propose `cadence.longs_per_week` distinct themes (mostly `general`, at most `cadence.max_variants_per_week` `sleep`/`focus` variants); show them to the user as a single list and get approval (this is the only approval point).
2. For each approved theme, follow the `/new-episode` steps.
3. For each episode, follow the `/build-episode` steps in order (with `--trial` if given); do not wait for approval. If an episode stops on missing inputs, go on to the next one and keep its list.
4. Write `output/week-<ISO week>/upload-checklist.md`: suggested publish day/time (spread across the week), title, description, tags, chapters, thumbnail path (`output/<slug>/thumbnail.jpg`), short path and the answer to the "Altered or synthetic content" question (Unity render → no; if there is an exception, the reason). List episodes that were not built together with their missing inputs. For a trial, put "TRIAL — do not upload" at the top.
