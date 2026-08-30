# GitHub CI baseline

## Purpose

The fork needs a credential-free verification baseline before Ryot code is added. CI runs entirely on GitHub-hosted runners and does not depend on the LOG workstation, an Emby/Jellyfin/Plex server, Trakt credentials, or a Ryot instance.

## Workflow

`.github/workflows/ci.yml` runs on branch pushes, pull requests and manual dispatches.

### Syntax compatibility

The project README declares Python 3.8 as the minimum supported version. The syntax matrix therefore checks:

- Python 3.8, preserving the documented compatibility floor;
- Python 3.13, representing the current runtime baseline used for new work.

Each matrix job runs `compileall` over the main entry point, `utils/`, and `embyBangumi/` without executing media-server or provider traffic.

### Provider import smoke test

A separate Python 3.13 job installs only `requests>=2.31,<3` and imports:

- `utils.trakt_api`;
- `utils.simkl_api`;
- `utils.bangumi_api`.

This catches broken provider-module imports without OAuth, media-server credentials or network calls to those services.

Provider-dispatch unit tests are intentionally deferred until a small testable dispatcher/helper is extracted as part of the Ryot integration. S0.5 does not refactor working playback code merely to manufacture a test seam.

## Verified baseline

Verified on 2026-08-30 against `feat/ryot-foundation` commit `d62565a557591ac51600924ef4f74d83079956db`.

GitHub Actions run: `33319956224`

Results:

- Python 3.8 compileall: passed;
- Python 3.13 compileall: passed;
- provider API import smoke test: passed.

No packaging artifact is produced at S0.5; release packaging remains a later stage after Ryot behavior has tests.
