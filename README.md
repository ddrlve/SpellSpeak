# SpellSpeak

Gamified real-time English pronunciation trainer for Indonesian learners. Cast "spells" by speaking: dual-track local ASR (streaming transcript + wav2vec2 phoneme scoring), 100% offline. Python backend, Godot frontend. Final Project COMP6822001 Speech Recognitio

SpellSpeak/
├── backend/
│   ├── audio/          # capture, VAD
│   ├── asr_stream/     # Jalur A
│   ├── scoring/        # Jalur B (phoneme_scorer.py)
│   ├── server/         # WebSocket
│   └── eval/           # WER, PER, latency logger
├── game/               # project Godot
├── data/               # spell list JSON (tidak commit dataset besar)
├── experiments/        # CSV hasil, notebook analisis
├── docs/               # arsitektur, AI usage log
└── README.md
