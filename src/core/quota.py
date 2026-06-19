"""Local-first quota tracking with persistence and cycle resets.

We track usage *locally* (not just via cloud errors) so failover can begin
BEFORE a free tier is exhausted. Each account stores its consumed amount in
its native unit:
  - monthly_audio -> seconds
  - credit_usd    -> USD
  - monthly_chars -> characters
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..models import QuotaKind

ROLLING_30D = 30 * 24 * 3600


@dataclass
class AccountStatus:
    account_id: str
    kind: QuotaKind
    used: float          # native unit
    limit: float         # native unit
    fraction: float      # used / limit (clamped >= 0)
    warn_at: List[float]
    hard_stop_at: float

    @property
    def remaining(self) -> float:
        return max(0.0, self.limit - self.used)

    @property
    def over_hard_stop(self) -> bool:
        return self.fraction >= self.hard_stop_at


class QuotaManager:
    def __init__(
        self,
        accounts_cfg: Dict[str, Dict[str, Any]],
        state_path: str = ".state/quota_state.json",
        clock=time.time,
    ):
        self._cfg = accounts_cfg
        self._state_path = state_path
        self._clock = clock
        # state[account] = {"used": float, "period_start": epoch}
        self._state: Dict[str, Dict[str, float]] = {}
        self._load()
        self._ensure_accounts()

    # ----- persistence -------------------------------------------------
    def _load(self) -> None:
        if os.path.exists(self._state_path):
            try:
                with open(self._state_path, "r", encoding="utf-8") as fh:
                    self._state = json.load(fh)
            except (json.JSONDecodeError, OSError):
                self._state = {}

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self._state_path) or ".", exist_ok=True)
        tmp = self._state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self._state, fh, indent=2)
        os.replace(tmp, self._state_path)

    def _ensure_accounts(self) -> None:
        now = self._clock()
        for acc in self._cfg:
            self._state.setdefault(acc, {"used": 0.0, "period_start": now})
        self._apply_resets()

    # ----- reset logic -------------------------------------------------
    def _apply_resets(self) -> None:
        now = self._clock()
        changed = False
        for acc, cfg in self._cfg.items():
            reset = cfg.get("reset", "never")
            st = self._state[acc]
            if reset == "rolling_30d" and now - st.get("period_start", now) >= ROLLING_30D:
                st["used"] = 0.0
                st["period_start"] = now
                changed = True
        if changed:
            self._save()

    # ----- unit conversion --------------------------------------------
    def _to_native(self, account: str, audio_seconds: float, chars: int) -> float:
        cfg = self._cfg[account]
        kind = cfg["kind"]
        if kind == QuotaKind.MONTHLY_AUDIO.value:
            return audio_seconds
        if kind == QuotaKind.CREDIT_USD.value:
            return audio_seconds * float(cfg.get("usd_per_audio_second", 0.0))
        if kind == QuotaKind.MONTHLY_CHARS.value:
            return float(chars)
        return 0.0

    def _limit(self, account: str) -> float:
        cfg = self._cfg[account]
        if cfg["kind"] == QuotaKind.MONTHLY_AUDIO.value:
            return float(cfg["limit_seconds"])
        return float(cfg["limit"])

    # ----- recording ---------------------------------------------------
    def record(self, accounts: List[str], audio_seconds: float = 0.0, chars: int = 0) -> None:
        self._apply_resets()
        for acc in accounts:
            if acc not in self._cfg:
                continue
            self._state[acc]["used"] += self._to_native(acc, audio_seconds, chars)
        self._save()

    # ----- queries -----------------------------------------------------
    def status(self, account: str) -> AccountStatus:
        cfg = self._cfg[account]
        limit = self._limit(account)
        used = self._state[account]["used"]
        frac = (used / limit) if limit > 0 else 1.0
        return AccountStatus(
            account_id=account,
            kind=QuotaKind(cfg["kind"]),
            used=used,
            limit=limit,
            fraction=max(0.0, frac),
            warn_at=list(cfg.get("warn_at", [])),
            hard_stop_at=float(cfg.get("hard_stop_at", 1.0)),
        )

    def worst_fraction(self, accounts: List[str]) -> float:
        """Highest used-fraction across the given accounts (0 if none)."""
        return max((self.status(a).fraction for a in accounts if a in self._cfg), default=0.0)

    def any_over_hard_stop(self, accounts: List[str]) -> bool:
        return any(self.status(a).over_hard_stop for a in accounts if a in self._cfg)

    def remaining_seconds(self, accounts: List[str]) -> Optional[float]:
        """Estimate remaining audio seconds before the first hard stop."""
        best: Optional[float] = None
        for acc in accounts:
            if acc not in self._cfg:
                continue
            st = self.status(acc)
            cfg = self._cfg[acc]
            allowance = st.hard_stop_at * st.limit - st.used
            if st.kind == QuotaKind.MONTHLY_AUDIO:
                secs = allowance
            elif st.kind == QuotaKind.CREDIT_USD:
                rate = float(cfg.get("usd_per_audio_second", 0.0))
                secs = allowance / rate if rate > 0 else None
            else:
                continue  # char accounts: not time-bounded here
            if secs is None:
                continue
            best = secs if best is None else min(best, secs)
        return best

    def reset_account(self, account: str) -> None:
        self._state[account] = {"used": 0.0, "period_start": self._clock()}
        self._save()
