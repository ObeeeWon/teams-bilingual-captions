"""Split provider: a streaming STT (e.g. Deepgram) + a separate translator.

Used for providers #2 (Deepgram + Azure Translator) and #3 (Deepgram + DeepL).
Partial English is emitted immediately; the translator is invoked only on
FINAL sentences to save characters and keep the Chinese line stable.
"""
from __future__ import annotations

import os
from typing import List, Optional

from ..models import AudioChunk, Caption
from .base import CaptionCallback, ProviderAdapter
from .translators import Translator, make_translator


class DeepgramSTT:
    """Deepgram streaming STT. $200 signup credit (no expiry).

    Env: DEEPGRAM_API_KEY ; WSS: wss://api.deepgram.com/v1/listen
    Emits interim_results (partial) and is_final segments.
    """

    def __init__(self):
        self._key = os.getenv("DEEPGRAM_API_KEY")

    async def warmup(self) -> bool:
        return bool(self._key)

    # TODO: open the websocket, stream PCM, surface partial/final transcripts.


class SplitProvider(ProviderAdapter):
    def __init__(self, provider_id: str, stt_name: str, translate_name: str,
                 audio_accounts: List[str], char_accounts: List[str],
                 source_lang: str = "en", target_lang: str = "zh"):
        self.id = provider_id
        self.audio_accounts = audio_accounts
        self.char_accounts = char_accounts
        self._source = source_lang
        self._target = target_lang
        self._stt = DeepgramSTT() if stt_name == "deepgram" else None
        self._translator: Translator = make_translator(translate_name)
        self._on_caption: Optional[CaptionCallback] = None

    async def warmup(self) -> bool:
        return bool(self._stt and await self._stt.warmup())

    async def start_session(self, on_caption: CaptionCallback) -> None:
        self._on_caption = on_caption
        # TODO: open Deepgram ws; on partial -> emit Caption(is_final=False);
        #       on final -> translate then emit Caption(is_final=True).
        raise NotImplementedError("Wire up Deepgram streaming + translator here")

    async def feed_audio(self, chunk: AudioChunk) -> None:
        raise NotImplementedError

    async def stop_session(self) -> None:
        self._on_caption = None

    async def _on_final_english(self, text: str) -> None:
        zh = await self._translator.translate(text, self._source, self._target)
        if self._on_caption:
            await self._on_caption(Caption(
                text_en=text, text_zh=zh, is_final=True, provider_id=self.id))
