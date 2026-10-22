# godot

The game screen of SpellSpeak, built with Godot 4.3 or newer. It only shows the interface. The microphone, the voice activity detection and all scoring live in the Python backend.

## Run

1. Start the backend: `cd backend`, then `python server.py`.
2. Open this `godot/` folder in Godot 4.x.
3. Press Run, then press **Cast Spell**.

If the backend is not running, the status line says so.

## Files

| File | Purpose |
| --- | --- |
| `project.godot` | Project settings. The main scene is `main.tscn` and the window is 960 by 540 |
| `main.tscn` | The main scene. It holds one control that runs `main.gd` |
| `main.gd` | Builds the whole interface in code, connects to the backend and handles every message |

## How a round works

1. The screen shows a monster, a health bar and the spell word with its IPA hint.
2. **Cast Spell** sends `{"type": "start", "word": "..."}` to the backend. The state becomes listening.
3. The backend streams the player's voice through the microphone and sends `partial` messages. The screen shows them as "Heard".
4. When the backend detects that the player stopped, it sends `endpoint`. The state becomes scoring.
5. The backend sends `score`. The screen shows the phoneme errors and lowers the monster health on a hit.
6. If the backend sends `error`, the screen shows the detail and returns to idle.

## Mock banner

The yellow banner appears whenever the last message carried `"mock": true`. Right now `ready`, `partial` and `score` are still mock, and only `endpoint` is real. Values from mock messages are never results and must not be copied into the report.

## Attempt log

Each finished round appends a row to `user://attempts.csv`. In Godot, use Project, Open User Data Folder to find it. The columns include the `mock` flag, so mock rows can be filtered out.

## Placeholders

`MAX_ERRORS_FOR_HIT` in `main.gd` is a placeholder. Calibrate it from our own PER data before using it in any claim.

## Protocol

The protocol reference is the header of `backend/server.py`. Change the header first, then this client.
