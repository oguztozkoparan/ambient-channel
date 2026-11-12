"""Config resolution. Precedence: brand.yaml < brand.local.yaml < use_cases.yaml < episode.yaml.

Paths are relative to the repo root (cwd); commands are run from the repo root.
"""

import glob
import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

CONFIG = Path("config")
PLACEHOLDER_HANDLE = "@your-handle"


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Bed(_Model):
    file: Path
    gain_db: float = 0.0


class Event(_Model):
    file: str  # glob
    every_s: tuple[float, float]
    gain_db: tuple[float, float]

    @field_validator("every_s")
    @classmethod
    def _interval_advances(cls, v: tuple[float, float]) -> tuple[float, float]:
        if not 0 <= v[0] <= v[1] or v[1] <= 0:  # otherwise event planning never terminates
            raise ValueError("every_s must be [min, max] with 0 <= min <= max and max > 0")
        return v

    pan_jitter: float = Field(0.0, ge=0, le=1)


class Audio(_Model):
    target_lufs: float
    true_peak: float = -1.5
    beds: list[Bed] = Field(min_length=1)
    events: list[Event] = []


class Visual(_Model):
    unity_preset: str
    clip_16x9: Path
    clip_9x16: Path | None = None
    crf: int = 20


class Short(_Model):
    duration_s: float = Field(30, ge=20, le=45)
    font: Path
    hook: str
    line2: str | None = None
    cta: str
    # new brand fields always get a default so older forks' brand.yaml keeps working
    text_color: str = "white"
    outline_color: str = "black"


class Pomodoro(_Model):
    work_min: float
    break_min: float
    work_label: str = "Focus"
    break_label: str = "Break"


class Watermark(_Model):
    file: Path | None = None
    position: Literal["top-left", "top-right", "bottom-left", "bottom-right"] = "bottom-right"
    opacity: float = Field(0.6, gt=0, le=1)


class Chapter(_Model):
    t: str
    label: str


class Disclosure(_Model):
    synthetic_realistic: bool = False
    note: str = ""


class Channel(_Model):
    name: str
    handle: str
    niche: str
    language: str
    voice: str


class Episode(_Model):
    slug: str
    seed: int
    use_case: Literal["general", "sleep", "focus"]
    variant_of: str | None = None
    title: str
    description: str
    tags: list[str] = []
    chapters: list[Chapter] = []
    duration_s: float  # target duration of this build (--duration can override it)
    nominal_duration_s: float  # duration from config; title/CTA texts use this
    loop_seconds: float
    event_density: float
    event_max_gain_db: float
    overlay: Literal["none", "pomodoro"] = "none"
    pomodoro: Pomodoro | None = None
    visual_exposure_ev: float | None = None  # used only by the Unity preset
    title_suffix: str = ""
    visual: Visual
    audio: Audio
    short: Short
    disclosure: Disclosure = Disclosure()
    watermark: Watermark = Watermark()
    channel: Channel
    description_footer: str = ""
    default_tags: list[str] = []

    @property
    def duration_overridden(self) -> bool:
        return self.duration_s != self.nominal_duration_s


def parse_duration(value: str | float) -> float:
    """ "8h" / "10m" / "90s" / number -> seconds."""
    if isinstance(value, int | float):
        return float(value)
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([hms])", value.strip())
    if not m:
        raise ValueError(f"invalid duration: {value!r} (e.g. 8h, 10m, 90s)")
    return float(m[1]) * {"h": 3600, "m": 60, "s": 1}[m[2]]


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


def _merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        out[k] = _merge(base[k], v) if isinstance(v, dict) and isinstance(base.get(k), dict) else v
    return out


def load_brand() -> dict:
    brand = _load(CONFIG / "brand.yaml")
    local = CONFIG / "brand.local.yaml"
    return _merge(brand, _load(local)) if local.exists() else brand


def load_episode(episode_dir: Path, duration: str | None = None) -> Episode:
    path = Path(episode_dir) / "episode.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"episode not found: {path}")
    raw = _load(path)
    brand = load_brand()
    use_cases = _load(CONFIG / "use_cases.yaml")
    name = raw.get("use_case", "general")
    if name not in use_cases:
        raise ValueError(f"unknown use_case: {name!r} (config/use_cases.yaml)")

    data = _merge(use_cases[name], raw)
    data["use_case"] = name
    nominal = parse_duration(data.pop("duration"))
    data["nominal_duration_s"] = nominal
    data["duration_s"] = parse_duration(duration) if duration else nominal
    data["audio"] = {"target_lufs": data.pop("target_lufs"), **data.get("audio", {})}

    channel = brand["channel"]
    short = {**brand.get("short", {}), **data.get("short", {})}
    values = {"hours": f"{nominal / 3600:g}", "name": channel["name"], "handle": channel["handle"]}
    if "cta" in short:  # a missing cta is reported by validation below
        try:
            short["cta"] = short["cta"].format(**values)
        except KeyError as e:
            raise ValueError(f"short.cta: unknown placeholder {e}; use {sorted(values)}") from None
    data["short"] = short
    data["watermark"] = {**(brand.get("watermark") or {}), **(data.get("watermark") or {})}
    data["channel"] = channel
    meta = brand.get("metadata", {})
    data["description_footer"] = meta.get("description_footer", "")
    data["default_tags"] = meta.get("default_tags", [])
    return Episode.model_validate(data)


def event_files(pattern: str) -> list[Path]:
    """Resolves an event glob; returns it sorted (determinism)."""
    return sorted(Path(p) for p in glob.glob(pattern))
