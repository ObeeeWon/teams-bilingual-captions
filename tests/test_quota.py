import os
import tempfile

from src.core.quota import QuotaManager, ROLLING_30D


def _cfg():
    return {
        "azure_audio": {"kind": "monthly_audio", "limit_seconds": 100,
                        "reset": "rolling_30d", "warn_at": [0.9], "hard_stop_at": 0.98},
        "deepgram_credit": {"kind": "credit_usd", "limit": 1.0,
                            "usd_per_audio_second": 0.001, "reset": "never",
                            "warn_at": [0.9], "hard_stop_at": 0.95},
        "chars": {"kind": "monthly_chars", "limit": 1000, "reset": "rolling_30d",
                  "warn_at": [0.9], "hard_stop_at": 0.95},
    }


def _qm(tmp, clock):
    return QuotaManager(_cfg(), state_path=os.path.join(tmp, "q.json"), clock=clock)


def test_audio_seconds_accumulate_and_fraction():
    with tempfile.TemporaryDirectory() as tmp:
        q = _qm(tmp, lambda: 1000.0)
        q.record(["azure_audio"], audio_seconds=49)
        assert abs(q.status("azure_audio").fraction - 0.49) < 1e-6
        assert q.status("azure_audio").remaining == 51


def test_credit_usd_conversion():
    with tempfile.TemporaryDirectory() as tmp:
        q = _qm(tmp, lambda: 0.0)
        q.record(["deepgram_credit"], audio_seconds=500)  # 500 * 0.001 = 0.5 usd
        assert abs(q.status("deepgram_credit").fraction - 0.5) < 1e-6


def test_chars_hard_stop():
    with tempfile.TemporaryDirectory() as tmp:
        q = _qm(tmp, lambda: 0.0)
        q.record(["chars"], chars=960)
        assert q.any_over_hard_stop(["chars"]) is True


def test_persistence_across_instances():
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "q.json")
        q1 = QuotaManager(_cfg(), state_path=path, clock=lambda: 0.0)
        q1.record(["azure_audio"], audio_seconds=30)
        q2 = QuotaManager(_cfg(), state_path=path, clock=lambda: 0.0)
        assert q2.status("azure_audio").used == 30


def test_rolling_reset():
    now = [0.0]
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "q.json")
        q = QuotaManager(_cfg(), state_path=path, clock=lambda: now[0])
        q.record(["azure_audio"], audio_seconds=50)
        assert q.status("azure_audio").used == 50
        now[0] = ROLLING_30D + 1
        # next record triggers reset before adding
        q.record(["azure_audio"], audio_seconds=5)
        assert q.status("azure_audio").used == 5


def test_remaining_seconds_credit():
    with tempfile.TemporaryDirectory() as tmp:
        q = _qm(tmp, lambda: 0.0)
        # hard stop 0.95 of $1 at $0.001/s => 950 seconds budget
        rem = q.remaining_seconds(["deepgram_credit"])
        assert abs(rem - 950) < 1e-6
