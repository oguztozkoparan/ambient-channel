---
name: build-episode
description: Bir episode'u build eder ve QC'den geçirir. Kullanıcı bir videoyu üretmek veya yeniden build etmek istediğinde kullan.
argument-hint: "[slug] [--duration 10m]"
disable-model-invocation: true
---
1. `episodes/$0/episode.yaml` var ve şemaya uygun mu kontrol et.
2. Unity klipleri (`assets/clips/$0/`) yoksa unity-scene-builder ile render et.
3. `uv run python -m pipeline build episodes/$0 $1` çalıştır.
4. qc-reviewer alt ajanını çalıştır.
5. Fail varsa ilgili ajana delege edip düzelt, tekrar build + QC. En fazla 2 tur; sonra raporla ve dur.
6. Sonuç: output yolları, süre, LUFS, QC özeti.
