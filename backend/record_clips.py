"""Record own dataset clips (NOT the app; fixed-length recording is fine here).

Usage:
  python record_clips.py --speaker S01 [--reps 3] [--seconds 2.5] [--out ../data/own]

Writes 16 kHz mono 16-bit WAV files and appends to metadata.csv.
Consent is required once per run. Do not put real names in speaker ids.
Every clip must come from a real person who agreed. Never generate or fake clips.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from datetime import date
from pathlib import Path

import sounddevice as sd
import soundfile as sf

SR = 16000
FIELDS = ["speaker_id", "word", "rep", "file", "device", "room", "consent", "date"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--speaker", required=True, help="anonymous id, e.g. S01")
    ap.add_argument("--words", default=str(Path(__file__).with_name("words.json")))
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--seconds", type=float, default=2.5)
    ap.add_argument("--out", default="../data/own")
    ap.add_argument("--room", default="quiet room")
    ap.add_argument("--device", default="built-in mic")
    a = ap.parse_args()

    print("Consent: recordings stay on team devices and are used only for this course project.")
    if input("Does the speaker agree? type yes: ").strip().lower() != "yes":
        sys.exit("No consent, nothing recorded.")

    words = [w["word"] for w in json.load(open(a.words))["words"]]
    jobs = [(w, r) for w in words for r in range(1, a.reps + 1)]
    random.shuffle(jobs)

    out = Path(a.out)
    (out / "wav").mkdir(parents=True, exist_ok=True)
    meta = out / "metadata.csv"
    new = not meta.exists()
    with open(meta, "a", newline="") as f:
        wr = csv.DictWriter(f, FIELDS)
        if new:
            wr.writeheader()
        for i, (word, rep) in enumerate(jobs, 1):
            input(f"[{i}/{len(jobs)}] say '{word}' after pressing Enter... ")
            audio = sd.rec(int(a.seconds * SR), samplerate=SR, channels=1, dtype="int16")
            sd.wait()
            name = f"{a.speaker}_{word}_{rep}.wav"
            sf.write(out / "wav" / name, audio, SR, subtype="PCM_16")
            wr.writerow({"speaker_id": a.speaker, "word": word, "rep": rep, "file": f"wav/{name}",
                         "device": a.device, "room": a.room, "consent": "yes",
                         "date": date.today().isoformat()})
            f.flush()
    print(f"done: {len(jobs)} clips in {out}")


if __name__ == "__main__":
    main()
