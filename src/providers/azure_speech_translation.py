"""Provider #1: Azure Speech Translation (integrated STT + EN->ZH).

Free tier: 5 audio hours / month (F0).

Env (loaded from keys.env / .env):
  AZURE_SPEECH_KEY, AZURE_SPEECH_REGION
"""
from __future__ import annotations

import asyncio
import os
from typing import List, Optional

from ..models import AudioChunk, Caption
from .base import CaptionCallback, ProviderAdapter

try:
    import azure.cognitiveservices.speech as speechsdk
    _HAS_SDK = True
except ImportError:
    _HAS_SDK = False


def _azure_recognition_language(lang: str) -> str:
    """STT input needs a BCP-47 locale, e.g. en-US (not bare 'en')."""
    if "-" in lang:
        return lang
    return {"en": "en-US", "zh": "zh-CN"}.get(lang.lower(), lang)


def _azure_translation_target(lang: str) -> str:
    """Translation targets use short codes, e.g. zh (not zh-Hans)."""
    lang = lang.lower()
    if lang.startswith("zh"):
        return "zh"
    return lang.split("-")[0]


class AzureSpeechTranslationProvider(ProviderAdapter):
    def __init__(self, provider_id: str, audio_accounts: List[str],
                 char_accounts: List[str], source_lang: str = "en",
                 target_lang: str = "zh-Hans"):
        self.id = provider_id
        self.audio_accounts = audio_accounts
        self.char_accounts = char_accounts
        self._source = _azure_recognition_language(source_lang)
        self._target = _azure_translation_target(target_lang)
        self._on_caption: Optional[CaptionCallback] = None
        self._key = os.getenv("AZURE_SPEECH_KEY", "").strip()
        self._region = os.getenv("AZURE_SPEECH_REGION", "").strip()

        self._recognizer = None
        self._push_stream = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def warmup(self) -> bool:
        if not (_HAS_SDK and self._key and self._region):
            return False
        return True

    async def start_session(self, on_caption: CaptionCallback) -> None:
        if not _HAS_SDK:
            raise RuntimeError(
                "azure-cognitiveservices-speech not installed. "
                "Run: pip install azure-cognitiveservices-speech")
        if not (self._key and self._region):
            raise RuntimeError(
                "AZURE_SPEECH_KEY / AZURE_SPEECH_REGION not set. "
                "Fill them in keys.env (project root).")

        self._on_caption = on_caption
        self._loop = asyncio.get_running_loop()

        tcfg = speechsdk.translation.SpeechTranslationConfig(
            subscription=self._key, region=self._region)
        tcfg.speech_recognition_language = self._source
        tcfg.add_target_language(self._target)
        print(f"[azure] 识别语言={self._source}  翻译目标={self._target}  区域={self._region}",
              flush=True)

        fmt = speechsdk.audio.AudioStreamFormat(
            samples_per_second=16000, bits_per_sample=16, channels=1)
        self._push_stream = speechsdk.audio.PushAudioInputStream(fmt)
        audio_cfg = speechsdk.audio.AudioConfig(stream=self._push_stream)

        self._recognizer = speechsdk.translation.TranslationRecognizer(
            translation_config=tcfg, audio_config=audio_cfg)

        self._recognizer.recognizing.connect(self._on_recognizing)
        self._recognizer.recognized.connect(self._on_recognized)
        self._recognizer.canceled.connect(self._on_canceled)

        self._recognizer.start_continuous_recognition_async().get()

    def _emit(self, caption: Caption) -> None:
        if self._on_caption is None or self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._on_caption(caption), self._loop)

    def _on_recognizing(self, evt) -> None:
        if evt.result.reason != speechsdk.ResultReason.TranslatingSpeech:
            return
        en = evt.result.text or ""
        if not en:
            return
        zh = evt.result.translations.get(self._target) or ""
        if not zh and evt.result.translations:
            zh = next(iter(evt.result.translations.values()), "")
        self._emit(Caption(text_en=en, text_zh=zh, is_final=False, provider_id=self.id))

    def _on_recognized(self, evt) -> None:
        if evt.result.reason != speechsdk.ResultReason.TranslatedSpeech:
            return
        en = evt.result.text or ""
        if not en:
            return
        zh = evt.result.translations.get(self._target) or ""
        if not zh and evt.result.translations:
            zh = next(iter(evt.result.translations.values()), "")
        self._emit(Caption(text_en=en, text_zh=zh, is_final=True, provider_id=self.id))

    def _on_canceled(self, evt) -> None:
        details = evt.result.cancellation_details
        print(f"[azure] canceled: {details.reason} — {details.error_details}", flush=True)

    async def feed_audio(self, chunk: AudioChunk) -> None:
        if self._push_stream is not None and chunk.pcm:
            self._push_stream.write(chunk.pcm)

    async def stop_session(self) -> None:
        if self._recognizer is not None:
            self._recognizer.stop_continuous_recognition_async().get()
            self._recognizer = None
        if self._push_stream is not None:
            self._push_stream.close()
            self._push_stream = None
        self._on_caption = None
