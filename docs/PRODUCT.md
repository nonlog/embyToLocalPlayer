# Product Direction

## Goal

Keep embyToLocalPlayer's existing Emby/Jellyfin/Plex + local-player behavior intact while adding three optional capabilities:

1. synchronize useful playback state to self-hosted Floppy through Floppy's public API;
2. configure ETLP through a lightweight standalone Python/Tkinter GUI;
3. restore reliable operation with current PotPlayer while retaining 240618 compatibility.

## Invariants

- Media-server playback reporting remains the primary source of truth.
- Floppy is additive and disabled by default.
- Floppy failure never breaks local playback or server progress updates.
- GUI is a configuration surface only; service/CLI startup works without importing it.
- Existing mpv, VLC, MPC, IINA, Dandanplay and third-party sync behavior must not regress.
- Player/request overrides are persisted in INI and visible to the user.
- No permanent administrator requirement for PotPlayer.

## Acceptance criteria

- Floppy receives start, pause/resume where observable, periodic progress, stop and completion data through public endpoints.
- Episode identity is deterministic enough for Floppy (series external ID + season/episode preferred).
- GUI can edit playback/player, request override, network/path behavior, PotPlayer and Floppy settings; latest sanitized request can be inspected.
- PotPlayer works with local and HTTP media on old/current builds, does not lose the tracked PID through single-instance forwarding, and returns sane stop progress.
- Automated tests cover new mapping/config/Pot compatibility helpers and GitHub CI executes them.
