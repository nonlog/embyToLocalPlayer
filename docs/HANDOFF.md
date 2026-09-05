# Development Handoff

## Source state

- Repository: `nonlog/embyToLocalPlayer`
- Development branch: `feat/floppy-gui-potplayer`
- Baseline: `feat/ryot-foundation` at `3ec4a6f21e5b5089fb71bfa24db15103c6a368bc`
- First implementation commit: `e0744412cfa7c127586a7391e7bde1ee38dd7d53`
- PotPlayer 240618 compatibility follow-up: `e1524481db6e306ad24476287e9a6a17c947ed67`

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
- PotPlayer title handling is version-specific: 240618 only replaces ASCII double quotes; newer builds use the stricter quote/space mapping needed by current PotPlayer.
- PotPlayer Win32 progress IPC uses bounded `SendMessageTimeoutW`, ignores invalid time values, and exits polling after an already-seen playback window closes even if Pot keeps a background/tray window.
- Portable/elevated wrapper mitigation through `[potplayer] direct_exe`; WinError 740 is reported as a direct-executable configuration problem rather than recommending permanent administrator mode.
- Progress observation hooks added to mpv, VLC, MPC and PotPlayer without changing their existing return contracts.
- Unit tests and GitHub CI test job added.

## Windows-log validation (2026-09-05)

Validation was performed from a clean clone of the GitHub feature branch. No phone screenshots or foreground-phone content were captured.

Environment:

- Python 3.14.7, Tk 9.0.
- PotPlayer old tree: `D:\Tools\Player\PotPlayer\PotPlayerMini64.exe`, localized History reports `240618`.
- PotPlayer current tree: `D:\Tools\Player\PotPlayer2\PotPlayerMini64.exe`, localized History reports `251126`.
- Both installations' own `CmdLine64.txt` document `/new`, `/current`, `/seek`, `/sub`, and `/title`.

Runtime matrix (generated 16-second H.264/AAC MKV):

| PotPlayer | Source | Result |
| --- | --- | --- |
| 240618 | local MKV | PASS: 16 s duration, progress reached 9 s, stable controlled PID |
| 240618 | HTTP `stream.mkv` | PASS: 16 s duration, progress reached 10 s, stable controlled PID |
| 251126 | local MKV | PASS: 16 s duration, progress reached 8 s, stable controlled PID |
| 251126 | HTTP `stream.mkv` | PASS: 16 s duration, progress reached 11 s, stable controlled PID |

In all four cases `/current /add` returned 0 and the original `/new` PID remained valid. No Pin-render error, `KeyError: 'stream.mkv'`, `pot stop, stop_sec=None`, or WinError 740 occurred. The first run intentionally exposed a 240618 double-quote title incompatibility; the version-specific fix was then added and the complete matrix passed on the second run.

GUI smoke validation created the window in withdrawn mode and loaded all seven tabs (`Playback`, `Request overrides`, `PotPlayer`, `Network & behavior`, `Floppy`, `Last request`, `Advanced INI`) with 42 editable variables.

Windows-log can reach `https://floppy.414222.xyz/api/v1/info/`; it returned HTTP 200 and Floppy `v26.8.27`. No Floppy credential is committed to this repository, so authenticated write testing requires a user-created Floppy integration/API token.

## Existing installed deployment discovered on Windows-log

The currently installed production copy is still the upstream Scoop package:

- Scoop bucket: `www`
- Installed version: `2026.07.18`
- Package source/homepage: upstream `kjtsune/embyToLocalPlayer`
- Persistent config: `D:\Programs\Scoop\persist\embyToLocalPlayer\embyToLocalPlayer_config.ini`
- Configured player: `pot`
- Configured Pot path: `D:\Tools\Player\PotPlayer\PotPlayerMini64.exe` (240618)
- Server progress reporting: enabled
- No ETLP Python background process was running during validation.

The development checkout used for testing is separate at `D:\Workspace\embyToLocalPlayer-floppy`; its `.tmp` runtime fixtures are not part of Git.
