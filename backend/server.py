"""SpellSpeak local backend (MOCK MODE).

Purpose today: let the Godot UI and the game flow be built and demoed before
Jalur A (streaming ASR) and Jalur B (wav2vec2 phoneme CTC) exist.

EVERY message sent in mock mode carries "mock": true. Nothing printed by this
mode is a measurement. Do not copy values from it into the report.

Protocol (JSON text frames over ws://127.0.0.1:8765)
  client -> server  {"type": "start", "word": "think"}
  server -> client  {"type": "ready", "word": ..., "target_ipa": [...], "mock": true}
  server -> client  {"type": "partial", "text": "...", "mock": true}      (repeated)
  server -> client  {"type": "endpoint", "mock": true}
  server -> client  {"type": "score", "per": f, "S": n, "D": n, "I": n, "N": n,
                     "target_ipa": [...], "heard_ipa": [...], "errors": [...], "mock": true}

Replace the MOCK blocks with the real pipeline:
  Jalur A  -> partial messages (display only, never triggers endpoint)
  VAD      -> endpoint message (Silero VAD + hesitation + timeout)
  Jalur B  -> heard_ipa, then per.per(target_ipa, heard_ipa)
"""
from __future__ import annotations

import asyncio
import json
import sys

import websockets

import per as per_mod

HOST, PORT = "127.0.0.1", 8765

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
    msg["mock"] = True
    await ws.send(json.dumps(msg, ensure_ascii=False))


async def handle(ws) -> None:
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
        for text in ("", word[: max(1, len(word) // 2)], word):  # MOCK partials
            await asyncio.sleep(0.25)
            await send(ws, type="partial", text=text)
        await asyncio.sleep(0.3)
        await send(ws, type="endpoint")
        heard = mock_heard(ref)  # MOCK: replace with Jalur B output
        result = per_mod.per(ref, heard)
        await send(ws, type="score", target_ipa=ref, heard_ipa=heard, **result)


async def main() -> None:
    async with websockets.serve(handle, HOST, PORT):
        print(f"SpellSpeak MOCK backend on ws://{HOST}:{PORT}", flush=True)
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
