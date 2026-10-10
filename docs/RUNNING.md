# Cara Run SpellSpeak

Panduan singkat untuk dibaca ulang. Detail eksperimen ada di `docs/NOTEBOOKS.md`.

## 1. Lokal (laptop, CPU)

```powershell
cd backend
python per.py                      # selftest PER, harus print "per.py selftest OK"
pip install -r requirements.txt
python server.py                   # mock backend di ws://127.0.0.1:8765
```

Lalu buka folder `godot/` di Godot 4.x, tekan Run, tekan Cast.
Semua angka dari mock server membawa `"mock": true` dan bukan hasil.

Script yang memang harus jalan di laptop (bukan Kaggle):

```powershell
python backend/record_clips.py --speaker S01     # rekam clip sendiri, butuh consent, hasil ke data/own
python backend/bench_rtf.py clip1.wav clip2.wav  # gate RTF Jalur B di CPU laptop terlemah
```

`espeak-ng` harus terinstall di OS supaya phonemizer jalan.

## 2. Kaggle

Penting: notebook melakukan `git clone` dari GitHub. Push dulu sebelum run.
Kalau repo private, upload folder repo sebagai private Kaggle Dataset `spellspeak-code`.

Langkah per notebook:
1. Kaggle: New Notebook, File, Import Notebook, pilih `kaggle/NBxx.ipynb`.
2. Settings: Internet ON. Accelerator sesuai cell pertama notebook (GPU T4 atau none).
3. Add Input: pasang dataset yang dibutuhkan (tabel di bawah).
4. Run All.
5. Download `/kaggle/working/results/`, copy isinya ke `results/` di repo, commit.

## 3. Dataset yang dibutuhkan

Semua dataset di bawah dibuat sendiri sebagai private Kaggle Dataset.

| Notebook | Dataset wajib | Accelerator | Bisa run sebelum rekam? |
| --- | --- | --- | --- |
| NB00_setup | tidak ada | none | ya |
| NB02_scratch_kws | tidak ada (Speech Commands didownload otomatis, sekitar 2.3 GB) | GPU T4 | ya |
| NB01_pretrained_phoneme_eval | `spellspeak-own-clips` (opsional `l2-arctic`) | GPU T4 | tidak |
| NB03_asr_stream_eval | `spellspeak-own-clips` | none | tidak |
| NB04_noise_conditions | `spellspeak-own-clips` + `demand` (folder noise .wav) | GPU T4 | tidak |
| NB06_results_report | `spellspeak-results` (folder `results/` repo) | none | setelah ada JSON |

Isi dataset:
- `spellspeak-own-clips`: isi folder `data/own` dari `record_clips.py`, yaitu `metadata.csv` dan `wav/`. Hanya speaker asli dengan consent.
- `l2-arctic`: folder speaker L2-ARCTIC (`<spk>/wav`, `<spk>/annotation`). Lisensi CC BY-NC 4.0.
- `demand`: file noise `.wav` dari DEMAND atau subset noise MUSAN.
- `spellspeak-results`: folder `results/` dari repo.

Kalau dataset wajib belum dipasang, notebook berhenti dengan `FileNotFoundError`. Notebook tidak pernah memalsukan data.

## 4. Fungsi tiap notebook

| Notebook | Fungsi | Output |
| --- | --- | --- |
| NB00_setup | Cek GPU dan versi, install espeak-ng, cek kata di `words.json` bisa di-phonemize dan tokennya ada di vocab wav2vec2, inventaris data | `NB00_setup.json`, `NB00_words_validation.csv` |
| NB01_pretrained_phoneme_eval | Jalur B zero-shot: PER (S/D/I/N) di rekaman sendiri, RTF di T4, CPU fp32, CPU int8. Opsional PER vs label manusia L2-ARCTIC | `NB01_*.json`, `NB01_per_clip.csv` |
| NB02_scratch_kws | CNN kecil dilatih dari nol di Speech Commands (35 kelas). Lengan "scratch" untuk perbandingan scratch vs pretrained | `NB02_scratch_kws.json`, `kws_scratch.pt` |
| NB03_asr_stream_eval | Jalur A: sherpa zipformer vs Vosk, streaming chunk 100 ms real-time. WER, latency partial pertama dan stabil, RTF, dengan dan tanpa hotwords | `NB03_*.json`, `NB03_per_clip.csv` |
| NB04_noise_conditions | Clip sendiri dicampur noise SNR 20/10/5 dB (seed tetap), ukur ulang PER dan WER | `NB04_*.json`, `NB04_per_clip.csv` |
| NB06_results_report | Baca semua `results/*.json`, buat tabel dan grafik. Tidak menghitung angka baru | `report_tables.md`, `fig_noise.png` |

NB05 (fine-tune, stretch) belum dibuat.

## 5. Urutan kerja yang disarankan

1. Push repo ke GitHub.
2. Run NB00 dan NB02 di Kaggle (tidak butuh rekaman).
3. Rekam clip dengan `record_clips.py`, upload sebagai `spellspeak-own-clips`.
4. Run `bench_rtf.py` di laptop terlemah. Ini gate Jalur B.
5. Run NB01 dan NB03, lalu NB04.
6. Copy semua `results/` ke repo, run NB06 untuk tabel laporan.

## 6. Catatan penting

- RTF dari CPU Kaggle bukan RTF laptop. Klaim real-time di laporan harus dari `bench_rtf.py` di laptop.
- `PER_MARGIN` di NB01 diisi sebelum melihat hasil. Kalau `None`, notebook hanya melapor tanpa verdict int8.
- Tabel ARPAbet ke IPA di NB01 masih draf. Cek dulu sebelum PER L2-ARCTIC dipakai di laporan.
- Angka hanya boleh masuk laporan kalau berasal dari file di `results/` yang dibuat oleh script atau notebook.
