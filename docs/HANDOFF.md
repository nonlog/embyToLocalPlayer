# Development Handoff

## Branch

Current development branch: `feat/floppy-gui-potplayer`, based on `feat/ryot-foundation` at `3ec4a6f21e5b5089fb71bfa24db15103c6a368bc`.

## Implemented

- Floppy public-API adapter (`scrobble` + playback progress) with start/pause/resume/progress/stop/completed semantics.
- External-ID mapping for movies and episodes, including parent-series lookup for episodes.
- Failure-isolated, ordered background delivery and API idempotency keys.
- Standalone `config_gui.py` using Tkinter; CLI/background startup does not import it.
- Comment-preserving INI writes for common GUI fields, plus a full Advanced INI editor.
- Persisted safe request overrides and JSON player extra arguments.
- Sanitized `.tmp/last_request.json` for GUI inspection; auth/query secrets are redacted.
- PotPlayer controlled instance launch (`/new`) and playlist append (`/current`).
- PotPlayer playlist aliases include media title, original basename, `media_basename`, and HTTP URL basename such as `stream.mkv`.
- PotPlayer version detection scans localized `History/*.txt`, not only `History/English.txt`.
- PotPlayer Win32 progress IPC uses bounded `SendMessageTimeoutW` and ignores non-playback windows/invalid time values.
- Portable/elevated wrapper mitigation through `[potplayer] direct_exe`; WinError 740 is reported as a direct-executable configuration problem rather than recommending permanent administrator mode.
- Progress observation hooks added to mpv, VLC, MPC and PotPlayer without changing their existing return contracts.
- Unit tests and GitHub CI test job added.

## Validation state

Linux/CI-style unit and compile checks are expected before commit. Windows-log runtime validation must cover both local PotPlayer trees:

- `D:\Tools\Player\PotPlayer\PotPlayerMini64.exe` (History baseline 240618)
- `D:\Tools\Player\PotPlayer2\PotPlayerMini64.exe` (newer branch, previously observed 25xxxx history)

Test local file, HTTP URL, title containing spaces/quotes, progress polling and normal stop. Do not use phone screenshots.

## Remaining deployment setup

Floppy is disabled in the committed sample configuration and contains no credential. On a real machine, set `[floppy] base_url`, token, and `enable=yes` through `config_gui.py` or the INI. Prefer a scoped Floppy integration/API token.
