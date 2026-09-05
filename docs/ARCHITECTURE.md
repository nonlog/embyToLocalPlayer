# Architecture

## Baseline

Fork baseline: `kjtsune/embyToLocalPlayer` `main` at `0554fd9c8b6759f41448927f4fdf4922d1f54ce3`.

## Playback path

```text
Browser userscript -> HTTP handler -> parse request -> optional persisted overrides
                  -> choose local player -> player-specific launcher/poller
                  -> media-server progress (existing, authoritative)
                  -> existing Trakt/Bangumi/Simkl completion sync
```

The fork adds two side channels without replacing that path:

```text
parsed request -> sanitized .tmp/last_request.json -> standalone config GUI
player poller  -> FloppyPlaybackBridge -> Floppy public v1 API
```

## Floppy bridge

`utils/floppy_sync.py` is deliberately separate from existing third-party completion providers because Floppy consumes real playback state rather than only the legacy >90% completion seam.

Player polling functions keep their existing return values and accept an optional `progress_callback`. mpv, VLC, MPC and PotPlayer report key/position/duration/pause state into the bridge. PotPlayer pause is inferred only after its position remains unchanged for a configurable interval because PotPlayer has no stable public pause-state API in the existing integration.

Floppy network work is serialized off the polling thread. The bridge maintains the current playlist item, emits start/pause/resume/progress/stop, and sends final stop events for played playlist items. Disabled or failed Floppy calls are no-ops with respect to playback.

## Configuration GUI

`config_gui.py` is a standalone entry point. It uses stdlib Tkinter and `utils/config_editor.py`; the server never imports it.

Common fields are written with a comment-preserving INI updater. The Advanced INI tab exposes the complete file for existing path maps and rarely used options. A sanitized snapshot written by `utils/config_state.py` lets the GUI display the latest parsed request without storing media-server credentials.

## PotPlayer compatibility

The launcher explicitly owns the Pot process:

- initial playback uses `/new`, preventing a transient forwarding process from becoming ETLP's tracked PID;
- playlist additions use `/current`, targeting the controlled Pot instance rather than depending on global single-instance preferences;
- tracked title aliases include the actual HTTP basename (`stream.mkv`), media basename and pretty/original names;
- localized `History/*.txt` files are scanned for modern-version title workarounds;
- Win32 progress reads use `SendMessageTimeoutW`, visible Pot windows only, and sanity checks;
- portable wrappers can be bypassed with `[potplayer] direct_exe` to avoid WinError 740/UAC mismatch.

These switches are documented by PotPlayer itself in `CmdLine64.txt` in both the 240618 and newer Windows-log installations.
