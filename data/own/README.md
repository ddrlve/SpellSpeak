# data/own

Our own recordings. These are the main data for evaluation and calibration, because no public set has Indonesian accented English with phoneme labels.

This is the only folder under `data/` that git tracks. Every other dataset stays out of the repository.

## Rules

1. Every clip comes from a real person who agreed to be recorded. Never generate, synthesize or fake a clip.
2. Speaker ids are anonymous, for example `S01`. Never put a real name in an id, a file name or the metadata.
3. Consent is asked once per recording session. The data stays on team devices and is used only for this course project.
4. Split by speaker, never by clip, for any calibration or fine tuning.

## Layout

| Path | Content |
| --- | --- |
| `metadata.csv` | One row per clip |
| `wav/` | 16 kHz, mono, 16 bit WAV files named `<speaker>_<word>_<rep>.wav` |

## metadata.csv columns

| Column | Meaning |
| --- | --- |
| `speaker_id` | Anonymous speaker id |
| `word` | The word that was asked for, from `backend/words.json` |
| `rep` | Repetition number of that word for that speaker |
| `file` | Path of the WAV file relative to this folder |
| `device` | Microphone used |
| `room` | Recording room, for example `quiet room` |
| `consent` | `yes` when the speaker agreed |
| `date` | Recording date |

## Add a new speaker

```powershell
python backend/record_clips.py --speaker S02 --room "quiet room" --device "built-in mic"
```

The script asks for consent, then shows each word in random order and records one clip after each Enter. It appends to `metadata.csv`. Run `python backend/record_clips.py --help` to see all options.

## Where the data is used

The Kaggle notebooks NB01, NB03 and NB04 read this folder. Upload its content as a private Kaggle Dataset named `spellspeak-own-clips`. See `docs/RUNNING.md`.
