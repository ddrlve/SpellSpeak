"""Endpoint state machine. Input is AUDIO FRAMES ONLY.

Hard rule: Jalur A (ASR) text never reaches VAD or endpoint. There is no text
parameter anywhere in this module, and test_endpointer.py asserts that.

Flow: wait for speech -> speech -> silence longer than hesitation_ms -> ENDPOINT.
No speech at all within timeout_s -> TIMEOUT.
"""
from __future__ import annotations

from collections import deque
from enum import Enum
from typing import Callable

import numpy as np

from vad_config import VadParams

SAMPLE_RATE = 16000
FRAME_SAMPLES = 512  # Silero VAD at 16 kHz takes exactly 512 samples per call
FRAME_MS = 1000 * FRAME_SAMPLES / SAMPLE_RATE

SpeechProb = Callable[[np.ndarray], float]  # audio frame in, probability out


class Event(Enum):
    NONE = "none"
    SPEECH_START = "speech_start"
    ENDPOINT = "endpoint"
    TIMEOUT = "timeout"


class Endpointer:
    def __init__(self, params: VadParams, speech_prob: SpeechProb) -> None:
        self._p = params
        self._prob = speech_prob
        self._min_speech = max(1, round(params.min_speech_ms / FRAME_MS))
        self._pre_roll = round(params.pre_roll_ms / FRAME_MS)
        self._timeout_frames = round(params.timeout_s * 1000 / FRAME_MS)
        self._hesitation_frames = max(1, round(params.hesitation_ms / FRAME_MS))
        self._max_frames = round(params.max_utterance_s * 1000 / FRAME_MS)
        self._recent: deque[np.ndarray] = deque(maxlen=self._pre_roll + self._min_speech)
        self._utterance: list[np.ndarray] = []
        self._waited = 0
        self._run = 0       # consecutive speech frames while waiting
        self._silence = 0   # consecutive non-speech frames while speaking
        self._speaking = False
        self._done = False
        self.end_reason = ""  # "silence" | "max_length" after ENDPOINT

    @property
    def utterance_audio(self) -> np.ndarray:
        """float32 mono 16 kHz, from just before speech start up to the endpoint."""
        if not self._utterance:
            return np.zeros(0, dtype=np.float32)
        return np.concatenate(self._utterance)

    def feed(self, frame: np.ndarray) -> Event:
        if self._done:
            raise RuntimeError("endpointer finished; create a new one")
        is_speech = self._prob(frame) >= self._p.speech_threshold
        if self._speaking:
            return self._feed_speaking(frame, is_speech)
        return self._feed_waiting(frame, is_speech)

    def _feed_waiting(self, frame: np.ndarray, is_speech: bool) -> Event:
        self._recent.append(frame)
        self._waited += 1
        self._run = self._run + 1 if is_speech else 0
        if self._run >= self._min_speech:
            self._speaking = True
            self._utterance = list(self._recent)
            return Event.SPEECH_START
        if self._waited >= self._timeout_frames:
            self._done = True
            return Event.TIMEOUT
        return Event.NONE

    def _feed_speaking(self, frame: np.ndarray, is_speech: bool) -> Event:
        self._utterance.append(frame)
        self._silence = 0 if is_speech else self._silence + 1
        if self._silence >= self._hesitation_frames:
            return self._finish("silence")
        if len(self._utterance) >= self._max_frames:
            return self._finish("max_length")
        return Event.NONE

    def _finish(self, reason: str) -> Event:
        self._done = True
        self.end_reason = reason
        return Event.ENDPOINT
