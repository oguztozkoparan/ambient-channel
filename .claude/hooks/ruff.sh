#!/usr/bin/env bash
# If a Python file was edited: ruff format + check; on errors, reports back to Claude (exit 2).
f=$(jq -r '.tool_input.file_path // empty')
[[ "$f" == *.py ]] || exit 0
cd "$CLAUDE_PROJECT_DIR" || exit 0
uv run ruff format "$f" >/dev/null 2>&1
out=$(uv run ruff check "$f" 2>&1) || { echo "$out" >&2; exit 2; }
exit 0
