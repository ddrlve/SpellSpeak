# AI Usage Log

Fill the last column yourself after you actually checked. Do not leave it as a claim.

| No | Date | Tool | Purpose | Output used | Student verification |
| --- | --- | --- | --- | --- | --- |
| 1 | 2026-10-09 | Claude (Anthropic) | Review draft report, find datasets and models, write PRD | PRD structure, dataset and model shortlist | [TO FILL: licenses and sizes checked on official pages; models benchmarked ourselves] |
| 2 | 2026-10-10 | Claude (Anthropic) | Starter kit: mock backend, per.py, Godot basic UI, Kaggle scratch script, bench_rtf.py | Code in this repo | [TO FILL: per.py selftest run; server.py run with a real client; Godot opened and run; train_kws_scratch.py run on Kaggle; bench_rtf.py run on weakest laptop] |
| 3 | 2026-10-10 | Claude Code | Repo review; convert Kaggle work to notebooks NB00-NB04, NB06 (scratch script moved into NB02, file-list bug fixed); rewrite .gitignore; update docs | kaggle/*.ipynb, .gitignore, results/.gitkeep, CLAUDE.md, README.md, docs/NOTEBOOKS.md, docs/PLAN.md; removed kaggle/train_kws_scratch.py. Verified only statically (schema, compile, unit checks of mix_snr, TextGrid parser, partial latency); not run on Kaggle | [TO FILL by Dian] |
| 4 | 2026-10-10 | Claude Code | Exclude AI agent files from git (CLAUDE.md, .claude/, .remember/, prompt doc); drop their references from README and PLAN | .gitignore, README.md, docs/PLAN.md. Verified with `git add -A --dry-run` (no agent files listed) | [TO FILL by Dian] |
| 5 | 2026-10-10 | Claude Code | Write run guide (local, Kaggle, datasets per notebook, notebook purposes) | docs/RUNNING.md, README.md link | [TO FILL by Dian] |
| 6 | 2026-10-10 | Claude Code | Rewrite README (what SpellSpeak is, round flow, architecture diagram) and draw banner illustration | README.md, docs/assets/spellspeak-hero.svg. Banner checked by rendering with headless Edge | [TO FILL by Dian] |
| 7 | 2026-10-10 | Claude Code | Banner text to English; rewrite README "How it works" for first-time readers (plain-words section, simpler diagram, Jalur explained) | README.md, docs/assets/spellspeak-hero.svg | [TO FILL by Dian] |
| 8 | 2026-10-10 | Claude Code | Add "Technical view" to README: sequence diagram, process model, per-component notes, protocol table, evidence rules | README.md. Facts checked against backend/server.py header and per.py; marked as target design where not built | [TO FILL by Dian] |
| 9 | 2026-10-10 | Claude Code | Simplify both README diagrams (4-step flowchart, 3-participant sequence diagram) | README.md | [TO FILL by Dian] |
| 10 | 2026-10-10 | Claude Code | Restore original README data-flow diagram (user preferred it); add box-by-box table with the "tink" example | README.md | [TO FILL by Dian] |
| 11 | 2026-10-11 | Claude Code | Add missing `sounddevice` to backend/requirements.txt (record_clips.py failed with ModuleNotFoundError) | backend/requirements.txt | [TO FILL by Dian] |
| 12 | 2026-10-12 | Claude Code | Build progress-update slide deck (24 slides, speaker notes) following the team moodboard; draw original vector characters and backgrounds (no moodboard images reused) | docs/presentation/SpellSpeak_Progress.pptx. Content taken from docs/PLAN.md, DATASETS.md, NOTEBOOKS.md, GAME_DESIGN.md, server.py header; no result numbers (results/ is empty), PER 0.25 shown only as a labeled formula example. Verified: pptx validator passed, every slide rendered with PowerPoint and checked by eye | [TO FILL by Dian] |
| 13 | 2026-10-13 | Claude Code | NB02 training cell: precompute log-mel once and train from tensors (epoch took 201 s, bottleneck was per-sample wav read + mel in DataLoader) | kaggle/NB02_scratch_kws.ipynb. Cell compiles; not run on Kaggle yet | [TO FILL by Dian] |
| 14 | 2026-10-13 | Claude Code | Update docs/PLAN.md: status date and notebook status checklist (NB00, NB02 done, no numbers copied) | docs/PLAN.md | [TO FILL by Dian] |
