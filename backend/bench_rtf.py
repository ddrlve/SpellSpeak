"""Gate script: measure Jalur B real-time factor (RTF) on THIS machine.

Usage:
  python bench_rtf.py clip1.wav clip2.wav ...   (16 kHz mono WAV, your own recordings)

RTF = processing time / audio duration. Report the machine (CPU, RAM, OS) next
to the numbers. Run it on the weakest laptop in the team. The first run is a
warm-up and is excluded.
"""
from __future__ import annotations

import statistics
import sys
import time

import soundfile as sf
import torch
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

MODEL = "facebook/wav2vec2-lv-60-espeak-cv-ft"


def main(paths: list[str]) -> None:
    if not paths:
        sys.exit("give at least one 16 kHz mono wav file")
    t0 = time.perf_counter()
    processor = Wav2Vec2Processor.from_pretrained(MODEL)
    model = Wav2Vec2ForCTC.from_pretrained(MODEL).eval()
    print(f"model load: {time.perf_counter() - t0:.2f} s")

    def run(path: str) -> tuple[float, float, str]:
        audio, sr = sf.read(path, dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if sr != 16000:
            sys.exit(f"{path}: need 16000 Hz, got {sr}")
        inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
        t = time.perf_counter()
        with torch.inference_mode():
            logits = model(inputs.input_values).logits
        elapsed = time.perf_counter() - t
        phones = processor.batch_decode(torch.argmax(logits, dim=-1))[0]
        return elapsed, len(audio) / sr, phones

    run(paths[0])  # warm-up, excluded
    rtfs = []
    for p in paths:
        elapsed, dur, phones = run(p)
        rtfs.append(elapsed / dur)
        print(f"{p}: audio {dur:.2f} s, infer {elapsed:.3f} s, RTF {elapsed / dur:.3f}, phones: {phones}")
    print(f"n={len(rtfs)} median RTF {statistics.median(rtfs):.3f}, max {max(rtfs):.3f}")
    print("threads:", torch.get_num_threads(), "| cuda:", torch.cuda.is_available())


if __name__ == "__main__":
    main(sys.argv[1:])
