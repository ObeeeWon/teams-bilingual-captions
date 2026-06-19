"""Console subtitle UI (default; works headless, no GUI deps).

Partials are shown on a transient line (carriage-return overwrite); finals are
committed as a two-line EN/ZH block. A status line shows the active provider
and remaining free allowance.
"""
from __future__ import annotations

import sys

from ..models import Caption
from .base import SubtitleUI


class ConsoleUI(SubtitleUI):
    def __init__(self):
        self._status = ""
        self._frozen = False

    def update_caption(self, caption: Caption) -> None:
        if self._frozen:
            return
        if caption.is_final:
            # Clear the transient partial line, then commit the block.
            sys.stdout.write("\r" + " " * 80 + "\r")
            print(f"EN  {caption.text_en}")
            if caption.text_zh:
                print(f"ZH  {caption.text_zh}")
            print("-" * 40)
        else:
            sys.stdout.write("\r.. " + caption.text_en[:76])
            sys.stdout.flush()

    def set_status(self, text: str) -> None:
        if text == self._status:
            return
        self._status = text
        print(f"\n[status] {text}")

    def freeze(self, message: str) -> None:
        self._frozen = True
        print("\n" + "=" * 40)
        print(f"[stopped] {message}")
        print("=" * 40)
