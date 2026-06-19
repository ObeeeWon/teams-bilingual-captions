"""Subtitle UI interface."""
from __future__ import annotations

import abc

from ..models import Caption


class SubtitleUI(abc.ABC):
    @abc.abstractmethod
    def update_caption(self, caption: Caption) -> None:
        ...

    @abc.abstractmethod
    def set_status(self, text: str) -> None:
        """Small badge: active provider + remaining free allowance."""

    @abc.abstractmethod
    def freeze(self, message: str) -> None:
        """Hard stop: stop updating captions, keep history visible."""
