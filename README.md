# ambient-channel

YouTube ambient kanalı için üretim pipeline'ı: `episode.yaml` → long video + Short + metadata + QC. Kanal kimliği `config/brand.yaml`'dan gelir; repoyu fork'layıp veya klonlayıp kendi markanızla kullanabilirsiniz. Upload manuel (YouTube Studio).

Supported platform: macOS (Apple Silicon tested). Linux and Windows are untested.

## Kurulum (klon başına bir kez)
1. Önkoşullar: `uv`, `jq` ve drawtext içeren bir ffmpeg. macOS:
   `brew install uv jq ffmpeg-full && brew link ffmpeg-full`
   (Homebrew'un sade `ffmpeg` paketi drawtext içermez; Short metinleri ve pomodoro timer onu kullanır.)
2. `./bootstrap.sh` — Python bağımlılıklarını kurar, opsiyonel araçları (graphify, rtk, Unity CLI skill'i) varsa bağlar ve hazırlık kontrolünü çalıştırır.
3. Marka: Claude Code'da `/brand-setup` → `config/brand.yaml` (fork) veya `/brand-setup --local` → `config/brand.local.yaml` (commit'lenmez).
4. Deneme build'i (Unity ve gerçek ses gerekmez; girdiler sentetik üretilir):
   ```sh
   uv run python -m pipeline synth episodes/_template
   uv run python -m pipeline build episodes/_template --duration 10m
   uv run python -m pipeline qc output/example-outpost-night
   ```
   `qc.json` içinde tüm kontroller `pass` ise pipeline çalışıyor demektir.

Her an `uv run python -m pipeline doctor` neyin hazır, neyin eksik olduğunu söyler.

## Gerçek üretim için ek kurulum
- Unity CLI: `brew install --cask unity-cli`, `unity auth login`, `unity install lts`. Projeyi aç: `unity open unity`. Editor açıkken `unity pipeline install`; kontrol: `unity pipeline list` → "Pipeline: Installed". Unity Recorder paketini (`com.unity.recorder`) ekle.
- Ses: dosyalar `assets/audio/` altına (git'e girmez), her biri `assets/audio/LICENSES.md` içine kaynak ve lisansıyla. Şablondaki sentetik placeholder satırlarını gerçek kayıtlarla değiştirin.
- fal.ai MCP opsiyonel (thumbnail arka planı / konsept görseli; her üretim fal kredisi harcar). `.mcp.json`'da tanımlı; ilk kullanımda `/mcp` ile OAuth. Ana loop görselinde kullanılmaz.
- The Unity scene kit is not part of this repo: each user builds their own under `unity/`. `docs/KICKOFF.md` is a ready-made session prompt for that.

Ajan talimatları `AGENTS.md`'de (Claude Code, Codex, Cursor vb. ortak); `CLAUDE.md` onu import eder.

## Haftalık kullanım
`/weekly-batch` → tema onayı → build + QC → `output/week-XX/upload-checklist.md` → Studio'da zamanla.
Tek video: `/new-episode <slug> <tema>` → `/build-episode <slug>`.

## Build süreleri
Long steps draw a progress bar with a time estimate (one line per 10% when not on a terminal).

Apple M1'de ölçüldü (60 sn'lik 1080p loop, sentetik girdi):
- 10 dakikalık deneme build'i: toplam ~47 sn (loop encode ~12 sn, kalanı ses + Short).
- 10 saatlik build (tahmin, ölçülmedi): ~50 dk. Neredeyse tamamı two-pass loudnorm (~13x gerçek zaman); loop encode tek sefer ~12 sn, concat + mux ~15 sn. Geçici ses dosyası için ~14 GB boş disk gerekir.
- `focus` (pomodoro, tam encode): VideoToolbox ile ~6.8x gerçek zaman; 3 saatlik build ~26 dk encode + ~15 dk ses (tahmin).

## Lisans
Kod ve config: MIT (`LICENSE`). Kapsam dışı: `assets/fonts/` (SIL OFL 1.1, `assets/fonts/OFL.txt`), `.claude/skills/ffmpeg/` (MIT, kendi `LICENSE` dosyası) ve sizin eklediğiniz ses, klip, logo ile üretilen videolar; bunlar kendi lisanslarına tabidir.
