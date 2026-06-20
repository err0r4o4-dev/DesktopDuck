from __future__ import annotations

from dataclasses import replace

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from desktop_duck.config import AppConfig, DEFAULT_MESSAGES


class SettingsDialog(QDialog):
    def __init__(self, config: AppConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ตั้งค่า DesktopDuck")
        self.setMinimumWidth(380)
        self._original = config

        self.size_input = QDoubleSpinBox()
        self.size_input.setRange(0.6, 2.0)
        self.size_input.setSingleStep(0.1)
        self.size_input.setValue(config.size)

        self.speed_input = QDoubleSpinBox()
        self.speed_input.setRange(0.5, 12.0)
        self.speed_input.setSingleStep(0.5)
        self.speed_input.setValue(config.speed)

        self.avoid_input = QCheckBox("เป็ดวิ่งหนีเมาส์เมื่อเข้าใกล้")
        self.avoid_input.setChecked(config.avoid_mouse)
        self.sound_input = QCheckBox("เปิดเสียง")
        self.sound_input.setChecked(config.sound_enabled)

        self.talk_min_input = QSpinBox()
        self.talk_min_input.setRange(5, 300)
        self.talk_min_input.setSuffix(" วินาที")
        self.talk_min_input.setValue(config.talk_min_seconds)
        self.talk_max_input = QSpinBox()
        self.talk_max_input.setRange(5, 600)
        self.talk_max_input.setSuffix(" วินาที")
        self.talk_max_input.setValue(config.talk_max_seconds)

        self.messages_input = QPlainTextEdit()
        self.messages_input.setPlaceholderText("หนึ่งข้อความต่อหนึ่งบรรทัด")
        self.messages_input.setPlainText("\n".join(config.messages or DEFAULT_MESSAGES))
        self.messages_input.setMinimumHeight(120)

        form = QFormLayout()
        form.addRow("ขนาด", self.size_input)
        form.addRow("ความเร็ว", self.speed_input)
        form.addRow("พูดเร็วสุดทุก", self.talk_min_input)
        form.addRow("พูดช้าสุดทุก", self.talk_max_input)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self.avoid_input)
        layout.addWidget(self.sound_input)
        layout.addWidget(QLabel("ข้อความที่เป็ดพูด (หนึ่งข้อความต่อบรรทัด)"))
        layout.addWidget(self.messages_input)
        layout.addWidget(buttons)

    def result_config(self) -> AppConfig:
        messages = [
            line.strip()
            for line in self.messages_input.toPlainText().splitlines()
            if line.strip()
        ]
        talk_minimum = self.talk_min_input.value()
        talk_maximum = max(talk_minimum, self.talk_max_input.value())
        return replace(
            self._original,
            size=self.size_input.value(),
            speed=self.speed_input.value(),
            avoid_mouse=self.avoid_input.isChecked(),
            sound_enabled=self.sound_input.isChecked(),
            talk_min_seconds=talk_minimum,
            talk_max_seconds=talk_maximum,
            messages=messages or DEFAULT_MESSAGES.copy(),
        )
