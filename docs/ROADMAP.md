# Roadmap

## S0 - Fork initialization

- [x] Fork baseline and upstream tracking.
- [x] Architecture/product documentation.
- [x] GitHub CI compile/import baseline.

## S1 - Floppy public API integration

- [x] Verify deployed Floppy v26.8.27 `scrobble` and `playback/progress` APIs.
- [x] Add configurable API client and failure isolation.
- [x] Map movie/episode external IDs.
- [x] Add start/pause/resume/progress/stop/completed events.
- [x] Add unit coverage and idempotency headers.

## S2 - Configuration GUI

- [x] Standalone Tkinter entry point.
- [x] Playback/player/network/PotPlayer/Floppy fields.
- [x] Persisted request overrides and per-player JSON args.
- [x] Sanitized latest-request viewer.
- [x] Full advanced INI editor while preserving CLI/background independence.

## S3 - PotPlayer compatibility

- [x] Controlled `/new` initial instance and `/current` playlist append.
- [x] `stream.mkv`/HTTP basename aliases.
- [x] Localized modern-version detection.
- [x] Bounded/sane Win32 progress IPC.
- [x] Direct-executable path for portable/elevation wrappers.
- [x] Complete Windows-log old/current local-file + HTTP runtime validation.

## S4 - Merge/release

- [x] Green GitHub Actions on feature branch (implementation commits validated; final commit rechecked before promotion).
- [x] Update handoff with Windows validation findings.
- [ ] Commit/push with Codex identity and open/merge PR according to project policy.
