#!/usr/bin/env bash
# Once per clone. Required: uv, ffmpeg (a build with drawtext), jq.
# Required AI tooling (CLAUDE.md), installed once per machine; this script only hooks it up:
#   graphify: pip install graphifyy && graphify install
#   rtk:      rtk init -g
#   headroom: alias claude="headroom wrap claude"
#   caveman, ponytail: Claude Code plugins, offered on first open (.claude/settings.json)
# Unity CLI is only needed for real production.
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
  graphify update .   # build the code knowledge graph (local, no LLM)
else
  echo "MISSING graphify (required for AI sessions): pip install graphifyy && graphify install, then rerun"
fi

if command -v rtk >/dev/null; then
  rtk --version   # hooks come from the per-machine `rtk init -g`
else
  echo "MISSING rtk (required for AI sessions): install rtk, run rtk init -g, then rerun"
fi

# Official Unity CLI skill (used by unity-scene-builder); the agent name may change between versions
if command -v unity >/dev/null; then
  unity skill install claude || echo "unity skill install failed: check the agent name with 'unity skill --help'"
else
  echo "Unity CLI not found, skipped (for real production: brew install --cask unity-cli)"
fi

uv run python -m pipeline doctor
