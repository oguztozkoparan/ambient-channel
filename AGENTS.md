# Ambient Channel — ajan rehberi

YouTube ambient kanalı için üretim pipeline'ı. Amaç: monetization'a uygun, özgün long videolar ve her biri için tanıtım amaçlı 1 Short (9:16, 20–45 sn, hook metinli). Kanal kimliği (ad, dil, ton, haftalık adet, CTA, font, logo) `config/brand.yaml`'dan gelir; varsayılan haftada 5 long (çoğu `general`, ara sıra `sleep`/`focus` varyantı). Upload manuel (YouTube Studio); bu repo üretim + QC'den sorumlu.

Bu dosya tüm kodlama ajanları için tek doğruluk kaynağıdır; `CLAUDE.md` bunu import eder.

## Mimari
- `unity/` — Unity 6 projesi: parametrik sahne kiti (preset ScriptableObject'ler: ışık, hava, kamera, efekt). Çıktı: seamless 16:9 loop klip + ayrı 9:16 kamera klibi.
- `pipeline/` — Python 3.12 + ffmpeg CLI (drawtext içeren build; macOS'ta `ffmpeg-full`). `episode.yaml` → `output/<slug>/{long.mp4, short.mp4, metadata.json, qc.json}`.
- `config/brand.yaml` — kanal kimliği. `config/brand.local.yaml` (git'e girmez) aynı şemayla alan bazında ezer.
- `config/use_cases.yaml` — `general` (varsayılan, çok amaçlı), `sleep`, `focus` varsayılanları: süre, LUFS, event yoğunluğu, overlay.
- `episodes/<slug>/episode.yaml` — episode'un tek doğruluk kaynağı. Şablon: `episodes/_template/episode.yaml`.
- `assets/` — ses katmanları, klipler, fontlar, marka dosyaları. Büyük medya git'e girmez (.gitignore).
- Config önceliği: `brand.yaml` < `brand.local.yaml` < `use_cases.yaml` < `episode.yaml`.

## Komutlar
- Kurulum: `uv sync`
- Build: `uv run python -m pipeline build episodes/<slug> [--duration 10m]`
- QC: `uv run python -m pipeline qc output/<slug>`
- Hazırlık kontrolü: `uv run python -m pipeline doctor`
- Deneme girdisi: `uv run python -m pipeline synth episodes/<slug>` (eksik klip/sesleri sentetik üretir; gerçek episode'da kullanılmaz)
- Test: `uv run pytest -q`
- Lint: `uv run ruff check . && uv run ruff format --check .`
- Unity (resmi Unity CLI): `unity open unity`, `unity pipeline list`, `unity command`. Sözdizimi için `unity <komut> --help`; ezberden yazma.

## Kurallar
- Config-driven: marka, tema, metin, süre, gain, seed kodda veya ajan talimatında hardcode edilmez.
- Deterministik: aynı config + seed = aynı çıktı.
- Long video tam süre encode edilmez (istisna: `focus` timer overlay'i her saniye değiştiği için tam encode gerektirir; varsa donanım encoder'ı kullan: macOS `h264_videotoolbox`, NVIDIA `h264_nvenc`): loop segmenti closed-GOP ile bir kez encode, concat demuxer + `-c copy` ile uzatılır; ses ayrı render edilip mux edilir.
- Ses tek loop'un tekrarı olmaz: bed katmanları + seed'li rastgele event katmanları. Loudness: two-pass loudnorm, varsayılan -20 LUFS / -1.5 dBTP.
- Ana görsel her zaman Unity render'ıdır. Generative AI görseli ana loop'ta kullanılmaz (disclosure gerektirmemesi ve kanalın kimliği için).
- Her episode tema, sahne preset'i, ses kompozisyonu ve başlık açısından önceki 20 episode'dan belirgin şekilde farklı olmalı (bkz. `channel-policy` skill'i).
- Pipeline kodu network çağrısı yapmaz (upload kapsam dışı).
- Pipeline'daki ffmpeg/ffprobe çağrıları `-hide_banner -loglevel error -nostats` ile çalışır; ilerleme gerekiyorsa `-progress` ile ayrı dosyaya yazılır.
- Minimal diff; istenmeyen refactor yok. İlgisiz bir sorun görürsen tek satırla bildir.

## Markalama
- Markaya özgü her değer `config/brand.yaml`'da durur. Fork kendi `brand.yaml`'ını commit'ler; lokal klon `brand.local.yaml` kullanır. Başka dosyada marka adı, handle, dil veya CTA yazma.
- `channel.handle` hâlâ `@your-handle` ise içerik (episode, başlık, Short) üretmeden önce `brand-setup` skill'ini çalıştır.
- Rebrand mevcut episode'ları yeniden yazmaz; eski metinler yalnızca listelenir.

## Araçlar
- Unity: resmi Unity CLI (`unity`), Bash üzerinden. Unity MCP kullanılmaz. Çalışan Editor'ü sürmek için projede Unity Pipeline paketi gerekir (`unity pipeline install`).
- fal.ai MCP (`.mcp.json`, sunucu adı `fal`, OAuth): yalnızca thumbnail arka planı ve konsept görseli için; ana loop'a ve Short görüntüsüne girmez. Her üretim fal kredisi harcar: önce `get_pricing`, kullanıcı onayı olmadan `run_model` / `submit_job` çağırma, ilerleme için yeniden gönderme (`check_job` kullan).

## Roller
Tanımlar `.claude/agents/*.md` altında (Claude Code'da alt ajan; diğer araçlarda rol talimatı olarak oku).
- `concept-planner` — haftalık tema, episode.yaml, başlık/açıklama/Short hook metinleri
- `audio-engineer` — `pipeline/audio.py`, ses katmanları, loudness
- `video-engineer` — `pipeline/video.py`, `short.py`, ffmpeg encode/concat/drawtext
- `unity-scene-builder` — `unity/` sahne kiti ve Unity CLI ile render otomasyonu
- `qc-reviewer` — salt okunur; dikiş, loudness, spec ve politika kontrolü

## Skill'ler
`.claude/skills/<ad>/SKILL.md` (Agent Skills formatı; skill desteği olmayan araçlar dosyayı adım listesi olarak okur).
- Proje: `brand-setup`, `new-episode`, `build-episode`, `weekly-batch`, `channel-policy`, `qc-checklist`.
- Dış kaynak: `ffmpeg` — [n0an/ffmpeg-skill](https://github.com/n0an/ffmpeg-skill) @ `aec7706`, MIT, değiştirilmeden kopyalandı. Tarif kaynağıdır; çakışmada bu dosyadaki kurallar kazanır. Örneklerindeki uzak URL'ler çalıştırılmaz; test girdisi lavfi ile üretilir.
- Dış kaynak: Unity CLI skill'i — `unity skill install <ajan>` ile kurulur (`bootstrap.sh`).
- Yeni dış skill eklerken: içeriğini oku, commit SHA'sını buraya yaz, script veya network çağrısı içereni ekleme.

## Done tanımı (her episode)
`qc.json` içinde tüm kontroller `pass`; long ≥ hedef süre, loop dikişinde görsel/ses sıçraması yok, LUFS hedefin ±1'i içinde, short 1080x1920 ve 20–45 sn, metadata tekrarı yok, metinler ve CTA `config/brand.yaml` ile uyumlu.
