import os
import tempfile

from src.core.billing_guard import BillingGuard
from src.core.failover import Action, FailoverController
from src.core.quota import QuotaManager

PROVIDERS = {
    "a": {"audio_accounts": ["audio_a"], "char_accounts": []},
    "b": {"audio_accounts": ["credit_b"], "char_accounts": ["chars_b"]},
    "c": {"audio_accounts": ["credit_b"], "char_accounts": ["chars_c"]},
}
CHAIN = ["a", "b", "c"]


def _accounts():
    return {
        "audio_a": {"kind": "monthly_audio", "limit_seconds": 100, "reset": "never",
                    "warn_at": [], "hard_stop_at": 0.98},
        "credit_b": {"kind": "credit_usd", "limit": 100.0, "usd_per_audio_second": 0.0001,
                     "reset": "never", "warn_at": [], "hard_stop_at": 0.95},
        "chars_b": {"kind": "monthly_chars", "limit": 100, "reset": "never",
                    "warn_at": [], "hard_stop_at": 0.95},
        "chars_c": {"kind": "monthly_chars", "limit": 100, "reset": "never",
                    "warn_at": [], "hard_stop_at": 0.95},
    }


def _make(tmp):
    q = QuotaManager(_accounts(), state_path=os.path.join(tmp, "q.json"), clock=lambda: 0.0)
    guard = BillingGuard({"allow_paid_fallback": False}, q)
    fc = FailoverController(CHAIN, PROVIDERS, q, guard, preemptive_at=0.90)
    return q, fc


def test_continue_when_plenty_left():
    with tempfile.TemporaryDirectory() as tmp:
        q, fc = _make(tmp)
        q.record(["audio_a"], audio_seconds=10)  # 10%
        assert fc.decide(0.0, prep_ready=False).action == Action.CONTINUE


def test_prep_then_switch_at_preemptive():
    with tempfile.TemporaryDirectory() as tmp:
        q, fc = _make(tmp)
        q.record(["audio_a"], audio_seconds=92)  # 92% > 90% preemptive
        d1 = fc.decide(0.0, prep_ready=False)
        assert d1.action == Action.PREP and d1.target_index == 1
        fc.mark_prepping(1, 0.0)
        d2 = fc.decide(1.0, prep_ready=True)
        assert d2.action == Action.SWITCH and d2.target_index == 1


def test_switch_advances_active():
    with tempfile.TemporaryDirectory() as tmp:
        q, fc = _make(tmp)
        fc.commit_switch(1)
        assert fc.active_id == "b"
        assert set(fc.active_accounts()) == {"credit_b", "chars_b"}


def test_stop_when_last_provider_exhausted():
    with tempfile.TemporaryDirectory() as tmp:
        q, fc = _make(tmp)
        fc.commit_switch(2)  # provider c is last
        q.record(["chars_c"], chars=96)  # over 0.95 hard stop
        assert fc.decide(0.0, prep_ready=False).action == Action.STOP


def test_shared_credit_blocks_sibling_provider():
    # If b exhausts the SHARED credit account, c (also on credit_b) is unusable.
    with tempfile.TemporaryDirectory() as tmp:
        q, fc = _make(tmp)
        fc.commit_switch(1)  # active b
        q.record(["credit_b"], audio_seconds=960000)  # blow past 95% of $100
        # active b exhausted, c shares credit_b -> no usable next -> STOP
        assert fc.decide(0.0, prep_ready=False).action == Action.STOP
