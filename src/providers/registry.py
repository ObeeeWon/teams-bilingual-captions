"""Builds provider instances from config, or simulated stand-ins for the demo."""
from __future__ import annotations

from typing import Any, Dict

from .azure_speech_translation import AzureSpeechTranslationProvider
from .base import ProviderAdapter
from .simulation import SimulatedProvider
from .split_provider import SplitProvider


def build_provider(pid: str, cfg: Dict[str, Any], simulate: bool = False,
                   sim_seconds_per_sentence: float = 3.0) -> ProviderAdapter:
    pconf = cfg["providers"][pid]
    audio_accounts = list(pconf.get("audio_accounts", []))
    char_accounts = list(pconf.get("char_accounts", []))

    if simulate:
        return SimulatedProvider(
            pid, audio_accounts, char_accounts,
            seconds_per_sentence=sim_seconds_per_sentence,
        )

    ptype = pconf.get("type")
    tr = cfg.get("translate", {})
    if ptype == "integrated":
        return AzureSpeechTranslationProvider(
            pid, audio_accounts, char_accounts,
            source_lang=tr.get("source_lang", "en-US"),
            target_lang=tr.get("target_lang", "zh"),
        )
    if ptype == "split":
        return SplitProvider(
            pid, pconf["stt"], pconf["translate"],
            audio_accounts, char_accounts,
            source_lang=tr.get("source_lang", "en"),
            target_lang=tr.get("target_lang", "zh"),
        )
    raise ValueError(f"provider '{pid}' has unsupported type '{ptype}' "
                     f"(local fallback not bundled in this scaffold)")
