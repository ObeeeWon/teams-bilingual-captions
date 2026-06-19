"""Shared data types used across the pipeline."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class QuotaKind(str, Enum):
    MONTHLY_AUDIO = "monthly_audio"   # measured in seconds, resets each cycle
    CREDIT_USD = "credit_usd"         # one-time / prepaid balance in USD
    MONTHLY_CHARS = "monthly_chars"   # translated characters, resets each cycle


class Severity(str, Enum):
    INFO = "info"        # silent badge in the subtitle window
    TOAST = "toast"      # transient, non-modal notification
    MODAL = "modal"      # blocking dialog (only near hard stop)
    HARD_STOP = "hard_stop"


@dataclass
class Caption:
    """A single subtitle update emitted by a provider."""
    text_en: str
    text_zh: str = ""
    is_final: bool = False
    provider_id: str = ""
    ts: float = field(default_factory=time.time)


@dataclass
class UsageDelta:
    """Raw usage produced by handling some audio / text.

    Providers report in *native* terms (seconds + characters); the
    QuotaManager converts these to each account's unit.
    """
    audio_seconds: float = 0.0
    chars: int = 0


@dataclass
class AudioChunk:
    pcm: bytes
    seconds: float
    sample_rate: int = 16000
