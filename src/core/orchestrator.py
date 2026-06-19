"""The conductor: audio -> active provider -> captions -> UI, with quota
tracking, background warmup, and seamless sentence-boundary failover.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Dict, Optional

from ..models import AudioChunk, Caption, Severity
from ..providers.base import ProviderAdapter
from .billing_guard import BillingGuard
from .failover import Action, FailoverController
from .notifier import Notifier, ThresholdTracker
from .quota import QuotaManager

ProviderFactory = Callable[[str], ProviderAdapter]


def _fmt_secs(seconds: Optional[float]) -> str:
    if seconds is None:
        return "?"
    seconds = max(0, int(seconds))
    return f"{seconds // 60}m{seconds % 60:02d}s"


class Orchestrator:
    def __init__(
        self,
        cfg: Dict[str, Any],
        quota: QuotaManager,
        guard: BillingGuard,
        controller: FailoverController,
        notifier: Notifier,
        ui,
        provider_factory: ProviderFactory,
        clock: Callable[[], float] = time.time,
    ):
        self._cfg = cfg
        self._quota = quota
        self._guard = guard
        self._fc = controller
        self._notifier = notifier
        self._ui = ui
        self._make = provider_factory
        self._clock = clock
        self._thresholds = ThresholdTracker()

        self._active: Optional[ProviderAdapter] = None
        self._prepared: Optional[ProviderAdapter] = None
        self._prep_ready = False
        self._prep_task: Optional[asyncio.Task] = None
        self._pending_switch: Optional[int] = None
        self._boundary = False
        self._stopped = False

    # ----- caption handling -------------------------------------------
    async def _on_caption(self, cap: Caption) -> None:
        if cap.is_final and self._active is not None:
            self._quota.record(self._active.char_accounts, chars=len(cap.text_en))
            self._boundary = True
        self._ui.update_caption(cap)

    # ----- warmup / switch --------------------------------------------
    async def _warmup(self, index: int) -> None:
        pid = self._fc_chain()[index]
        provider = self._make(pid)
        ok = await provider.warmup()
        if ok:
            self._prepared = provider
            self._prep_ready = True
            self._notifier.notify(Severity.TOAST, "备用方案就绪",
                                  f"{pid} 已预热，将在句子结束时切换")

    def _fc_chain(self):
        return self._cfg["provider_chain"]

    async def _switch_to(self, index: int) -> None:
        if self._prepared is None:
            return
        old = self._active
        if old is not None:
            await old.stop_session()
        self._active = self._prepared
        self._prepared = None
        self._prep_ready = False
        self._pending_switch = None
        self._fc.commit_switch(index)
        await self._active.start_session(self._on_caption)
        self._notifier.notify(Severity.TOAST, "已切换免费方案",
                              f"现在使用 {self._active.id}")
        self._update_status()

    # ----- thresholds / status ----------------------------------------
    def _check_thresholds(self) -> None:
        for acc in self._fc.active_accounts():
            st = self._quota.status(acc)
            for t in self._thresholds.crossed(acc, st.fraction, st.warn_at):
                sev = Severity.MODAL if t >= 0.95 else Severity.TOAST
                self._notifier.notify(
                    sev, "免费额度提醒",
                    f"{acc} 已用 {st.fraction:.0%}（剩余约 {_fmt_secs(self._quota.remaining_seconds([acc]))}）",
                )

    def _update_status(self) -> None:
        accounts = self._fc.active_accounts()
        worst = self._quota.worst_fraction(accounts)
        free_pct = max(0, round((1 - worst) * 100))
        # Coarsen to 10% steps so the console line only updates meaningfully.
        bucket = (free_pct // 10) * 10
        self._ui.set_status(f"{self._fc.active_id} · 免费剩余 ~{bucket}%")

    # ----- main loop ---------------------------------------------------
    async def run(self, source, max_seconds: Optional[float] = None) -> None:
        pre = self._guard.preflight()
        if not pre.ok:
            self._notifier.notify(Severity.MODAL, "安全检查未通过", pre.reason)

        self._active = self._make(self._fc.active_id)
        await self._active.warmup()
        await self._active.start_session(self._on_caption)
        self._update_status()

        start = self._clock()
        async for chunk in source.stream():
            if self._stopped:
                break
            if max_seconds is not None and self._clock() - start >= max_seconds:
                break

            await self._active.feed_audio(chunk)
            self._quota.record(self._active.audio_accounts, audio_seconds=chunk.seconds)

            self._check_thresholds()
            await self._tick()
            if self._stopped:
                break

            if self._pending_switch is not None and self._boundary:
                self._boundary = False
                await self._switch_to(self._pending_switch)

            self._update_status()

        await self._shutdown()

    async def _tick(self) -> None:
        now = self._clock()
        decision = self._fc.decide(now, self._prep_ready)

        if decision.action == Action.PREP:
            if self._prep_task is None or self._prep_task.done():
                self._fc.mark_prepping(decision.target_index, now)
                self._prep_ready = False
                self._notifier.notify(Severity.INFO, "后台预热", decision.reason)
                self._prep_task = asyncio.create_task(self._warmup(decision.target_index))

        elif decision.action == Action.SWITCH:
            self._pending_switch = decision.target_index

        elif decision.action == Action.STOP:
            self._notifier.notify(
                Severity.HARD_STOP, "免费额度已用尽",
                "为避免产生费用，字幕已停止。会议不受影响。")
            self._ui.freeze("免费额度已用尽，字幕已停止（未产生任何费用）")
            self._stopped = True

    async def _shutdown(self) -> None:
        if self._prep_task and not self._prep_task.done():
            self._prep_task.cancel()
        if self._active is not None:
            try:
                await self._active.stop_session()
            except NotImplementedError:
                pass
