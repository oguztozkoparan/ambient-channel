#!/usr/bin/env bash
# Python dosyası düzenlendiyse ruff format + check; hata varsa Claude'a geri bildirir (exit 2).
f=$(jq -r '.tool_input.file_path // empty')
[[ "$f" == *.py ]] || exit 0
cd "$CLAUDE_PROJECT_DIR" || exit 0
uv run ruff format "$f" >/dev/null 2>&1
out=$(uv run ruff check "$f" 2>&1) || { echo "$out" >&2; exit 2; }
exit 0
