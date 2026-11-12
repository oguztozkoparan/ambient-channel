#!/usr/bin/env bash
# Once per clone. Required: uv, ffmpeg (a build with drawtext), jq.
# Optional personal tools (skipped if missing): graphify, rtk, Unity CLI.
set -euo pipefail
cd "$(dirname "$0")"

need() { command -v "$1" >/dev/null || { echo "missing: $1  ->  $2" >&2; exit 1; }; }
need uv "brew install uv"
need jq "brew install jq"
need ffmpeg "brew install ffmpeg-full && brew link ffmpeg-full"

[ -d .git ] || git init -q
uv sync

if command -v graphify >/dev/null; then
  backup=$(mktemp)
  cp .claude/settings.json "$backup"
  graphify claude install   # overwrites settings.json without merging
  graphify hook install
  # graphify hooks (contain absolute paths) move to local; the committed settings are restored
  jq '{hooks: .hooks}' .claude/settings.json > .claude/settings.local.json
  cp "$backup" .claude/settings.json
  rm -f "$backup" .claude/settings.json.graphify-bak
else
  echo "graphify not found, skipped (optional: pip install graphifyy && graphify install)"
fi

if command -v rtk >/dev/null; then rtk init --show; else echo "rtk not found, skipped (optional)"; fi

# Official Unity CLI skill (used by unity-scene-builder); the agent name may change between versions
if command -v unity >/dev/null; then
  unity skill install claude || echo "unity skill install failed: check the agent name with 'unity skill --help'"
else
  echo "Unity CLI not found, skipped (for real production: brew install --cask unity-cli)"
fi

uv run python -m pipeline doctor
