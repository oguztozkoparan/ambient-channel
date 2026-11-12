---
name: brand-setup
description: Sets up or changes the channel brand (name, handle, niche, language, voice, weekly count, title pattern, CTA, font, logo) in config/brand.yaml. Use when the repo has been forked or cloned, while `channel.handle` is still a placeholder, or when the user asks for branding/a rebrand.
argument-hint: "[--local]"
---
1. Read `config/brand.yaml` and, if present, `config/brand.local.yaml`. Ask the user about all missing or placeholder fields at once: channel name, handle, niche, language, voice, longs per week, title pattern, description footer, CTA text, font file, logo (optional). Do not make up values; leave unanswered fields as they are.
2. Target file: `config/brand.yaml` for a permanent brand (fork). If `$ARGUMENTS` contains `--local`, or the change will not be committed upstream, use `config/brand.local.yaml` (only the changed fields; not tracked in git).
3. If the language or niche changed, adapt the `title_suffix` values in `config/use_cases.yaml` to the new language/niche; do not touch any other field in that file.
4. Check that the `short.font` and `watermark.file` paths exist on disk; if not, list them as missing assets, do not make up paths.
5. Do not rewrite existing `episodes/*/episode.yaml` files. If any title, description or CTA was written with the old brand, only list it.
6. Give a summary: changed fields, missing assets, manual steps (the YouTube Studio channel name/handle is not managed from this repo).
