# Agent Guidelines

## Purpose

This fork adds optional self-hosted Ryot tracking to embyToLocalPlayer while preserving its existing media-server playback and third-party providers.

Read before changing Ryot-related code:

- `docs/PRODUCT.md`
- `docs/ARCHITECTURE.md`
- `docs/RYOT-INTEGRATION.md`
- `docs/UPSTREAM.md`
- `docs/ROADMAP.md`

## Rules

- Do not rewrite the player core for a provider-only feature.
- Emby/Jellyfin/Plex progress reporting remains independent of Ryot.
- Preserve Trakt, Bangumi and Simkl when Ryot is disabled.
- Start Ryot work at the existing `sync_third_party_for_eps` completion seam.
- Prefer external media IDs (TMDB/TVDB/IMDb and season/episode) over titles, filenames or Ryot internal IDs.
- Never commit credentials, integration slugs, tokens, private server URLs containing secrets, or generated token files.
- Redact credentials from logs and CI output.
- Keep diffs small enough to merge upstream changes safely.
- GitHub Actions is the canonical build/test environment; a developer workstation is not a required build dependency.

## Git identity

For new commits created by Codex, both author and committer must resolve to:

```text
Codex <codex@openai.com>
```

Do not rewrite existing commit authorship.
