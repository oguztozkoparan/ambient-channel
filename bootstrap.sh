#!/usr/bin/env bash
# Klon başına bir kez. Zorunlu: uv, ffmpeg (drawtext içeren build), jq.
# Opsiyonel kişisel araçlar (yoksa atlanır): graphify, rtk, Unity CLI.
set -euo pipefail
cd "$(dirname "$0")"

need() { command -v "$1" >/dev/null || { echo "eksik: $1  ->  $2" >&2; exit 1; }; }
need uv "brew install uv"
need jq "brew install jq"
need ffmpeg "brew install ffmpeg-full && brew link ffmpeg-full"

[ -d .git ] || git init -q
uv sync

if command -v graphify >/dev/null; then
  backup=$(mktemp)
  cp .claude/settings.json "$backup"
  graphify claude install   # settings.json'ı merge etmeden üzerine yazar
  graphify hook install
  # graphify hook'ları (mutlak path içerir) local'e taşınır, commit'lenen settings geri yüklenir
  jq '{hooks: .hooks}' .claude/settings.json > .claude/settings.local.json
  cp "$backup" .claude/settings.json
  rm -f "$backup" .claude/settings.json.graphify-bak
else
  echo "graphify yok, atlandı (opsiyonel: pip install graphifyy && graphify install)"
fi

if command -v rtk >/dev/null; then rtk init --show; else echo "rtk yok, atlandı (opsiyonel)"; fi

# Resmi Unity CLI skill'i (unity-scene-builder kullanır); ajan adı sürüme göre değişebilir
if command -v unity >/dev/null; then
  unity skill install claude || echo "unity skill kurulamadı: 'unity skill --help' ile ajan adını doğrula"
else
  echo "Unity CLI yok, atlandı (gerçek üretim için: brew install --cask unity-cli)"
fi

uv run python -m pipeline doctor
