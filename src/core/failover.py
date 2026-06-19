"""Failover state machine.

Pure-ish decision logic: given current quota usage and whether the next
provider has finished warming up, decide what to do. The Orchestrator
executes the actions (async warmup, sentence-boundary switch).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from .billing_guard import BillingGuard
from .quota import QuotaManager


class Action(str, Enum):
    CONTINUE = "continue"
    PREP = "prep"        # start warming up the next provider in the background
    SWITCH = "switch"    # next provider is ready; switch at sentence boundary
    STOP = "stop"        # no safe free option left; stop captions


@dataclass
class Decision:
    action: Action
    target_index: Optional[int] = None
    target_id: Optional[str] = None
    reason: str = ""


def provider_accounts(provider_cfg: Dict[str, Any], pid: str) -> List[str]:
    p = provider_cfg.get(pid, {})
    return list(p.get("audio_accounts", [])) + list(p.get("char_accounts", []))


class FailoverController:
    def __init__(
        self,
        chain: List[str],
        provider_cfg: Dict[str, Any],
        quota: QuotaManager,
        guard: BillingGuard,
        preemptive_at: float = 0.95,
        switch_timeout_s: float = 300.0,
    ):
        self._chain = chain
        self._pcfg = provider_cfg
        self._quota = quota
        self._guard = guard
        self._preemptive = preemptive_at
        self._timeout = switch_timeout_s

        self.current_index = 0
        self.prep_index: Optional[int] = None
        self.prep_started_at: Optional[float] = None

    # ----- identity helpers -------------------------------------------
    @property
    def active_id(self) -> str:
        return self._chain[self.current_index]

    def active_accounts(self) -> List[str]:
        return provider_accounts(self._pcfg, self.active_id)

    def _next_usable_index(self) -> Optional[int]:
        for i in range(self.current_index + 1, len(self._chain)):
            pid = self._chain[i]
            if self._guard.can_use(provider_accounts(self._pcfg, pid)).ok:
                return i
        return None

    # ----- state transitions ------------------------------------------
    def mark_prepping(self, index: int, now: float) -> None:
        self.prep_index = index
        self.prep_started_at = now

    def commit_switch(self, index: int) -> None:
        self.current_index = index
        self.prep_index = None
        self.prep_started_at = None

    # ----- core decision ----------------------------------------------
    def decide(self, now: float, prep_ready: bool) -> Decision:
        accounts = self.active_accounts()
        worst = self._quota.worst_fraction(accounts)
        nxt = self._next_usable_index()

        # 1) Past hard stop on the active provider -> must leave immediately.
        if self._quota.any_over_hard_stop(accounts):
            if nxt is not None and prep_ready and self.prep_index == nxt:
                return Decision(Action.SWITCH, nxt, self._chain[nxt],
                                "active exhausted; next is warmed up")
            return Decision(Action.STOP, reason="active exhausted; no warmed free fallback")

        # 2) Preemptive zone (e.g. >= 95%): warm up / switch ahead of time.
        if worst >= self._preemptive and nxt is not None:
            if self.prep_index != nxt:
                return Decision(Action.PREP, nxt, self._chain[nxt],
                                f"active at {worst:.0%}; warming up {self._chain[nxt]}")
            if prep_ready:
                return Decision(Action.SWITCH, nxt, self._chain[nxt],
                                "next warmed up; switch at sentence boundary")
            return Decision(Action.CONTINUE, reason="warming up next provider")

        # 3) Preemptive zone but nothing else free: ride it out; STOP handled at hard stop.
        return Decision(Action.CONTINUE)
