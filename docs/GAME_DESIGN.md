# Game design (Godot 4)

Name: SpellSpeak. Wizard apprentice trains pronunciation by casting words at monsters. Content is hard English sounds for Indonesian learners. No Harry Potter names, spells, or characters.

## Core loop (one round, about 20 seconds)
1. Screen shows a monster, its HP bar, the target word, and its IPA.
2. Player presses Cast (or Space) and speaks. Mic meter moves. Partial transcript appears live (Jalur A, display only).
3. VAD ends the utterance. Status: "Scoring...".
4. Phoneme runes light up per sound: green match, orange substituted, red missing/extra (from `score` message).
5. Damage depends on the score bucket. Thresholds are calibrated from our own data. Until then they are PLACEHOLDERS in `config.gd` and the UI says so.
6. Monster defeated or next round. Failed sound goes to the end-of-session summary.

## Screens
1. Title and mic check (level meter, "say hello").
2. Level select: 3 tiers (Apprentice, Adept, Archmage).
3. Battle (main screen).
4. Session summary: top confusions (for example /θ/ heard as /t/), words to retry, per-word PER. This screen is also the user-testing material.
5. Settings: mic device, show IPA on/off, show Indonesian hint on/off.

## Battle wireframe
```
+--------------------------------------------------------+
| [MOCK MODE banner when backend says mock]              |
|  Monster HP [#########-----]        Round 2/5          |
|                                                        |
|   (wizard)                 (monster sprite)            |
|                                                        |
|            T H I N K      /θ ɪ ŋ k/                    |
|   runes:   [θ→t] [ɪ] [ŋ] [k]                           |
|   Heard (live): "thin"                                 |
|   Hint: lidah di antara gigi, tanpa suara              |
|   mic ||||||||----        [ Cast (Space) ]            |
+--------------------------------------------------------+
```

## State machine (Godot side)
IDLE -> LISTENING (on Cast, send `start`) -> SCORING (on `endpoint`) -> RESULT (on `score`) -> IDLE or VICTORY.
Errors (`error` message, socket closed) go to a visible error state. Never fake a result when the backend is down.

## Tiers and endpoint parameters
| Tier | Content | Endpoint parameters |
| --- | --- | --- |
| 1 Apprentice | single words, one target sound | placeholders, calibrate |
| 2 Adept | harder words, clusters | placeholders, calibrate |
| 3 Archmage | short phrases | placeholders, calibrate |
Parameters (silence timeout, hesitation allowance, max length) live in one config file and are tuned on own recordings.

## Candidate word bank
In `backend/words.json`. All entries are candidates. Validate each one with phonemizer + espeak-ng and drop words the model alphabet cannot express. Target sounds: /θ/, /ð/, /v/ vs /f/, final consonant clusters, /æ/ vs /ɛ/.

## Hints
Short Indonesian hints per sound. Draft below. Verify with a phonetics source or a linguistics lecturer before use.
- /θ/: ujung lidah di antara gigi, tanpa getaran suara.
- /ð/: sama seperti /θ/ tetapi dengan getaran suara.
- /v/: gigi atas menyentuh bibir bawah, dengan suara (beda dengan /f/ tanpa suara).
- /æ/ vs /ɛ/: /æ/ mulut lebih terbuka daripada /ɛ/.

## Visual and audio
Keep scope small: flat 2D, placeholder shapes first, one monster sprite and one wizard sprite from free-license assets or own drawing (check licenses, no copyrighted characters). Sound effects optional. Priority is the loop and the feedback, not art.

## Godot implementation notes
- UI builds in code (`main.gd`) today. Move to scenes once the loop is stable.
- `WebSocketPeer` polls in `_process`. Reconnect with a button, not silently.
- Mic capture stays in Python. Godot never touches audio.
- Keep message handling in one function so the protocol is easy to extend.

## Protocol extensions planned
`audio_level` (mic meter), `config` (tier params from backend), `session_summary`. Add them to the header of `backend/server.py` first, then to Godot.
