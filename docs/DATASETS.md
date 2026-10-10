# Datasets

Verified facts come from the pages listed at the end (checked 2026-10-09 and 2026-10-10). Check licenses again before the report.

## Decision
Own recordings are the main data. Public sets only validate the pipeline, supply noise, or give a rough accent signal.

| Dataset | Use | Facts | Limit |
| --- | --- | --- | --- |
| Own recordings (Indonesian speakers, with consent) | Main eval and calibration | Made with `backend/record_clips.py` | Small. Needs manual phoneme labels on a subset |
| EdAcc (Edinburgh International Accents of English Corpus) | Jalur A WER on an Indonesian English subset | About 40 hours of conversational video-call speech, includes Indonesian English speakers, CC-BY-SA, DOI 10.7488/ds/7914 | Conversational, not isolated words. Speaker count per L1 not confirmed. No phoneme labels. Check how to filter Indonesian speakers |
| L2-ARCTIC | Check `per.py` and Jalur B against human phoneme labels | 24 speakers, L1 Hindi, Korean, Mandarin, Spanish, Arabic, Vietnamese. 150 utterances per speaker annotated by hand (substitution, deletion, addition). CC BY-NC 4.0 | No Indonesian speakers |
| speechocean762 | Correlate scores with expert ratings | 5000 sentences, Mandarin L1, sentence/word/phoneme scores by 5 experts, CC BY 4.0 | Not Indonesian |
| Speech Accent Archive | Qualitative accent examples | About 14 Indonesian speakers reading one paragraph, BY-NC-SA | Too small for statistics, no phoneme labels |
| Google Speech Commands v0.02 | Scratch KWS baseline | 105,829 clips, 35 words, train/val/test 84,848 / 9,982 / 4,890 | Native-ish crowd audio. Our spell words are not in it |
| MUSAN | Noise and music for SNR mixing | CC BY 4.0, 11 GB | Take only noise and music subsets |
| DEMAND | Environment noise | CC BY-SA 3.0 | Check recording count after download |
| LibriSpeech | Reference only | Training data of the sherpa zipformer | Native speakers |

Not suitable: Common Voice Indonesian. It is Indonesian-language speech, not English with an Indonesian accent.

## Own recording protocol (v1)
- Speakers: at least 5 Indonesian speakers outside the dev team if possible. User testers may overlap only if consent covers both uses. Never fake or synthesize speakers.
- Consent: written or typed "yes" before recording. Data stays on team devices, used only for this course.
- Words: from `backend/words.json` (candidates, validate with phonemizer first). Each word 3 repetitions, random order.
- Format: 16 kHz, mono, 16-bit WAV. Same laptop microphone for the baseline set. Quiet room.
- Metadata (`metadata.csv`): speaker_id, word, rep, file, device, room, consent, date. No names.
- Phoneme labels: one person with phonetics knowledge labels at least a subset by ear. Record who labeled and how (for the report).
- Splits: split by speaker, never by clip, for any calibration or fine-tuning.

## What each dataset feeds
- NB01 (Jalur B): L2-ARCTIC annotated subset + own clips.
- NB02 (scratch): Speech Commands.
- NB03 (Jalur A): EdAcc Indonesian subset + own clips.
- NB04 (noise): own clips mixed with MUSAN/DEMAND at 20, 10, 5 dB.

## Sources
- L2-ARCTIC: https://psi.engr.tamu.edu/l2-arctic-corpus/
- speechocean762: https://www.openslr.org/101
- EdAcc: https://www.research.ed.ac.uk/en/datasets/the-edinburgh-international-accents-of-english-corpus/
- Speech Accent Archive: https://accent.gmu.edu/language/indonesian/
- Speech Commands card: https://huggingface.co/datasets/google/speech_commands
- MUSAN: https://openslr.org/17/
- DEMAND: https://zenodo.org/records/1227121
