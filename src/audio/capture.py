"""Audio sources.

Async generators that yield AudioChunk objects. Two real backends are
stubbed (ScreenCaptureKit for permission-friendly company laptops, BlackHole
for a virtual cable) plus a SimulatedSource used by the demo.
"""
from __future__ import annotations

import asyncio
from typing import AsyncIterator, Optional

from ..models import AudioChunk


class SimulatedSource:
    """Emits silent chunks on a wall-clock schedule so the pipeline runs
    without any audio hardware. `speed` compresses time for fast demos."""

    def __init__(self, sample_rate: int = 16000, chunk_ms: int = 200, speed: float = 1.0):
        self._sr = sample_rate
        self._chunk_ms = chunk_ms
        self._speed = max(speed, 0.001)

    async def stream(self) -> AsyncIterator[AudioChunk]:
        chunk_s = self._chunk_ms / 1000.0
        nbytes = int(self._sr * chunk_s) * 2  # 16-bit mono
        sleep_s = chunk_s / self._speed
        while True:
            await asyncio.sleep(sleep_s)
            yield AudioChunk(pcm=b"\x00" * nbytes, seconds=chunk_s, sample_rate=self._sr)


class MicrophoneSource:
    """Capture from the default microphone — quickest way to verify Azure works.

    Speak English into the mic; bilingual captions appear in the console.
    For Teams meetings you still need system audio (BlackHole) later.
    """

    def __init__(self, sample_rate: int = 16000, chunk_ms: int = 200, device=None):
        self._sr = sample_rate
        self._chunk_ms = chunk_ms
        self._device = device

    async def stream(self) -> AsyncIterator[AudioChunk]:
        try:
            import sounddevice as sd
            import numpy as np
        except ImportError:
            raise RuntimeError("pip install sounddevice numpy")

        chunk_s = self._chunk_ms / 1000.0
        block = int(self._sr * chunk_s)
        q: asyncio.Queue = asyncio.Queue(maxsize=32)
        loop = asyncio.get_running_loop()

        def callback(indata, frames, time_info, status):
            if status:
                print(f"[mic] {status}", flush=True)
            pcm = (indata[:, 0] * 32767).astype(np.int16).tobytes()
            loop.call_soon_threadsafe(q.put_nowait, pcm)

        stream = sd.InputStream(
            samplerate=self._sr, channels=1, dtype="float32",
            blocksize=block, device=self._device, callback=callback,
        )
        stream.start()
        print("[mic] 正在监听麦克风… 对着麦克风说英文测试。Ctrl+C 停止。", flush=True)
        try:
            while True:
                pcm = await q.get()
                yield AudioChunk(pcm=pcm, seconds=chunk_s, sample_rate=self._sr)
        finally:
            stream.stop()
            stream.close()


class BlackHoleSource:
    """Read system audio routed through BlackHole using sounddevice.

    Setup: install BlackHole 2ch, create a Multi-Output Device (speakers +
    BlackHole), set it as the system output. Then read from BlackHole here.
    """

    def __init__(self, sample_rate: int = 16000, chunk_ms: int = 200, device: str = "BlackHole"):
        self._sr = sample_rate
        self._chunk_ms = chunk_ms
        self._device_name = device

    def _find_device(self, sd):
        for i, d in enumerate(sd.query_devices()):
            if (self._device_name.lower() in d["name"].lower()
                    and d["max_input_channels"] > 0):
                return i
        raise RuntimeError(
            f"找不到 '{self._device_name}' 输入设备。"
            "请安装 BlackHole 并配置多输出设备。运行: python3 scripts/list_audio_devices.py")

    async def stream(self) -> AsyncIterator[AudioChunk]:
        try:
            import sounddevice as sd
            import numpy as np
        except ImportError:
            raise RuntimeError("pip install sounddevice numpy")

        dev = self._find_device(sd)
        chunk_s = self._chunk_ms / 1000.0
        block = int(self._sr * chunk_s)
        q: asyncio.Queue = asyncio.Queue(maxsize=32)
        loop = asyncio.get_running_loop()

        def callback(indata, frames, time_info, status):
            pcm = (indata[:, 0] * 32767).astype(np.int16).tobytes()
            loop.call_soon_threadsafe(q.put_nowait, pcm)

        stream = sd.InputStream(
            samplerate=self._sr, channels=1, dtype="float32",
            blocksize=block, device=dev, callback=callback,
        )
        stream.start()
        print(f"[audio] 正在从 {self._device_name} 采集系统音频… Ctrl+C 停止。", flush=True)
        try:
            while True:
                pcm = await q.get()
                yield AudioChunk(pcm=pcm, seconds=chunk_s, sample_rate=self._sr)
        finally:
            stream.stop()
            stream.close()


class ScreenCaptureKitSource:
    """Capture system audio via ScreenCaptureKit (macOS 13+), no virtual cable.

    Recommended for company laptops where installing BlackHole is blocked.
    Needs a small Swift/PyObjC bridge; requires Screen Recording permission.
    """

    def __init__(self, sample_rate: int = 16000, chunk_ms: int = 200):
        self._sr = sample_rate
        self._chunk_ms = chunk_ms

    async def stream(self) -> AsyncIterator[AudioChunk]:
        raise NotImplementedError("Bridge ScreenCaptureKit audio here")
        yield  # pragma: no cover


def make_source(cfg: dict, simulate: bool = False, speed: float = 1.0,
                backend: Optional[str] = None):
    audio = cfg.get("audio", {})
    sr = audio.get("sample_rate", 16000)
    chunk_ms = audio.get("chunk_ms", 200)
    if simulate:
        return SimulatedSource(sr, chunk_ms, speed=speed)
    backend = backend or audio.get("backend", "screencapturekit")
    if backend == "mic":
        return MicrophoneSource(sr, chunk_ms)
    if backend == "blackhole":
        return BlackHoleSource(sr, chunk_ms)
    if backend == "screencapturekit":
        return ScreenCaptureKitSource(sr, chunk_ms)
    raise ValueError(f"unknown audio backend: {backend}")
