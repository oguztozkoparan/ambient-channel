# Next session prompt: Unity scene kit (paste into Claude Code)

Status: `pipeline/` is ready (`build`, `qc`, `synth`, `doctor`; `uv run pytest -q` passes; `episodes/_template` passes an end-to-end build + QC with synthetic inputs). The only piece missing for production is `unity/`.

Prerequisite (manual): Unity CLI and the Unity 6 Editor installed, `unity auth login` done (see README).

Goal: set up the Unity 6 (URP) project under `unity/` following the architecture in AGENTS.md: a `ScenePreset` ScriptableObject (lighting, weather, particles, camera path, palette), a single parametric scene, 16:9 and 9:16 cameras, seamless loop rendering with Unity Recorder, and a single editor script triggered from the Unity CLI. First preset: `OutpostNight_Storm` from the template. Apply the `visual_exposure_ev` override for the `sleep` variant through the preset.

Constraints: AGENTS.md rules apply. The loop length equals episode.yaml `loop_seconds`; the first and last frames must match. Outputs are `assets/clips/<slug>/loop_16x9.mp4` and `loop_9x16.mp4`.

Flow: delegate to unity-scene-builder; have it verify syntax with `unity <command> --help`. Run Recorder through the open Editor first; use the headless path only after it has been verified. Finally, test with qc-reviewer.

Done: synthetic clips replaced with a Unity render; `uv run python -m pipeline build episodes/_template --duration 10m` and `qc` run without errors, `seam_visual_ssim_drop` < 0.02; Unity rows are `ok` in the `uv run python -m pipeline doctor` output.
