from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping


DEFAULT_MESSAGES = [
    "quack!",
    "อย่าลืมบันทึกงานนะ",
    "พักสายตาสักครู่ไหม?",
    "วันนี้คุณทำได้ดีมาก",
]


@dataclass(slots=True)
class AppConfig:
    size: float = 1.0
    speed: float = 3.0
    avoid_mouse: bool = True
    sound_enabled: bool = True
    talk_min_seconds: int = 18
    talk_max_seconds: int = 45
    messages: list[str] | None = None

    def __post_init__(self) -> None:
        if self.messages is None:
            self.messages = DEFAULT_MESSAGES.copy()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "AppConfig":
        messages = data.get("messages")
        clean_messages = (
            [str(item).strip() for item in messages if str(item).strip()]
            if isinstance(messages, list)
            else DEFAULT_MESSAGES.copy()
        )
        minimum = _integer(data.get("talk_min_seconds"), 18, 5, 300)
        maximum = _integer(data.get("talk_max_seconds"), 45, minimum, 600)
        return cls(
            size=_number(data.get("size"), 1.0, 0.6, 2.0),
            speed=_number(data.get("speed"), 3.0, 0.5, 12.0),
            avoid_mouse=_boolean(data.get("avoid_mouse"), True),
            sound_enabled=_boolean(data.get("sound_enabled"), True),
            talk_min_seconds=minimum,
            talk_max_seconds=maximum,
            messages=clean_messages or DEFAULT_MESSAGES.copy(),
        )


def _number(value: Any, default: float, lower: float, upper: float) -> float:
    try:
        return max(lower, min(upper, float(value)))
    except (TypeError, ValueError):
        return default


def _integer(value: Any, default: int, lower: int, upper: int) -> int:
    try:
        return max(lower, min(upper, int(value)))
    except (TypeError, ValueError):
        return default


def _boolean(value: Any, default: bool) -> bool:
    return value if isinstance(value, bool) else default


def default_config_path() -> Path:
    app_data = os.environ.get("APPDATA")
    base = Path(app_data) if app_data else Path.home() / "AppData" / "Roaming"
    return base / "DesktopDuck" / "config.json"


class ConfigStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_config_path()

    def load(self) -> AppConfig:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return AppConfig()
        return AppConfig.from_mapping(data) if isinstance(data, dict) else AppConfig()

    def save(self, config: AppConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(config.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)
