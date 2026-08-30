# Product Direction

## Goal

Add optional self-hosted Ryot tracking to embyToLocalPlayer without disturbing its primary job: launching local players and reporting playback progress back to Emby/Jellyfin/Plex.

Ryot should become another third-party tracking target beside Trakt, Bangumi and Simkl, not a replacement for server playback reporting.

## S0/S1 scope

- Preserve existing player launch, playlist and server progress behavior.
- Preserve existing Trakt/Bangumi/Simkl integrations.
- Add a Ryot provider behind the existing post-play third-party sync path.
- Configure Ryot per media-server host using the same `enable_host` convention where practical.
- Validate the selected Ryot API/sink contract against a deployed instance before implementing writes.
- Keep GitHub as the canonical source/build location.

## Non-goals for the first stages

- Rewriting player management or IPC.
- Replacing Emby/Jellyfin/Plex playback progress reporting with Ryot.
- Implementing a complete Ryot client.
- Reworking all existing provider modules into a large framework before Ryot proves the need.
- Adding continuous scrobbling to every player in the first Ryot patch.
- Removing or changing existing 90% watched behavior without a separate compatibility decision.

## Current behavior to preserve

The current code records final stop positions, writes progress back to the media server, then calls `sync_third_party_for_eps` for enabled providers. That function only sends items whose local playback reached more than 90% and deduplicates them per provider for the current process.

The first Ryot slice should attach to that same proven completion path. Real-time start/progress/pause/resume support can follow later.

## Initial acceptance criteria

S1 is complete when:

- Ryot can be enabled/disabled from configuration without affecting other providers;
- configuration contains no committed credentials;
- a connection/integration test can fail cleanly;
- existing providers behave exactly as before when Ryot is disabled;
- automated verification runs from GitHub.
