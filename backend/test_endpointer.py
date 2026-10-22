"""Logic tests for the endpointer. Synthetic audio proves LOGIC only, never accuracy.

The speech probability here is a test stub driven by amplitude, not Silero.
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path

import numpy as np
import pytest

import endpointer
import vad_silero
from endpointer import FRAME_MS, FRAME_SAMPLES, Endpointer, Event
from vad_config import VadParams, load_config

BACKEND = Path(__file__).parent


def params(**kw) -> VadParams:
    base = dict(tier=1, status="TEST", speech_threshold=0.5, min_speech_ms=96,
                hesitation_ms=320, timeout_s=1.0, pre_roll_ms=64, max_utterance_s=2.0)
    base.update(kw)
    return VadParams(**base)


def stub_prob(frame: np.ndarray) -> float:
    return 1.0 if float(np.abs(frame).max()) > 0.1 else 0.0


def silence(n: int) -> list[np.ndarray]:
    return [np.zeros(FRAME_SAMPLES, dtype=np.float32) for _ in range(n)]


def speech(n: int) -> list[np.ndarray]:
    t = np.arange(FRAME_SAMPLES) / 16000
    tone = (0.5 * np.sin(2 * np.pi * 200 * t)).astype(np.float32)
    return [tone.copy() for _ in range(n)]


def run(ep: Endpointer, frames: list[np.ndarray]) -> list[Event]:
    out = []
    for f in frames:
        ev = ep.feed(f)
        out.append(ev)
        if ev in (Event.ENDPOINT, Event.TIMEOUT):
            break
    return out


def frames_for(ms: float) -> int:
    return int(np.ceil(ms / FRAME_MS))


# --- audio-only interface ---------------------------------------------------

def test_feed_signature_is_audio_only():
    sig = inspect.signature(Endpointer.feed)
    assert list(sig.parameters) == ["self", "frame"]
    assert sig.parameters["frame"].annotation in (np.ndarray, "np.ndarray")


def test_silero_wrapper_signature_is_audio_only():
    sig = inspect.signature(vad_silero.SileroVad.__call__)
    assert list(sig.parameters) == ["self", "frame"]
    assert sig.parameters["frame"].annotation in (np.ndarray, "np.ndarray")


def test_endpointer_constructor_has_no_text_input():
    sig = inspect.signature(Endpointer.__init__)
    assert list(sig.parameters) == ["self", "params", "speech_prob"]


@pytest.mark.parametrize("module", ["endpointer.py", "vad_silero.py", "mic_stream.py"])
def test_vad_modules_do_not_import_asr_or_partial_code(module):
    tree = ast.parse((BACKEND / module).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & {"server", "sherpa_onnx", "vosk", "asr"}


def test_text_cannot_be_fed():
    ep = Endpointer(params(), stub_prob)
    with pytest.raises(Exception):
        ep.feed("think")  # type: ignore[arg-type]


# --- endpoint logic ---------------------------------------------------------

def test_silence_only_times_out():
    ep = Endpointer(params(timeout_s=1.0), stub_prob)
    events = run(ep, silence(100))
    assert events[-1] is Event.TIMEOUT
    assert Event.SPEECH_START not in events


def test_speech_then_long_silence_gives_endpoint():
    ep = Endpointer(params(hesitation_ms=320), stub_prob)
    events = run(ep, silence(5) + speech(20) + silence(30))
    assert Event.SPEECH_START in events
    assert events[-1] is Event.ENDPOINT
    assert ep.end_reason == "silence"
    audio = ep.utterance_audio
    assert audio.dtype == np.float32
    assert float(np.abs(audio).max()) > 0.1  # speech frames are in the buffer


def test_utterance_buffer_covers_speech_and_hesitation_tail():
    p = params(hesitation_ms=320, pre_roll_ms=64)
    ep = Endpointer(p, stub_prob)
    run(ep, silence(10) + speech(20) + silence(30))
    n_hes = frames_for(p.hesitation_ms)
    n_pre = round(p.pre_roll_ms / FRAME_MS)
    assert len(ep.utterance_audio) == (n_pre + 20 + n_hes) * FRAME_SAMPLES


def test_short_pause_inside_word_does_not_endpoint():
    ep = Endpointer(params(hesitation_ms=320), stub_prob)
    pause = frames_for(320) - 2  # shorter than hesitation_ms
    events = run(ep, speech(10) + silence(pause) + speech(10))
    assert Event.ENDPOINT not in events
    assert Event.SPEECH_START in events


def test_pause_resets_after_speech_resumes():
    ep = Endpointer(params(hesitation_ms=320), stub_prob)
    pause = frames_for(320) - 2
    events = run(ep, speech(10) + silence(pause) + speech(5) + silence(pause) + speech(5))
    assert Event.ENDPOINT not in events


def test_click_shorter_than_min_speech_is_ignored():
    ep = Endpointer(params(min_speech_ms=96), stub_prob)
    events = run(ep, silence(3) + speech(1) + silence(3) + speech(1) + silence(60))
    assert Event.SPEECH_START not in events
    assert events[-1] is Event.TIMEOUT


def test_max_utterance_caps_length():
    ep = Endpointer(params(max_utterance_s=1.0), stub_prob)
    events = run(ep, speech(200))
    assert events[-1] is Event.ENDPOINT
    assert ep.end_reason == "max_length"


def test_feed_after_done_raises():
    ep = Endpointer(params(timeout_s=0.1), stub_prob)
    run(ep, silence(20))
    with pytest.raises(RuntimeError):
        ep.feed(silence(1)[0])


# --- config -----------------------------------------------------------------

def test_config_loads_and_marks_uncalibrated():
    cfg = load_config()
    assert set(cfg.tiers) == {1, 2, 3}
    assert all(p.status == "UNCALIBRATED" for p in cfg.tiers.values())
    assert cfg.params_for(99).tier == cfg.default_tier  # unknown tier falls back


# --- Silero smoke (loads + returns float in [0,1]; says nothing about accuracy)

def test_silero_loads_and_returns_probability():
    pytest.importorskip("silero_vad")
    vad = vad_silero.SileroVad()
    vad.reset()
    p = vad(silence(1)[0])
    assert isinstance(p, float) and 0.0 <= p <= 1.0
    with pytest.raises(ValueError):
        vad(np.zeros(400, dtype=np.float32))
