# results

Every number in the report must come from a file in this folder. Each file is written by a script or a Kaggle notebook that can be run again. Never type a result by hand, and never copy a mock value here.

## Files

| File | Written by | Content |
| --- | --- | --- |
| `NB00_setup.json` | `kaggle/NB00_setup.ipynb` | Environment check and data inventory |
| `NB00_words_validation.csv` | `kaggle/NB00_setup.ipynb` | For each word in `backend/words.json`: its IPA, tokens missing from the model vocabulary, and whether the word is usable |
| `NB02_scratch_kws.json` | `kaggle/NB02_scratch_kws.ipynb` | Metrics of the small network trained from scratch. One seed, one run |

More files appear as the other notebooks run. The expected names are listed in `docs/NOTEBOOKS.md`.

## JSON shape

Every notebook writes a JSON file with these keys:

| Key | Meaning |
| --- | --- |
| `notebook` | Notebook name |
| `date` | Date of the run |
| `device` | Machine that ran it |
| `data` | Which data was used |
| `metrics` | The measured values |
| `notes` | Caveats, such as the number of seeds |
| `versions` | Package versions |

## How to add results

1. Run the notebook on Kaggle with Run All.
2. Download `/kaggle/working/results/`.
3. Copy the files into this folder and commit them.
4. Run `kaggle/NB06_results_report.ipynb` to build report tables. It reads these files and computes no new numbers.

## Reading results fairly

A result from the Kaggle CPU is not a laptop result. The claim that the system is real time must come from `backend/bench_rtf.py` on the weakest team laptop, with the machine written next to the numbers.
