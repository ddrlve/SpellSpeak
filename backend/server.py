"""SpellSpeak local backend (PARTIAL MOCK MODE).

Real:  mic capture (sounddevice) + Silero VAD endpoint. Parameters per tier live
       in vad_config.json and are UNCALIBRATED placeholders until we calibrate.
Mock:  ready, partial and score. Every mock message carries "mock": true and is
       never a measurement. Do not copy values from it into the report.

Protocol (JSON text frames over ws://127.0.0.1:8765)
  client -> server  {"type": "start", "word": "think"}
  server -> client  {"type": "ready", "word": ..., "target_ipa": [...], "mock": true}
  server -> client  {"type": "partial", "text": "...", "mock": true}      (repeated, MOCK)
  server -> client  {"type": "endpoint"}                    (REAL: no "mock" field)
  server -> client  {"type": "score", "per": f, "S": n, "D": n, "I": n, "N": n,
                     "target_ipa": [...], "heard_ipa": [...], "errors": [...], "mock": true}
  server -> client  {"type": "error", "detail": "..."}      (no "mock" field when real,
                     e.g. "timeout: no speech", "mic: ...")

Endpoint rule: audio only. Silero VAD sees mic frames, nothing else. Jalur A text
never reaches VAD or endpoint. The endpoint ends when speech was detected and
silence then lasts longer than hesitation_ms. No speech for timeout_s sends an
"error" with detail "timeout: no speech" instead of an endpoint.
The utterance audio (float32, 16 kHz) is kept in memory in Session.utterance for
Jalur B (next session, not processed yet).

Still to replace with the real pipeline:
  Jalur A  -> partial messages (display only, never triggers endpoint)
  Jalur B  -> heard_ipa, then per.per(target_ipa, heard_ipa)
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import websockets

import per as per_mod
from endpointer import Endpointer, Event
from mic_stream import MicStream
from vad_config import VadConfig, load_config
from vad_silero import SileroVad

HOST, PORT = "127.0.0.1", 8765
WORDS_PATH = Path(__file__).with_name("words.json")

# Hand-written fixture so the mock runs without espeak-ng.
# Real build: phonemizer + espeak-ng (same alphabet as the wav2vec2 model).
FIXTURE_IPA = {
    "think": ["θ", "ɪ", "ŋ", "k"],
    "very": ["v", "ɛ", "ɹ", "i"],
    "three": ["θ", "ɹ", "i"],
    "this": ["ð", "ɪ", "s"],
}


def target_ipa(word: str) -> list[str]:
    try:  # real path, used when phonemizer and espeak-ng are installed
        from phonemizer import phonemize
        from phonemizer.separator import Separator

        out = phonemize(word, language="en-us", backend="espeak",
                        separator=Separator(phone=" ", word="", syllable=""), strip=True)
        return out.split()
    except Exception:
        return FIXTURE_IPA.get(word.lower(), [])


def mock_heard(ref: list[str]) -> list[str]:
    """MOCK: pretend the learner replaced /θ/ and /ð/ with /t/ and /d/."""
    swap = {"θ": "t", "ð": "d", "v": "f"}
    return [swap.get(p, p) for p in ref]


async def send(ws, **msg) -> None:
    """MOCK sender: stamps "mock": true. Use only for values that are still mock."""
    msg["mock"] = True
    await ws.send(json.dumps(msg, ensure_ascii=False))


async def send_real(ws, **msg) -> None:
    """Real sender: no "mock" field. Only for output produced by the real pipeline."""
    await ws.send(json.dumps(msg, ensure_ascii=False))


@dataclass
class Session:
    """Per-connection state. utterance is the Jalur B input (next session)."""
    utterance: np.ndarray | None = None


def load_word_tiers() -> dict[str, int]:
    words = json.loads(WORDS_PATH.read_text(encoding="utf-8"))["words"]
    return {w["word"]: int(w["tier"]) for w in words}


WORD_TIERS = load_word_tiers()
_warned_words: set[str] = set()


def tier_for(word: str, cfg: VadConfig) -> int:
    if word in WORD_TIERS:
        return WORD_TIERS[word]
    if word not in _warned_words:
        _warned_words.add(word)
        print(f"[tier] '{word}' not in words.json, using default tier {cfg.default_tier}",
              file=sys.stderr, flush=True)
    return cfg.default_tier


async def mock_partials(ws, word: str) -> None:
    """MOCK partials. Independent of the mic, VAD and endpoint."""
    try:
        for text in ("", word[: max(1, len(word) // 2)], word):
            await asyncio.sleep(0.25)
            await send(ws, type="partial", text=text)
    except websockets.ConnectionClosed:
        pass


async def listen(ws, vad: SileroVad, cfg: VadConfig, tier: int) -> np.ndarray | None:
    """REAL: stream mic frames into the endpointer. Returns utterance audio on
    endpoint, or None after sending an error (mic failure or no-speech timeout)."""
    vad.reset()
    ep = Endpointer(cfg.params_for(tier), vad)
    mic = MicStream(asyncio.get_running_loop(), cfg.input_device)
    try:
        mic.start()
    except Exception as e:  # sounddevice raises PortAudioError for bad devices
        await send_real(ws, type="error", detail=f"mic: {e}")
        return None
    try:
        while True:
            try:
                frame = await asyncio.wait_for(mic.get(), timeout=2.0)
            except asyncio.TimeoutError:
                await send_real(ws, type="error", detail="mic: no audio frames")
                return None
            ev = ep.feed(frame)
            if ev is Event.ENDPOINT:
                await send_real(ws, type="endpoint")
                return ep.utterance_audio
            if ev is Event.TIMEOUT:
                await send_real(ws, type="error", detail="timeout: no speech")
                return None
    finally:
        mic.stop()


async def handle(ws, vad: SileroVad, cfg: VadConfig) -> None:
    session = Session()
    async for raw in ws:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            await send(ws, type="error", detail="invalid json")
            continue
        if msg.get("type") != "start":
            await send(ws, type="error", detail="unknown type")
            continue
        word = str(msg.get("word", "")).strip().lower()
        ref = target_ipa(word)
        if not ref:
            await send(ws, type="error", detail=f"no phonemes for '{word}'")
            continue
        await send(ws, type="ready", word=word, target_ipa=ref)
        partials = asyncio.create_task(mock_partials(ws, word))  # MOCK
        try:
            session.utterance = await listen(ws, vad, cfg, tier_for(word, cfg))
        finally:
            partials.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await partials
        if session.utterance is None:
            continue
        heard = mock_heard(ref)  # MOCK: replace with Jalur B output (uses session.utterance)
        result = per_mod.per(ref, heard)
        await send(ws, type="score", target_ipa=ref, heard_ipa=heard, **result)


async def main() -> None:
    cfg = load_config()
    vad = SileroVad()  # load once

    async def handler(ws) -> None:
        await handle(ws, vad, cfg)

    async with websockets.serve(handler, HOST, PORT):
        print(f"SpellSpeak backend (real mic + VAD endpoint, mock partial/score) "
              f"on ws://{HOST}:{PORT}", flush=True)
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
