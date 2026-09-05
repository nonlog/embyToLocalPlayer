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
- VLC/MPC regression tests verify that optional Floppy progress callbacks preserve the existing playlist stop-time return contracts.

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

## Production deployment on Windows-log

The production Scoop package has been moved from upstream to this fork and upgraded in place:

- Scoop bucket: `www` (`nonlog/scoop-www`)
- Installed version: `2026.09.05.3`
- Release: `nonlog/embyToLocalPlayer` tag `2026.09.05.3`
- Runtime commit for the patch release: `21aaba7ec13bbca6bebedc116fa503440a1bd2cf`
- Persistent config: `D:\Programs\Scoop\persist\embyToLocalPlayer\embyToLocalPlayer_config.ini`
- The persistent INI SHA-256 stayed identical across both Scoop upgrades, so existing settings were preserved.
- New shim: `embyToLocalPlayer_config` starts the standalone Tkinter configuration GUI.
- Configured player is `pot` at `D:\Programs\Scoop\apps\potplayer\current\PotPlayerMini64.exe`; the live 2026-09-05 log detects PotPlayer `260819`. Older 240618 and 251126 trees remain the compatibility-validation references.
- Background server smoke test on the installed package returned HTTP 200 from `127.0.0.1:58000` and the listener was cleanly removed after the test.
- Installed GUI smoke test loaded the real legacy INI without changing runtime defaults for missing new options. A dedicated regression test now covers those defaults.
- Floppy `v26.8.27` is reachable from Windows-log. In `2026.09.05.3`, the user's configured Floppy token passed a real read-only authentication test; the bridge loads as enabled with `timeout=5`, `progress_interval=30`, and completion threshold `80%`. No credential is stored in Git.
- `2026.09.05.3` also fixes blank Floppy numeric settings so empty or invalid values fall back safely instead of crashing playback, and avoids constructing a Floppy client at all when Floppy is disabled.
- The config GUI previously used `os.replace()` and could break Scoop's hardlink between the runtime INI and `persist`. The editor now detects symlinks/hardlinks and writes through the linked file. Windows-log's split config was reconciled, the `[floppy]` section was repaired, and a real no-op GUI-style save kept the hardlink intact. After cleanup, runtime and persist are the same hardlink with `nlink=2` and matching SHA-256.
- Trakt startup probing was removed in `2026.09.05.2`: Trakt is now lazy and is only contacted when a completed item matches `[trakt] enable_host`. Windows-log's persisted `trakt.enable_host` was cleared, while existing Trakt credentials/token were preserved. A real installed-package test with a non-empty test host and blank temporary credentials produced zero Trakt startup accesses and still returned HTTP 200 on port 58000; the original INI was restored byte-for-byte afterward.

The development checkout used for validation is separate at `D:\Workspace\embyToLocalPlayer-floppy`; its `.tmp` runtime fixtures are not part of Git.
