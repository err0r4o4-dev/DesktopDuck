from __future__ import annotations

import random
import time

from PySide6.QtCore import QPoint, QRect, QSize, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QCloseEvent,
    QCursor,
    QFont,
    QIcon,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QMenu,
    QSystemTrayIcon,
    QWidget,
)

from desktop_duck.animation import SpriteAnimator
from desktop_duck.behavior import DuckBehavior
from desktop_duck.config import AppConfig, ConfigStore, DEFAULT_MESSAGES
from desktop_duck.resources import resource_path
from desktop_duck.settings import SettingsDialog


class DuckWindow(QWidget):
    BASE_SPRITE_SIZE = QSize(240, 320)
    BUBBLE_SPACE = 60
    GROUND_INSET_RATIO = 0.16

    def __init__(self, config: AppConfig, store: ConfigStore) -> None:
        super().__init__()
        self.config = config
        self.store = store
        self.animator = SpriteAnimator(
            resource_path("assets", "sprites", "duck_sprite.png")
        )
        self.paused = False
        self.dragging = False
        self.drag_offset = QPoint()
        self.bubble_message = ""
        self.bubble_until = 0.0
        self._allow_close = False
        self._last_tick = time.monotonic()

        self.setWindowTitle("DesktopDuck")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        self._apply_size()

        screen = QApplication.primaryScreen()
        if screen is None:
            raise RuntimeError("ไม่พบหน้าจอสำหรับแสดง DesktopDuck")
        bounds = screen.availableGeometry()
        starting_x = random.uniform(
            bounds.left(), max(bounds.left(), bounds.right() - self.width())
        )
        self.behavior = DuckBehavior(starting_x, self.config)
        self._move_to_ground(starting_x, bounds)

        self.menu = QMenu(self)
        self.pause_action = QAction("พักการเดิน", self)
        self.pause_action.triggered.connect(self.toggle_pause)
        self.menu.addAction(self.pause_action)
        self.menu.addAction("พูด", self.say_random_message)
        self.menu.addAction("ดีใจ", lambda: self.set_duck_state("happy", 3.0))
        self.menu.addAction("นอน", lambda: self.set_duck_state("sleep", 8.0))
        self.menu.addSeparator()
        self.menu.addAction("ตั้งค่า", self.open_settings)
        self.menu.addAction("ย้ายกลับเข้าหน้าจอ", self.reset_position)
        self.menu.addSeparator()
        self.menu.addAction("ออก", self.quit_app)

        self.tray = self._create_tray_icon()

        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)

    def _create_tray_icon(self) -> QSystemTrayIcon | None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return None
        icon_path = resource_path("assets", "duck.ico")
        icon = QIcon(str(icon_path)) if icon_path.exists() else QIcon(
            self.animator.frames[4]
        )
        tray = QSystemTrayIcon(icon, self)
        tray.setToolTip("DesktopDuck")
        tray.setContextMenu(self.menu)
        tray.activated.connect(self._tray_activated)
        tray.show()
        return tray

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            self.show()
            self.raise_()

    def _apply_size(self) -> None:
        width = int(self.BASE_SPRITE_SIZE.width() * self.config.size)
        height = int(
            (self.BASE_SPRITE_SIZE.height() + self.BUBBLE_SPACE) * self.config.size
        )
        self.setFixedSize(width, height)
        self.animator.clear_cache()

    def _sprite_size(self) -> QSize:
        return QSize(
            int(self.BASE_SPRITE_SIZE.width() * self.config.size),
            int(self.BASE_SPRITE_SIZE.height() * self.config.size),
        )

    def _bubble_height(self) -> int:
        return int(self.BUBBLE_SPACE * self.config.size)

    def _current_screen_bounds(self) -> QRect:
        center = self.frameGeometry().center()
        screen = QApplication.screenAt(center) or QApplication.primaryScreen()
        if screen is None:
            return QRect(0, 0, 1920, 1080)
        return screen.availableGeometry()

    def _ground_y(self, bounds: QRect) -> int:
        inset = int(self._sprite_size().height() * self.GROUND_INSET_RATIO)
        return bounds.bottom() - self.height() + 1 + inset

    def _move_to_ground(
        self, x: float, bounds: QRect, *, sync_behavior: bool = False
    ) -> None:
        maximum_x = max(bounds.left(), bounds.right() - self.width() + 1)
        safe_x = max(bounds.left(), min(int(x), maximum_x))
        self.move(safe_x, self._ground_y(bounds))
        if sync_behavior and hasattr(self, "behavior"):
            self.behavior.place(safe_x)

    def tick(self) -> None:
        now = time.monotonic()
        seconds = min(0.08, now - self._last_tick)
        self._last_tick = now

        if not self.paused and not self.dragging:
            bounds = self._current_screen_bounds()
            pointer = QCursor.pos()
            snapshot = self.behavior.update(
                seconds=seconds,
                left=bounds.left(),
                right=bounds.right() + 1,
                width=self.width(),
                pointer=(pointer.x(), pointer.y()),
                center_y=(
                    self.y() + self._bubble_height() + self._sprite_size().height() / 2
                ),
                config=self.config,
            )
            self.animator.set_state(snapshot.state)
            self.animator.advance(seconds)
            self._move_to_ground(snapshot.x, bounds)
            if snapshot.should_talk:
                self.say_random_message()
            if snapshot.bumped:
                self.beep()

        if self.bubble_message and now >= self.bubble_until:
            self.bubble_message = ""
        self.update()

    def paintEvent(self, _event) -> None:  # type: ignore[no-untyped-def]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(
            0,
            self._bubble_height(),
            self.animator.pixmap(self._sprite_size(), self.behavior.direction),
        )

        if not self.bubble_message:
            return
        bubble = QRect(
            10,
            4,
            self.width() - 20,
            max(32, self._bubble_height() - 8),
        )
        path = QPainterPath()
        path.addRoundedRect(bubble, 12, 12)
        painter.fillPath(path, Qt.GlobalColor.white)
        painter.setPen(QPen(Qt.GlobalColor.black, 2))
        painter.drawPath(path)
        painter.setFont(QFont("Segoe UI", max(9, int(10 * self.config.size))))
        painter.drawText(
            bubble.adjusted(10, 6, -10, -6),
            Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap,
            self.bubble_message,
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_offset = event.position().toPoint()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self.menu.popup(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            target = event.globalPosition().toPoint() - self.drag_offset
            self.move(target)
            self.behavior.place(target.x())
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False
            self._move_to_ground(
                self.x(), self._current_screen_bounds(), sync_behavior=True
            )
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_duck_state("happy", 3.0)
            self.say_random_message()
            event.accept()

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self.pause_action.setText("เดินต่อ" if self.paused else "พักการเดิน")

    def set_duck_state(self, state: str, duration: float) -> None:
        self.behavior.trigger(state, duration)
        self.animator.set_state(state)
        self.beep()

    def say_random_message(self) -> None:
        messages = self.config.messages or DEFAULT_MESSAGES
        self.bubble_message = random.choice(messages)
        self.bubble_until = time.monotonic() + 2.8
        self.beep()
        self.update()

    def beep(self) -> None:
        if self.config.sound_enabled:
            QApplication.beep()

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        old_size = self.config.size
        self.config = dialog.result_config()
        self.store.save(self.config)
        if self.config.size != old_size:
            self._apply_size()
        self._move_to_ground(
            self.x(), self._current_screen_bounds(), sync_behavior=True
        )

    def reset_position(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        bounds = screen.availableGeometry()
        self._move_to_ground(
            bounds.center().x() - self.width() / 2,
            bounds,
            sync_behavior=True,
        )
        self.show()
        self.raise_()

    def keyPressEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.key() == Qt.Key.Key_Escape:
            self.quit_app()
        else:
            super().keyPressEvent(event)

    def quit_app(self) -> None:
        self.store.save(self.config)
        self._allow_close = True
        if self.tray is not None:
            self.tray.hide()
        QApplication.quit()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._allow_close:
            event.accept()
        elif self.tray is not None:
            self.hide()
            event.ignore()
        else:
            self.quit_app()
            event.accept()
