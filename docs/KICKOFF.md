# Sıradaki oturum prompt'u: Unity sahne kiti (Claude Code'a yapıştır)

Durum: `pipeline/` hazır (`build`, `qc`, `synth`, `doctor`; `uv run pytest -q` geçiyor; `episodes/_template` sentetik girdilerle uçtan uca build + QC'den geçiyor). Üretim için eksik tek parça `unity/`.

Önkoşul (elle): Unity CLI ve Unity 6 Editor kurulu, `unity auth login` yapılmış (bkz. README).

Hedef: AGENTS.md'deki mimariye göre `unity/` altında Unity 6 (URP) projesini kur: `ScenePreset` ScriptableObject (ışık, hava, partikül, kamera yolu, palet), parametrik tek sahne, 16:9 ve 9:16 kamera, Unity Recorder ile seamless loop render'ı ve Unity CLI'dan tetiklenen tek bir editor script'i. İlk preset: şablondaki `OutpostNight_Storm`. `sleep` varyantı için `visual_exposure_ev` override'ını preset üzerinden uygula.

Kısıtlar: AGENTS.md kuralları geçerli. Loop süresi episode.yaml `loop_seconds` ile aynı; ilk ve son frame eşleşmeli. Çıktılar `assets/clips/<slug>/loop_16x9.mp4` ve `loop_9x16.mp4`.

Akış: unity-scene-builder'a delege et; `unity <komut> --help` ile sözdizimini doğrulat. Recorder'ı önce açık Editor üzerinden çalıştır, headless yolu ancak doğrulandıktan sonra kullan. Sonunda qc-reviewer ile test et.

Done: sentetik klipler Unity render'ı ile değiştirildi; `uv run python -m pipeline build episodes/_template --duration 10m` ve `qc` hatasız, `seam_visual_ssim_drop` < 0.02; `uv run python -m pipeline doctor` çıktısında Unity satırları `ok`.
