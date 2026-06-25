"""Configuration loading.

The full default config lives here as a Python dict so the app (and the
--simulate demo) runs with zero third-party dependencies. If a config.yaml
is present *and* PyYAML is installed, it is deep-merged on top of the defaults.
"""
from __future__ import annotations

import copy
import os
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "audio": {
        "backend": "screencapturekit",
        "sample_rate": 16000,
        "channels": 1,
        "chunk_ms": 200,
    },
    "translate": {"source_lang": "en-US", "target_lang": "zh"},
    "ui": {
        "mode": "console",
        "history_lines": 3,
        "show_partial_en": True,
        "translate_partial": False,
    },
    "quota_accounts": {
        "azure_audio": {
            "kind": "monthly_audio",
            "limit_seconds": 18000,
            "reset": "rolling_30d",
            "warn_at": [0.90, 0.95, 0.98],
            "hard_stop_at": 0.98,
        },
        "deepgram_credit": {
            "kind": "credit_usd",
            "limit": 200,
            "usd_per_audio_second": 0.000128,
            "reset": "never",
            "warn_at": [0.90, 0.95],
            "hard_stop_at": 0.95,
        },
        "azure_translator_chars": {
            "kind": "monthly_chars",
            "limit": 2000000,
            "reset": "rolling_30d",
            "warn_at": [0.90, 0.95],
            "hard_stop_at": 0.95,
        },
        "deepl_chars": {
            "kind": "monthly_chars",
            "limit": 500000,
            "reset": "rolling_30d",
            "warn_at": [0.90, 0.95],
            "hard_stop_at": 0.95,
        },
    },
    "providers": {
        "azure_speech_translation": {
            "type": "integrated",
            "audio_accounts": ["azure_audio"],
            "char_accounts": [],
        },
        "deepgram_azure_translator": {
            "type": "split",
            "stt": "deepgram",
            "translate": "azure_translator",
            "audio_accounts": ["deepgram_credit"],
            "char_accounts": ["azure_translator_chars"],
        },
        "deepgram_deepl": {
            "type": "split",
            "stt": "deepgram",
            "translate": "deepl",
            "audio_accounts": ["deepgram_credit"],
            "char_accounts": ["deepl_chars"],
        },
        "local_lightweight": {
            "type": "local",
            "enabled": False,
            "audio_accounts": [],
            "char_accounts": [],
        },
    },
    "provider_chain": [
        "azure_speech_translation",
        "deepgram_azure_translator",
        "deepgram_deepl",
    ],
    "failover": {
        "enabled": True,
        "preemptive_switch_at": 0.95,
        "switch_timeout_s": 300,
        "switch_on": "sentence_boundary",
    },
    "billing_safety": {
        "allow_paid_fallback": False,
        "require_no_autoload": True,
        "stop_before_exhaustion": True,
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def load_config(path: str = "config.yaml") -> Dict[str, Any]:
    """Load defaults, then merge config.yaml on top if available."""
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    if not path or not os.path.exists(path):
        return cfg
    try:
        import yaml  # type: ignore
    except ImportError:
        return cfg
    with open(path, "r", encoding="utf-8") as fh:
        user_cfg = yaml.safe_load(fh) or {}
    return _deep_merge(cfg, user_cfg)
