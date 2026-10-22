"""Server message-flow tests with a fake mic and a stub VAD. Logic only, no accuracy claims."""
from __future__ import annotations

import asyncio
import json

import numpy as np

import server
from endpointer import FRAME_SAMPLES
from vad_config import load_config


class FakeWs:
    def __init__(self, incoming: list[dict]) -> None:
        self._incoming = [json.dumps(m) for m in incoming]
        self.sent: list[dict] = []

    def __aiter__(self):
        async def gen():
            for raw in self._incoming:
                yield raw
        return gen()

    async def send(self, raw: str) -> None:
        self.sent.append(json.loads(raw))


class StubVad:
    def reset(self) -> None:
        pass

    def __call__(self, frame: np.ndarray) -> float:
        return 1.0 if float(np.abs(frame).max()) > 0.1 else 0.0


def make_fake_mic(frames: list[np.ndarray]):
    class FakeMic:
        def __init__(self, loop, device=None) -> None:
            self._q: asyncio.Queue = asyncio.Queue()
            for f in frames:
                self._q.put_nowait(f)

        def start(self) -> None:
            pass

        def stop(self) -> None:
            pass

        async def get(self) -> np.ndarray:
            return await self._q.get()

    return FakeMic


def tone(n: int) -> list[np.ndarray]:
    t = np.arange(FRAME_SAMPLES) / 16000
    f = (0.5 * np.sin(2 * np.pi * 200 * t)).astype(np.float32)
    return [f.copy() for _ in range(n)]


def quiet(n: int) -> list[np.ndarray]:
    return [np.zeros(FRAME_SAMPLES, dtype=np.float32) for _ in range(n)]


def run_handle(monkeypatch, frames: list[np.ndarray]) -> list[dict]:
    monkeypatch.setattr(server, "MicStream", make_fake_mic(frames))
    ws = FakeWs([{"type": "start", "word": "think"}])
    asyncio.run(server.handle(ws, StubVad(), load_config()))
    return ws.sent


def test_real_endpoint_has_no_mock_flag_and_others_stay_mock(monkeypatch):
    sent = run_handle(monkeypatch, quiet(5) + tone(20) + quiet(60))
    by_type = {m["type"]: m for m in sent}
    assert "mock" not in by_type["endpoint"]
    assert by_type["ready"]["mock"] is True
    assert by_type["score"]["mock"] is True
    order = [m["type"] for m in sent]
    assert order.index("endpoint") < order.index("score")


def test_no_speech_sends_real_error_not_endpoint(monkeypatch):
    sent = run_handle(monkeypatch, quiet(400))
    types = [m["type"] for m in sent]
    assert "endpoint" not in types and "score" not in types
    err = next(m for m in sent if m["type"] == "error")
    assert err["detail"] == "timeout: no speech"
    assert "mock" not in err


def test_unknown_word_falls_back_to_default_tier():
    cfg = load_config()
    assert server.tier_for("father", cfg) == cfg.default_tier
    assert server.tier_for("think", cfg) == 1
