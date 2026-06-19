"""The last line of defense against accidental charges.

Nothing here ever spends money. It only *blocks* actions that could.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .quota import QuotaManager


@dataclass
class GuardResult:
    ok: bool
    reason: str = ""


class BillingGuard:
    def __init__(self, billing_cfg: Dict[str, Any], quota: QuotaManager):
        self._cfg = billing_cfg
        self._quota = quota

    @property
    def allow_paid_fallback(self) -> bool:
        return bool(self._cfg.get("allow_paid_fallback", False))

    def preflight(self, deepgram_autoload_disabled: bool = True) -> GuardResult:
        """Startup safety check. Returns ok=False to refuse auto-failover."""
        if self.allow_paid_fallback:
            return GuardResult(False, "allow_paid_fallback is true; refuse to run unattended")
        if self._cfg.get("require_no_autoload", True) and not deepgram_autoload_disabled:
            return GuardResult(
                False,
                "Deepgram auto-reload may charge your card. Disable it in the "
                "Deepgram console, or set billing_safety.require_no_autoload: false.",
            )
        return GuardResult(True)

    def can_use(self, provider_accounts: List[str]) -> GuardResult:
        """A provider is usable only if none of its accounts are past hard stop."""
        if self._quota.any_over_hard_stop(provider_accounts):
            return GuardResult(False, "free allowance exhausted for this provider")
        return GuardResult(True)
