# SpellSpeak Plan

Status date: 2026-10-10. Progress presentation: Wednesday 2026-10-14. Final deadline: [TO FILL].

## Goal
A real-time, 100% local English pronunciation trainer for Indonesian learners, shown as a wizard game.
Two outputs must both work: a correct real-time transcript (Jalur A) and a phoneme-level score (Jalur B).

## What "real-time" means here
- Audio streams from the microphone continuously.
- Jalur A emits partial transcripts while the player speaks. This satisfies the real-time rule.
- Jalur B runs once per utterance, after the VAD endpoint. It is not streaming. Report its latency as "endpoint to score" and defend this split in the report.
- Record-stop-process is forbidden in the app. Recording clips for the dataset (backend/record_clips.py) is allowed because it is not the app.

## Honest constraints
- Dian's laptop has no GPU. Inference must run on CPU. Kaggle T4 helps training only, never inference speed.
- wav2vec2 phoneme model takes the whole utterance in one forward pass (verified on its model card example). Latency grows with clip length. Measure RTF on the weakest laptop before building on it.
- sherpa-onnx streaming zipformer en-2023-06-26 is trained on LibriSpeech only (native audiobook speech, per its docs page). Expect weaker accuracy on Indonesian-accented speech. This is a hypothesis to measure, not a result.
- The EdAcc paper abstract reports lower ASR performance on Indonesian English speakers (for the systems it tested). Same warning.
- No public corpus of Indonesian-accented English with phoneme labels was found. Own recordings are the main evaluation data.

## Phases
| Phase | Deliverable | Gate to pass before next phase |
| --- | --- | --- |
| P0 Setup | Repo runs: `per.py` selftest, mock server, Godot connects | Done in starter kit except Godot run |
| P1 Jalur B gate | `bench_rtf.py` numbers on the weakest laptop, saved to results/ | Decide: keep wav2vec2, quantize it, or choose a smaller model |
| P2 Own data v1 | 5+ speakers, consent, 16 kHz wav, metadata.csv (record_clips.py) | Files load, metadata complete |
| P3 Jalur B real | Real phoneme output into `per.py` inside server.py, separate process | End-to-end on a WAV file |
| P4 Jalur A real | Streaming ASR from WAV and mic, partial messages | WER computed on own data |
| P5 VAD endpoint | Silero VAD + hesitation + timeout | Endpoint never uses ASR text (assert in test) |
| P6 Game loop | Godot flow in docs/GAME_DESIGN.md, real backend | Playable round |
| P7 Experiments | Notebooks NB01 to NB04: PER, WER, latency p50/p95, RTF, noise 20/10/5 dB | JSON results with machine info |
| P8 User testing | 5+ real testers, SUS, interview | Data linked to P7 results |
| P9 Report | Chapters 1 to 8, AI Usage Log | Every number traces to a results file |

## Schedule to Wednesday
- Sat 10 Oct: P0 finish (run Godot), P1 start (collect 10 to 20 clips, run bench_rtf.py), tell lecturer the scratch vs pretrained scope.
- Sun 11 Oct: Kaggle NB02 (scratch KWS). Start P3.
- Mon 12 Oct: NB01 on L2-ARCTIC subset and own clips. Start P4 from WAV files.
- Tue 13 Oct: slides, backup demo video, rehearsal.
- Wed 14 Oct: present. Say clearly what is real, what is mock, what is not built.

## Open decisions (owner: Dian)
- [ ] Lecturer confirms the scratch vs pretrained task (closed-set word classification vs something else).
- [ ] Team size and who records, who labels phonemes.
- [ ] Laptop OS and CPU of the weakest team laptop.
- [ ] Final deadline and demo date.
- [ ] Jalur A engine after benchmark: zipformer vs Vosk small.

## Rules that never change
No invented numbers: every metric comes from a rerunnable script and a results file. Mock output is never a result. Log AI usage in AI_USAGE_LOG.md.
