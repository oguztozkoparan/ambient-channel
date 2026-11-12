---
name: qc-checklist
description: Episode çıktısı için ölçülebilir QC kontrolleri ve komutları. QC, doğrulama veya "video hazır mı" sorularında kullan.
user-invocable: false
---
`uv run python -m pipeline qc output/<slug>` ölçülebilir kontrolleri yapar ve `output/<slug>/qc.json` içine `{check, value, threshold, pass}` yazar; qc.json elle yazılmaz. Aşağıdaki liste tam spec'tir. Komutun ölçemediği maddeler (pomodoro faz geçişi, hook/CTA görünürlüğü, metin dili, watermark, click) reviewer tarafından elle doğrulanır: ilgili andan `ffmpeg -ss <t> -frames:v 1` ile kare çıkar ve bak.

- Süre: `ffprobe -v error -show_entries format=duration -of csv=p=0 long.mp4` ≥ hedef.
- Loudness: `ffmpeg -hide_banner -nostats -i long.mp4 -t 600 -af ebur128=peak=true:framelog=verbose -f null -` → integrated hedef ±1 LU, true peak ≤ -1.0 dBTP.
- Loop dikişi (görsel): loop sınırının ±1 sn'sinden frame çıkar, ardışık frame SSIM düşüşü < 0.02 olmalı.
- Loop dikişi (ses): sınır ±50 ms penceresinde RMS sıçraması < 3 dB, click yok.
- use_case: süre ve LUFS hedefi `config/use_cases.yaml` + episode override'larından çözülür. `sleep`: hiçbir event peak'i bed RMS'inin +10 dB üstünde değil. `focus`: pomodoro faz geçişleri config'teki dakikalarla ±1 sn eşleşiyor.
- Short spec: 1080x1920, 20–45 sn, hook 0–2 sn içinde görünür, CTA son 3 sn.
- Metadata: başlık son 20 episode'un hiçbiriyle %70'ten fazla kelime örtüşmesi yok; açıklama ve chapter'lar dolu; başlıktaki süre gerçek süreyle tutarlı; hiçbir chapter video süresini aşmıyor.
- Marka: metinler `config/brand.yaml` `channel.language` dilinde; açıklama `metadata.description_footer` ile bitiyor; Short CTA'sı `short.cta` şablonundan (veya episode override'ından); `watermark.file` doluysa long ve short'ta görünür.
- Ses kaynakları: kullanılan her dosya `assets/audio/LICENSES.md` içinde kayıtlı.
