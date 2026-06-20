from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap


@dataclass(frozen=True, slots=True)
class AnimationSpec:
    frames: tuple[int, ...]
    fps: float


ANIMATIONS = {
    "walk": AnimationSpec((0, 1, 2, 3), 8.0),
    "idle": AnimationSpec((4, 5), 1.5),
    "sleep": AnimationSpec((6,), 1.0),
    "happy": AnimationSpec((7, 5), 3.5),
}


class SpriteAnimator:
    COLUMNS = 4
    ROWS = 2

    def __init__(self, sprite_path: Path) -> None:
        sheet = QPixmap(str(sprite_path))
        if sheet.isNull():
            raise FileNotFoundError(f"โหลด sprite ไม่ได้: {sprite_path}")

        cell_width = sheet.width() // self.COLUMNS
        cell_height = sheet.height() // self.ROWS
        self.frames = []
        for row in range(self.ROWS):
            for column in range(self.COLUMNS):
                self.frames.append(
                    sheet.copy(
                        column * cell_width,
                        row * cell_height,
                        cell_width,
                        cell_height,
                    )
                )

        self.state = "idle"
        self.frame_position = 0
        self.frame_elapsed = 0.0
        self._cache: dict[tuple[int, int, int, int], QPixmap] = {}

    def set_state(self, state: str) -> None:
        state = state if state in ANIMATIONS else "idle"
        if state == self.state:
            return
        self.state = state
        self.frame_position = 0
        self.frame_elapsed = 0.0

    def advance(self, seconds: float) -> None:
        spec = ANIMATIONS[self.state]
        if len(spec.frames) == 1:
            return
        self.frame_elapsed += seconds
        frame_duration = 1.0 / spec.fps
        while self.frame_elapsed >= frame_duration:
            self.frame_elapsed -= frame_duration
            self.frame_position = (self.frame_position + 1) % len(spec.frames)

    def pixmap(self, size: QSize, direction: int) -> QPixmap:
        frame_index = ANIMATIONS[self.state].frames[self.frame_position]
        facing = 1 if direction >= 0 else -1
        key = (frame_index, size.width(), size.height(), facing)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        frame = self.frames[frame_index]
        if facing < 0:
            frame = QPixmap.fromImage(frame.toImage().mirrored(True, False))
        scaled = frame.scaled(
            size,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._cache[key] = scaled
        return scaled

    def clear_cache(self) -> None:
        self._cache.clear()
