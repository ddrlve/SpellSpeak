# kaggle

Experiment notebooks. Training and evaluation run on Kaggle, because the team laptops have no GPU. Each notebook ends by writing a JSON file to `results/`.

## Notebooks

| Notebook | Purpose | Data needed | Accelerator |
| --- | --- | --- | --- |
| `NB00_setup.ipynb` | Check the environment and check that every word in `backend/words.json` can be phonemized | None | None |
| `NB01_pretrained_phoneme_eval.ipynb` | Jalur B without training: phoneme error rate on our recordings, plus speed on GPU and CPU | `spellspeak-own-clips`, optional `l2-arctic` | GPU T4 |
| `NB02_scratch_kws.ipynb` | Small network trained from scratch on Speech Commands. This is the "scratch" side of the scratch versus pretrained comparison | None, Speech Commands downloads itself | GPU T4 |
| `NB03_asr_stream_eval.ipynb` | Jalur A: streaming transcript quality and latency, comparing the sherpa zipformer with Vosk | `spellspeak-own-clips` | None |
| `NB04_noise_conditions.ipynb` | Our clips mixed with noise at 20, 10 and 5 dB, then measured again | `spellspeak-own-clips` and `demand` | GPU T4 |
| `NB06_results_report.ipynb` | Reads `results/*.json` and builds report tables and figures | `spellspeak-results` | None |

NB05 (fine tuning) is a stretch goal and does not exist yet.

`notebook_references/` holds a course notebook about wav2vec2 that we read as background. It is not part of our results.

## How to run a notebook

1. Push the repository to GitHub first. The notebooks clone it.
2. On Kaggle, create a new notebook and import the `.ipynb` file.
3. In Settings, turn Internet on and choose the accelerator named in the table above.
4. Add the datasets the notebook needs.
5. Run All.
6. Download `/kaggle/working/results/` and copy its content into the `results/` folder of the repository.

If a required dataset is missing, the notebook stops with a `FileNotFoundError`. It never invents data.

## Rules

1. A notebook never prints or stores a number it did not compute.
2. Use fixed seeds and state how many runs the numbers come from.
3. Kaggle CPU speed is not laptop speed. Do not use it for the real time claim.

More detail is in `docs/NOTEBOOKS.md` and `docs/RUNNING.md`.
