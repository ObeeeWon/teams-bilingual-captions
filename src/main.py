"""Entry point.

Real use:
    python3 -m src.main --ui qt

Demo without any keys / audio / GUI (recommended first run):
    python3 -m src.main --simulate --fast

The simulation drives the full pipeline (quota tracking, threshold warnings,
background warmup, sentence-boundary failover, and the safe hard stop) using
fabricated captions so you can watch the behavior end to end.
"""
from __future__ import annotations

import argparse
import asyncio
import copy
import os
import sys
from pathlib import Path
from typing import Any, Dict

from .audio.capture import make_source
from .config import load_config
from .core.billing_guard import BillingGuard
from .core.failover import FailoverController
from .core.notifier import Notifier
from .core.orchestrator import Orchestrator
from .core.quota import QuotaManager
from .env_loader import load_env, missing_vars
from .providers.registry import build_provider
from .ui.console import ConsoleUI

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _apply_fast_overrides(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Shrink limits so the whole failover chain plays out in ~15s."""
    cfg = copy.deepcopy(cfg)
    qa = cfg["quota_accounts"]
    qa["azure_audio"].update({"limit_seconds": 30, "hard_stop_at": 0.98,
                              "warn_at": [0.90, 0.95, 0.98]})
    qa["deepgram_credit"].update({"limit": 1.0})  # not the limiter in the demo
    # Finer char limits so the preemptive (90%) switch fires before the 95%
    # hard stop even though each sentence adds a chunk of characters at once.
    qa["azure_translator_chars"].update({"limit": 1200, "hard_stop_at": 0.95,
                                         "warn_at": [0.90, 0.95]})
    qa["deepl_chars"].update({"limit": 1200, "hard_stop_at": 0.95,
                              "warn_at": [0.90, 0.95]})
    cfg["failover"]["preemptive_switch_at"] = 0.90
    return cfg


def build_ui(mode: str):
    if mode == "qt":
        try:
            from .ui.subtitle_window import QtSubtitleWindow, _HAS_QT
            if _HAS_QT:
                return QtSubtitleWindow()
        except Exception:
            pass
        print("[warn] PyQt6 not available; falling back to console UI")
    return ConsoleUI()


async def run(args) -> None:
    simulate = getattr(args, "simulate", False)
    reset_quota = getattr(args, "reset_quota", False)
    fast = getattr(args, "fast", False)
    config_path = getattr(args, "config", "config.yaml")
    ui_mode = getattr(args, "ui", "console")
    audio = getattr(args, "audio", None)
    speed = getattr(args, "speed", 1.0)
    duration = getattr(args, "duration", None)

    cfg = load_config(config_path)
    if fast:
        cfg = _apply_fast_overrides(cfg)

    state_path = ".state/quota_state.sim.json" if simulate else ".state/quota_state.json"
    quota = QuotaManager(cfg["quota_accounts"], state_path=state_path)
    if simulate or reset_quota:
        for acc in cfg["quota_accounts"]:
            quota.reset_account(acc)

    guard = BillingGuard(cfg["billing_safety"], quota)
    controller = FailoverController(
        cfg["provider_chain"], cfg["providers"], quota, guard,
        preemptive_at=cfg["failover"]["preemptive_switch_at"],
        switch_timeout_s=cfg["failover"]["switch_timeout_s"],
    )
    notifier = Notifier(use_macos_notifications=not simulate)
    ui = build_ui(ui_mode)

    spp = 2.0 if fast else 3.0
    warmup_delay = 0.05 if fast else 1.0

    def factory(pid: str):
        return build_provider(
            pid, cfg, simulate=simulate,
            sim_seconds_per_sentence=spp,
        )

    # Inject a short warmup for the simulated demo so switches are snappy.
    if simulate:
        from .providers.simulation import SimulatedProvider
        orig = SimulatedProvider.__init__

        def patched(self, *a, **kw):
            kw.setdefault("warmup_delay", warmup_delay)
            orig(self, *a, **kw)

        SimulatedProvider.__init__ = patched  # type: ignore

    orch = Orchestrator(cfg, quota, guard, controller, notifier, ui, factory)
    audio_backend = audio or ("mic" if not simulate else None)
    source = make_source(cfg, simulate=simulate, speed=speed,
                         backend=audio_backend)
    await orch.run(source, max_seconds=duration)


def check_keys() -> int:
    load_env(PROJECT_ROOT)
    required = ["AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION"]
    optional = ["AZURE_TRANSLATOR_KEY", "DEEPGRAM_API_KEY"]
    miss = missing_vars(required)
    if miss:
        print("缺少必填项（请编辑 keys.env）:")
        for m in miss:
            print(f"  - {m}")
        print(f"\n文件位置: {PROJECT_ROOT / 'keys.env'}")
        return 1
    print("Azure Speech 密钥: OK")
    for m in optional:
        status = "已配置" if os.getenv(m, "").strip() else "未配置（备用方案暂不可用）"
        print(f"  {m}: {status}")
    try:
        import azure.cognitiveservices.speech  # noqa: F401
        print("Azure Speech SDK: 已安装")
    except ImportError:
        print("Azure Speech SDK: 未安装 → pip install azure-cognitiveservices-speech")
        return 1
    return 0


def main() -> None:
    os.chdir(PROJECT_ROOT)
    load_env(PROJECT_ROOT)

    p = argparse.ArgumentParser(description="Teams bilingual real-time captions")
    p.add_argument("--config", default="config.yaml")
    p.add_argument("--check-keys", action="store_true",
                   help="verify keys.env and SDK without starting a session")
    p.add_argument("--skip-bootstrap", action="store_true",
                   help="skip auto dependency install and first-run setup")
    p.add_argument("--simulate", action="store_true",
                   help="run the full pipeline with fake captions (no keys/audio)")
    p.add_argument("--fast", action="store_true",
                   help="shrink free quotas so failover/stop happen in ~15s")
    p.add_argument("--speed", type=float, default=1.0,
                   help="simulated audio speed multiplier (e.g. 4 = 4x faster)")
    p.add_argument("--duration", type=float, default=None,
                   help="auto-stop after N seconds (default: run until Ctrl+C)")
    p.add_argument("--ui", choices=["console", "qt"], default="console")
    p.add_argument("--audio", choices=["mic", "blackhole", "screencapturekit"],
                   default=None,
                   help="audio source (default: mic for quick test; set blackhole for Teams)")
    p.add_argument("--reset-quota", action="store_true",
                   help="reset local free-tier usage counters before starting")
    args = p.parse_args()

    if args.check_keys:
        from .bootstrap import ensure_ready
        ensure_ready(PROJECT_ROOT, quiet_hints=True)
        sys.exit(check_keys())

    if not args.skip_bootstrap:
        from .bootstrap import ensure_ready
        if not ensure_ready(PROJECT_ROOT, quiet_hints=False):
            if not args.simulate:
                print("\n[error] 环境未就绪。可手动运行: ./scripts/setup.sh", flush=True)
                sys.exit(1)

    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        print("\n[exit] stopped by user")


if __name__ == "__main__":
    main()
