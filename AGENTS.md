# Agent Guidelines

## Purpose

This fork adds optional self-hosted Floppy playback tracking and a standalone configuration GUI while preserving embyToLocalPlayer's media-server reporting and existing players/providers.

Read before changing fork-specific code:

- `docs/PRODUCT.md`
- `docs/ARCHITECTURE.md`
- `docs/FLOPPY-INTEGRATION.md`
- `docs/HANDOFF.md`
- `docs/UPSTREAM.md`

## Rules

- Emby/Jellyfin/Plex progress reporting remains authoritative and independent of Floppy.
- Floppy failures must never stop playback or prevent server progress updates.
- Use Floppy's public API; never write Floppy's database directly.
- Prefer TMDB/TVDB/IMDb identities. For episodes, prefer series IDs plus season/episode coordinates.
- Keep Trakt, Bangumi and Simkl behavior unchanged when Floppy is disabled.
- Keep the Tkinter configuration program standalone; CLI/background runtime must not import it.
- Keep request and player overrides in INI configuration, not hard-coded in playback logic.
- Preserve MPC/VLC/mpv compatibility when touching player polling.
- PotPlayer compatibility must support both 240618 and current builds. Do not require permanent elevation.
- Never commit credentials, integration tokens, private URLs containing secrets, or generated token files.
- Redact credentials from logs, request snapshots, tests and CI output.
- GitHub Actions is the canonical clean verification environment; Windows-log is used for real PotPlayer runtime validation.

## Git identity

For new commits created by Codex, both author and committer must resolve to:

```text
Codex <codex@openai.com>
```

Do not rewrite existing commit authorship.
