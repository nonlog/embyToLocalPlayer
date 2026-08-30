# Ryot Integration Contract

## Status

S0 design only. The exact write mechanism must be verified against the deployed Ryot v10 instance during S1.

Official references:

- https://docs.ryot.io/
- https://docs.ryot.io/configuration
- https://docs.ryot.io/integrations/overview.html
- https://docs.ryot.io/integrations/emby
- https://docs.ryot.io/guides/movies-and-shows
- https://github.com/IgnisDa/ryot

Ryot supports self-hosted integrations and advertises GraphQL for custom integrations. It also has sink webhooks such as its Emby integration at `https://<instance>/_i/<slug>`.

## API decision gate

Do not hard-code a GraphQL mutation or spoof an Emby webhook until S1 validates the current v10 behavior.

Evaluate these options in order:

1. A documented/stable sink payload suitable for ETLP completion/progress events.
2. Authenticated GraphQL operations if a sink cannot express the required state reliably.

The selected mechanism must support a self-hosted base URL and must not require a Ryot internal metadata ID as the input identity when external IDs can be resolved.

## Proposed configuration

The exact keys may change after the API validation, but configuration should follow the existing provider style:

```ini
[ryot]
# Media-server host keywords for which Ryot sync is enabled.
enable_host =

# Example: https://ryot.example.com
base_url =

# Token or integration slug/URL, depending on the validated S1 mechanism.
# Never commit a real value.
credential =
```

If a Ryot integration URL itself contains the secret slug, treat the complete URL as a credential.

## Completion payload semantics

The first slice reuses ETLP's existing completion threshold: only items over 90% are sent from the third-party completion dispatcher.

Normalized information should include:

```text
media type
TMDB / TVDB / IMDb IDs present in Emby/Jellyfin/Plex metadata
series identity for episodes
season and episode numbers
watched/completed state
watched timestamp when available
playback source/server for diagnostics
```

The Ryot adapter owns conversion from this neutral model to the chosen network request.

## TV episode caveat

Ryot's official Emby integration notes that show progress may only sync when the show already exists in Ryot because Emby does not send the show TMDB ID in the form Ryot expects. ETLP has access to additional item/series metadata and should attempt deterministic external-ID mapping rather than relying on a title guess.

This behavior must be included in S2 tests using both a movie and a TV episode.

## Reliability

- A Ryot failure must never prevent Emby/Jellyfin/Plex progress from being written.
- Third-party sync stays asynchronous relative to playback shutdown where the current code already behaves that way.
- Authentication failures should be logged distinctly from media-match failures.
- Network retries must be bounded.
- Do not mark an item as "synced" in the in-process dedupe cache before a failed Ryot write is handled correctly; current provider behavior should be reviewed here when implementing Ryot.
- Logs must redact credentials and secret integration URLs.

## Future progress sync

If real-time Ryot progress is added later, it should consume the existing player position events rather than introducing a second player-monitoring loop solely for Ryot. The event model should be roughly:

```text
start
progress(position, duration)
pause/resume (when available)
stop(position, duration)
complete
```

Provider-specific translation belongs in the Ryot adapter.
