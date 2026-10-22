"""Thin Silero VAD wrapper. Takes an audio frame, returns a speech probability.

Weights ship inside the `silero-vad` pip package (silero_vad/data), so nothing is
downloaded and nothing is committed. Named vad_silero.py to avoid shadowing the
`silero_vad` package.
"""
from __future__ import annotations

import numpy as np
import torch

from endpointer import FRAME_SAMPLES, SAMPLE_RATE


class SileroVad:
    def __init__(self) -> None:
        from silero_vad import load_silero_vad

        self._model = load_silero_vad()

    def reset(self) -> None:
        self._model.reset_states()

    def __call__(self, frame: np.ndarray) -> float:
        if frame.shape != (FRAME_SAMPLES,):
            raise ValueError(f"frame must have shape ({FRAME_SAMPLES},), got {frame.shape}")
        with torch.no_grad():
            return float(self._model(torch.from_numpy(frame), SAMPLE_RATE).item())
