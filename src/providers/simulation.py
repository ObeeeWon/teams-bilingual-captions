"""A fake provider so the whole pipeline (quota + failover + UI) can be run
and demonstrated with no API keys, no audio device, and no network.

It turns elapsed audio time into partial/final captions drawn from a small
script, and fabricates a "translation" by tagging the provider id.
"""
from __future__ import annotations

import asyncio
from typing import List, Optional

from ..models import AudioChunk, Caption
from .base import CaptionCallback, ProviderAdapter

_SCRIPT = [
    ("Thanks everyone for joining the call today.", "感谢大家今天加入通话。"),
    ("Let's start with a quick status update.", "我们先快速同步一下进展。"),
    ("The new feature is almost ready for review.", "新功能基本可以进入评审了。"),
    ("We hit a small issue with the audio pipeline.", "我们在音频管道上遇到一个小问题。"),
    ("Can you share your screen for a moment?", "你能分享一下屏幕吗？"),
    ("That makes sense, let's move forward.", "有道理，我们继续推进。"),
    ("I'll follow up with the details after the meeting.", "会后我会跟进具体细节。"),
    ("Any questions before we wrap up?", "结束之前还有问题吗？"),
]


class SimulatedProvider(ProviderAdapter):
    def __init__(
        self,
        provider_id: str,
        audio_accounts: List[str],
        char_accounts: List[str],
        seconds_per_sentence: float = 3.0,
        warmup_delay: float = 1.0,
    ):
        self.id = provider_id
        self.audio_accounts = audio_accounts
        self.char_accounts = char_accounts
        self._spp = seconds_per_sentence
        self._warmup_delay = warmup_delay

        self._on_caption: Optional[CaptionCallback] = None
        self._accum = 0.0
        self._idx = 0
        self._emitted_partial = False
        self._warm = False

    async def warmup(self) -> bool:
        await asyncio.sleep(self._warmup_delay)
        self._warm = True
        return True

    async def start_session(self, on_caption: CaptionCallback) -> None:
        self._on_caption = on_caption
        self._accum = 0.0
        self._emitted_partial = False

    async def feed_audio(self, chunk: AudioChunk) -> None:
        if self._on_caption is None:
            return
        self._accum += chunk.seconds
        en, zh = _SCRIPT[self._idx % len(_SCRIPT)]

        # Halfway through a sentence: emit a partial (English only).
        if not self._emitted_partial and self._accum >= self._spp * 0.4:
            self._emitted_partial = True
            await self._on_caption(Caption(
                text_en=en, text_zh="", is_final=False, provider_id=self.id))

        # End of sentence: emit the final with translation.
        if self._accum >= self._spp:
            self._accum = 0.0
            self._emitted_partial = False
            self._idx += 1
            await self._on_caption(Caption(
                text_en=en, text_zh=zh, is_final=True, provider_id=self.id))

    async def stop_session(self) -> None:
        self._on_caption = None
