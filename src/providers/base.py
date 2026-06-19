"""Provider interface.

Every backend (Azure integrated, Deepgram+Translator split, local, or the
simulated demo) implements this same contract, so the Orchestrator can swap
the active provider without touching the audio source or the UI.

Lifecycle:
    warmup()         # connect / load, cheaply, BEFORE we need to switch
    start_session()  # begin a live transcription session
    feed_audio()     # push PCM chunks
    -> on_caption    # provider emits partial/final Caption objects
    stop_session()   # tear down
"""
from __future__ import annotations

import abc
from typing import Awaitable, Callable, List

from ..models import AudioChunk, Caption

CaptionCallback = Callable[[Caption], Awaitable[None]]


class ProviderAdapter(abc.ABC):
    #: stable id, matches the key in config "providers"
    id: str = "base"

    #: quota accounts consumed (filled from config)
    audio_accounts: List[str] = []
    char_accounts: List[str] = []

    @abc.abstractmethod
    async def warmup(self) -> bool:
        """Pre-connect / preload. Return True when ready to take over.

        Must be cheap and must NOT consume metered quota beyond a trivial
        handshake. Used for seamless background failover.
        """

    @abc.abstractmethod
    async def start_session(self, on_caption: CaptionCallback) -> None:
        ...

    @abc.abstractmethod
    async def feed_audio(self, chunk: AudioChunk) -> None:
        ...

    @abc.abstractmethod
    async def stop_session(self) -> None:
        ...
