"""User notifications that never interrupt the meeting unless near billing.

Severity ladder:
  INFO/TOAST -> non-modal (subtitle badge / macOS notification)
  MODAL      -> blocking dialog, only at >= 95%
  HARD_STOP  -> service stopped; captions freeze, meeting untouched
"""
from __future__ import annotations

import shutil
import subprocess
from typing import Set

from ..models import Severity


class Notifier:
    def __init__(self, use_macos_notifications: bool = True):
        self._macos = use_macos_notifications and shutil.which("osascript") is not None

    def notify(self, severity: Severity, title: str, message: str) -> None:
        tag = {
            Severity.INFO: "·",
            Severity.TOAST: "•",
            Severity.MODAL: "!",
            Severity.HARD_STOP: "■",
        }.get(severity, "·")
        print(f"[{tag}] {title}: {message}", flush=True)
        if self._macos and severity in (Severity.TOAST, Severity.MODAL, Severity.HARD_STOP):
            self._macos_notify(title, message)

    def _macos_notify(self, title: str, message: str) -> None:
        try:
            safe_t = title.replace('"', "'")
            safe_m = message.replace('"', "'")
            subprocess.run(
                ["osascript", "-e",
                 f'display notification "{safe_m}" with title "{safe_t}"'],
                check=False, capture_output=True, timeout=3,
            )
        except (OSError, subprocess.SubprocessError):
            pass


class ThresholdTracker:
    """Fires each configured warn threshold at most once per account+level."""

    def __init__(self):
        self._fired: Set[str] = set()

    def crossed(self, account_id: str, fraction: float, thresholds) -> list:
        newly = []
        for t in sorted(thresholds):
            key = f"{account_id}@{t}"
            if fraction >= t and key not in self._fired:
                self._fired.add(key)
                newly.append(t)
        return newly

    def reset(self, account_id: str) -> None:
        self._fired = {k for k in self._fired if not k.startswith(account_id + "@")}
