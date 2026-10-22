"""Continuous mic capture (sounddevice callback), 16 kHz mono float32.

Not record-stop-process: the PortAudio callback pushes fixed-size frames into an
asyncio queue while the stream is open. The consumer reads frames one by one.
"""
from __future__ import annotations

import asyncio
import sys

import numpy as np
import sounddevice as sd

from endpointer import FRAME_SAMPLES, SAMPLE_RATE


class MicStream:
    def __init__(self, loop: asyncio.AbstractEventLoop, device: int | str | None = None) -> None:
        self._loop = loop
        self._device = device
        self._queue: asyncio.Queue[np.ndarray] = asyncio.Queue()
        self._pending = np.zeros(0, dtype=np.float32)
        self._stream: sd.InputStream | None = None

    def _callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        if status:
            print(f"[mic] {status}", file=sys.stderr, flush=True)
        self._pending = np.concatenate([self._pending, indata[:, 0]])
        while len(self._pending) >= FRAME_SAMPLES:
            frame = self._pending[:FRAME_SAMPLES].copy()
            self._pending = self._pending[FRAME_SAMPLES:]
            self._loop.call_soon_threadsafe(self._queue.put_nowait, frame)

    def start(self) -> None:
        self._stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                                      blocksize=FRAME_SAMPLES, device=self._device,
                                      callback=self._callback)
        self._stream.start()

    def stop(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    async def get(self) -> np.ndarray:
        return await self._queue.get()
