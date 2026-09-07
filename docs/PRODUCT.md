# Product Direction

## Goal

Keep embyToLocalPlayer's existing Emby/Jellyfin/Plex + local-player behavior intact while adding three optional capabilities:

1. synchronize useful playback state to self-hosted Floppy through Floppy's public API;
2. configure ETLP through a lightweight standalone Python/Tkinter GUI;
3. restore reliable operation with current PotPlayer while retaining 240618 compatibility;
4. optionally override the Emby client/device identity ETLP sends back to the server.

## Invariants

- Media-server playback reporting remains the primary source of truth.
- Floppy is additive and disabled by default.
- Floppy failure never breaks local playback or server progress updates.
- GUI is a configuration surface only; service/CLI startup works without importing it.
- Existing mpv, VLC, MPC, IINA, Dandanplay and third-party sync behavior must not regress.
- Player/request overrides are persisted in INI and visible to the user.
- Emby identity overrides are opt-in, host-scoped, and blank fields preserve existing values.
- No permanent administrator requirement for PotPlayer.

## Acceptance criteria

- Floppy receives start, pause/resume where observable, periodic progress, stop and completion data through public endpoints.
- Episode identity is deterministic enough for Floppy (series external ID + season/episode preferred).
- GUI can edit playback/player, request override, Emby identity, network/path behavior, PotPlayer and Floppy settings; latest sanitized request can be inspected.
- Emby DeviceId/Device/Client/Version/User-Agent overrides are applied consistently to generated stream URLs, API/progress requests and authorization without changing Jellyfin/Plex behavior when disabled.
- PotPlayer works with local and HTTP media on old/current builds, does not lose the tracked PID through single-instance forwarding, and returns sane stop progress.
- Automated tests cover new mapping/config/Pot compatibility helpers and GitHub CI executes them.
