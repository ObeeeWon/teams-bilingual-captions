"""Text translators used by the split providers (#2 and #3).

Kept tiny and synchronous-friendly; the split provider calls translate() for
each FINAL English sentence only (cheaper + stabler subtitles).
"""
from __future__ import annotations

import abc
import os


class Translator(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    async def translate(self, text: str, source: str, target: str) -> str:
        ...


class AzureTranslator(Translator):
    """Azure Translator, F0 free tier = 2,000,000 chars / month.

    Env: AZURE_TRANSLATOR_KEY, AZURE_TRANSLATOR_REGION
    REST: POST https://api.cognitive.microsofttranslator.com/translate
    """
    name = "azure_translator"

    def __init__(self):
        self._key = os.getenv("AZURE_TRANSLATOR_KEY")
        self._region = os.getenv("AZURE_TRANSLATOR_REGION")

    async def translate(self, text: str, source: str, target: str) -> str:
        if not self._key:
            raise RuntimeError("AZURE_TRANSLATOR_KEY not set")
        # TODO: POST to the translate endpoint (use aiohttp/requests).
        raise NotImplementedError("Wire up Azure Translator REST call here")


class DeepLTranslator(Translator):
    """DeepL API Free = 500,000 chars / month. Endpoint api-free.deepl.com.

    Env: DEEPL_API_KEY
    """
    name = "deepl"

    def __init__(self):
        self._key = os.getenv("DEEPL_API_KEY")

    async def translate(self, text: str, source: str, target: str) -> str:
        if not self._key:
            raise RuntimeError("DEEPL_API_KEY not set")
        # TODO: use the `deepl` package or POST api-free.deepl.com/v2/translate
        raise NotImplementedError("Wire up DeepL call here")


def make_translator(name: str) -> Translator:
    if name == "azure_translator":
        return AzureTranslator()
    if name == "deepl":
        return DeepLTranslator()
    raise ValueError(f"unknown translator: {name}")
