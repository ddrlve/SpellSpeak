# Kaggle notebooks

Rule for every notebook: it ends by writing `results/<notebook>.json` with this shape. It never prints or hardcodes numbers it did not compute.

```json
{
  "notebook": "NB01_pretrained_phoneme_eval",
  "date": "<ISO date>",
  "device": {"name": "<gpu or cpu model>", "threads": 0, "platform": "<string>"},
  "data": {"source": "<dataset>", "n_utterances": 0, "speakers": 0},
  "metrics": {},
  "notes": "<what was run, versions, seeds>",
  "versions": {"torch": "<x.y.z>"}
}
```

## Files and how to run
All notebooks live in `kaggle/` as `.ipynb`. On Kaggle: New Notebook, File, Import Notebook, pick the file, set Accelerator and Internet as written in its first cell, Run All.
Then download `/kaggle/working/results/` and copy the files into the repo `results/` (JSON and per-clip CSV are tracked in git).

Every notebook gets the repo code (`per.py`, `words.json`) in its first code cell:
- public repo: `git clone` (Internet ON), or
- private repo: upload the repo as a private Kaggle Dataset `spellspeak-code`.

Kaggle Dataset names the notebooks expect (all private):
| Dataset | Content | Used by |
| --- | --- | --- |
| `spellspeak-own-clips` | `data/own` from `record_clips.py`: `metadata.csv` + `wav/` | NB00, NB01, NB03, NB04 |
| `l2-arctic` | L2-ARCTIC speaker folders (`<spk>/wav`, `<spk>/annotation`) | NB01 (optional) |
| `demand` | any folder of noise `.wav` (DEMAND or MUSAN noise) | NB04 |
| `spellspeak-results` | the repo `results/` folder | NB06 |

Not a notebook on purpose: `backend/bench_rtf.py` (must run on the weakest laptop CPU) and `backend/record_clips.py` (needs the laptop mic).

## Kaggle facts
- Session: GPU notebooks give T4 x2 or P100. Quota and session length changed over time. From general knowledge, about 30 GPU hours per week and about 9 hours per session. Read the numbers in the notebook settings panel before planning. [Likely, not verified on the live page]
- Turn on Internet in notebook settings to download models and datasets, then save outputs. Add own recordings as a private Kaggle Dataset (consent applies).
- Save results/ and model files under /kaggle/working so they survive. Download the JSON files into the repo.
- Pin versions in the first cell (`pip freeze | grep -E "torch|transformers|torchaudio"`) and write them in the JSON.

## Notebook list (7)
| # | Name | GPU | Priority | Purpose |
| --- | --- | --- | --- | --- |
| 00 | NB00_setup | no | must | Check GPU, versions, download datasets, unpack own clips, write data inventory |
| 01 | NB01_pretrained_phoneme_eval | yes (and CPU run) | must | Jalur B zero-shot: PER on L2-ARCTIC annotated subset and own clips, RTF on T4 and CPU, dynamic int8 quantization effect on PER and RTF |
| 02 | NB02_scratch_kws | yes | must | Scratch arm: small CNN on Speech Commands, trained in the notebook, writes JSON |
| 03 | NB03_asr_stream_eval | no (CPU) | must | Jalur A: sherpa-onnx zipformer vs Vosk small. WER on own clips and EdAcc Indonesian subset, with and without biasing. Partial first-token latency, stable-partial latency, RTF |
| 04 | NB04_noise_conditions | no | should | Mix MUSAN/DEMAND at SNR 20/10/5 dB with fixed seed, rerun NB01 and NB03 metrics per condition |
| 05 | NB05_finetune_phoneme (not created yet) | yes | stretch | Fine-tune wav2vec2 phoneme CTC on L2-ARCTIC plus own train speakers. Adopt only if PER on held-out own speakers beats zero-shot |
| 06 | NB06_results_report | no | must | Read all results/*.json, build tables and figures for the report. No new numbers |

## Details

### NB01 steps
1. Load `facebook/wav2vec2-lv-60-espeak-cv-ft` with `Wav2Vec2ForCTC` and `Wav2Vec2Processor`. Input 16 kHz mono.
2. Reference phonemes: L2-ARCTIC human labels (map ARPAbet to the model alphabet, document the mapping) and phonemizer + espeak-ng for own clips. Keep both PER variants separate.
3. Compute PER with `backend/per.py`. Report S, D, I, N too.
4. Time inference per clip: warm-up excluded, `torch.inference_mode`, report median and p95, RTF = infer time / audio time. Run on T4 and on CPU (`CUDA_VISIBLE_DEVICES=""`).
5. Quantize with `torch.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)`. Compare PER and RTF against fp32. Accept only if PER stays within a margin you decide before looking.
6. Save per-clip rows to CSV and aggregates to JSON.

### NB03 steps
1. Install `sherpa-onnx`. Download `sherpa-onnx-streaming-zipformer-en-2023-06-26` (docs list int8 encoder 68 MB). Also Vosk `vosk-model-small-en-us-0.15`.
2. Stream each WAV in 100 ms chunks at real-time pace. Log wall-clock time of every partial.
3. WER with `jiwer` against reference text. Normalize text the same way for all engines (lowercase, strip punctuation).
4. Contextual biasing only as a second configuration. Report WER with and without.
5. Report first-partial latency, stable-partial latency, RTF on a CPU run that matches the laptop as closely as possible.

### Training time
Do not guess. Run 1 epoch (or 100 steps) with timing on, extrapolate, write the extrapolation as an estimate. Rough expectation, unmeasured: the scratch CNN is small and should be minutes per epoch; wav2vec2-large fine-tuning is the expensive one. [Guessing]

## Success criteria
There is no "good enough" number set in advance by me. Set them with the lecturer. Method: baseline first (zero-shot, pretrained), then every change must beat it on held-out speakers.
