"""PyQt6 always-on-top, translucent bilingual subtitle overlay.

Optional UI (requires PyQt6). Falls back is handled by the caller. Run the Qt
event loop on the main thread and post updates via signals from the asyncio
pipeline thread.

This is a minimal, functional skeleton: a frameless translucent window with an
English line (white), a Chinese line (light gray), and a small status badge.
"""
from __future__ import annotations

from ..models import Caption
from .base import SubtitleUI

try:
    from PyQt6.QtCore import Qt, pyqtSignal, QObject
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
    _HAS_QT = True
except ImportError:  # pragma: no cover
    _HAS_QT = False


if _HAS_QT:

    class _Bridge(QObject):
        caption = pyqtSignal(object)
        status = pyqtSignal(str)
        frozen = pyqtSignal(str)

    class QtSubtitleWindow(QWidget, SubtitleUI):
        def __init__(self, history_lines: int = 3):
            super().__init__()
            self.bridge = _Bridge()
            self.bridge.caption.connect(self._on_caption)
            self.bridge.status.connect(self._on_status)
            self.bridge.frozen.connect(self._on_frozen)

            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint
                | Qt.WindowType.WindowStaysOnTopHint
                | Qt.WindowType.Tool
            )
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

            self._en = QLabel("")
            self._zh = QLabel("")
            self._badge = QLabel("")
            self._en.setFont(QFont("Helvetica", 20))
            self._zh.setFont(QFont("PingFang SC", 20))
            self._badge.setFont(QFont("Helvetica", 11))
            self._en.setStyleSheet("color: white;")
            self._zh.setStyleSheet("color: #d0d0d0;")
            self._badge.setStyleSheet("color: #9acd32;")

            layout = QVBoxLayout(self)
            layout.addWidget(self._badge)
            layout.addWidget(self._en)
            layout.addWidget(self._zh)
            self.setStyleSheet("background: rgba(0,0,0,160); border-radius: 12px;")
            self.resize(760, 160)

        # Thread-safe entry points (called from the asyncio side).
        def update_caption(self, caption: Caption) -> None:
            self.bridge.caption.emit(caption)

        def set_status(self, text: str) -> None:
            self.bridge.status.emit(text)

        def freeze(self, message: str) -> None:
            self.bridge.frozen.emit(message)

        # Slots (run on the Qt main thread).
        def _on_caption(self, caption: Caption) -> None:
            color = "white" if caption.is_final else "#9a9a9a"
            self._en.setStyleSheet(f"color: {color};")
            self._en.setText(caption.text_en)
            if caption.is_final and caption.text_zh:
                self._zh.setText(caption.text_zh)

        def _on_status(self, text: str) -> None:
            self._badge.setText(text)

        def _on_frozen(self, message: str) -> None:
            self._badge.setText(message)
