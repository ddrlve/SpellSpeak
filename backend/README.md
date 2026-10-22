# backend

The Python side of SpellSpeak. It captures the microphone, decides when the player has finished speaking, and talks to the Godot game over a local WebSocket at `ws://127.0.0.1:8765`.

## What is real and what is mock

| Part | Status |
| --- | --- |
| Microphone capture (16 kHz, mono, continuous stream) | Real |
| Endpoint detection (Silero VAD, hesitation, timeout) | Real |
| `ready`, `partial` and `score` messages | Mock. Every one carries `"mock": true` and is never a result |
| Jalur A (streaming transcript) | Not built yet |
| Jalur B (phoneme model) | Not built yet. `bench_rtf.py` only measures its speed |

The endpoint only ever sees audio. Text from Jalur A never reaches the VAD or the endpoint decision.

## Files

| File | Purpose |
| --- | --- |
| `server.py` | WebSocket server. The header of this file is the protocol reference |
| `mic_stream.py` | Continuous microphone capture with a `sounddevice` callback |
| `vad_silero.py` | Wrapper around Silero VAD. Takes one audio frame, returns a speech probability |
| `endpointer.py` | State machine: wait for speech, then speech, then silence longer than the hesitation allowance gives an endpoint. No speech before the timeout gives a timeout |
| `vad_config.py` | Reads `vad_config.json` |
| `vad_config.json` | The only place for endpoint parameters, one block per tier. All values are marked `UNCALIBRATED` |
| `per.py` | Phoneme Error Rate with alignment (substitutions, deletions, insertions) |
| `words.json` | Candidate word bank with tier and target sound. Candidates only |
| `record_clips.py` | Records our own dataset clips. It is not part of the app |
| `bench_rtf.py` | Measures the real time factor of the phoneme model on this machine |
| `test_endpointer.py` | Tests for the endpoint logic and for the audio only interface |
| `test_server_flow.py` | Tests for the message flow, using a fake microphone |

## Setup

```powershell
cd backend
pip install -r requirements.txt
```

`espeak-ng` must also be installed on the operating system. The `phonemizer` package needs it to build target phonemes.

The Silero VAD weights ship inside the `silero-vad` pip package. Nothing is downloaded and nothing is committed to git.

## Run

```powershell
python per.py                 # self test, prints "per.py selftest OK"
python server.py              # starts the backend, then open godot/ and press Cast
python -m pytest -q           # logic tests
```

To check the real endpoint: start the server, press Cast in the game, say one word, then stay quiet. When the silence lasts longer than `hesitation_ms`, the server sends `{"type": "endpoint"}` without a `mock` field. If nobody speaks before `timeout_s`, the server sends an `error` message with the detail `timeout: no speech`.

## Endpoint parameters

All parameters live in `vad_config.json`, one block per tier.

| Parameter | Meaning |
| --- | --- |
| `speech_threshold` | Speech probability from the VAD at or above which a frame counts as speech |
| `min_speech_ms` | Speech must last this long before it counts. Shorter sounds such as clicks are ignored |
| `hesitation_ms` | Silence allowed after speech before the endpoint fires |
| `timeout_s` | How long to wait for any speech before giving up |
| `pre_roll_ms` | Audio kept from just before the speech start, so the first sound is not cut |
| `max_utterance_s` | Upper limit on the length of one utterance |

Every value is a placeholder until it is calibrated on our own recordings. The server prints a warning at start while a tier is `UNCALIBRATED`. A word that is not in `words.json` uses `default_tier`, and the server prints a warning once for that word.

## Rules for this folder

1. Everything runs locally. No external speech, ASR or LLM service.
2. Microphone capture stays in Python. Godot only shows the interface.
3. A number is never written down unless a script that can be rerun produced it. Mock output is never a result.
4. When the protocol changes, update the header of `server.py` first, then the Godot client.
