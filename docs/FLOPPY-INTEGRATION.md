# Floppy Integration Contract

## Verified target

The deployed Floppy baseline used for this implementation is v26.8.27. Its source exposes two public v1 endpoints that match ETLP's needs without database access:

- `POST /api/v1/scrobble/` for `start`, `pause`, and `stop`.
- `PUT /api/v1/playback/progress/` for durable in-progress position updates.

Authentication supports Floppy API/integration tokens through `X-API-Key` (also supported upstream through Bearer/Token auth). ETLP never logs the configured token.

## Event mapping

`FloppyPlaybackBridge` in `utils/floppy_sync.py` owns the translation:

| Local event | Floppy call |
| --- | --- |
| player starts / resumes | scrobble `action=start` |
| player pauses | scrobble `action=pause` |
| periodic position | playback progress `PUT` |
| player/file stops | scrobble `action=stop` |
| reaches configured watched threshold | `completed=true` on progress/stop |

Events are serialized through a daemon queue so a slow Floppy request cannot block player polling and start/pause/stop ordering is preserved. Network/API failures are logged and discarded; existing Emby/Jellyfin/Plex reporting continues.

## Media identity

Movies use available `ProviderIds` from TMDB, IMDb or TVDB.

Episodes prefer the parent series ProviderIds plus `ParentIndexNumber` and `IndexNumber`. ETLP fetches parent-series metadata from Emby/Jellyfin when needed. If series metadata is unavailable, episode IMDb/TVDB IDs may be used because Floppy can remap them; an episode TMDB ID is deliberately not sent as a show TMDB ID.

## Configuration

```ini
[floppy]
enable = no
base_url = https://floppy.example.com
token =
enable_host = .
progress_interval = 30
completed_percent = 90
timeout = 5
verify_ssl = yes
```

`enable_host` follows ETLP's existing host-keyword convention. `.` means all media-server hosts.

## Idempotency

Every write includes a unique `Idempotency-Key`. Floppy's receipt layer can suppress a repeated delivery of the same event if a future retry mechanism is added.

## Scope boundaries

- No Floppy database reads/writes.
- No replacement of media-server playback reporting.
- No Floppy dependency when `[floppy] enable = no`.
- No requirement that the Tkinter GUI is installed or running.
