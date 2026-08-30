# Upstream Maintenance

## Remotes and baseline

- Fork: `nonlog/embyToLocalPlayer`
- Upstream: `kjtsune/embyToLocalPlayer`
- Upstream default branch: `main`
- S0 baseline commit: `0554fd9c8b6759f41448927f4fdf4922d1f54ce3`
- Fork development branch: `feat/ryot-foundation`

## Policy

- Keep `main` close to upstream and usable.
- Develop Ryot changes on feature branches.
- Avoid unrelated player, downloader, GUI or networking refactors.
- Preserve Trakt, Bangumi and Simkl behavior.
- Prefer additions around the existing third-party sync seam before restructuring the playback core.
- Keep provider-specific code isolated in `utils/*_api.py` / `utils/*_sync.py` where that matches existing style.
- Record the upstream baseline for releases and major syncs.

## Upstream sync

Use a dedicated update branch, fetch `upstream/main`, review changes that touch playback or third-party sync paths, run GitHub verification, and merge normally. Do not routinely rewrite published history.

## CI

The baseline repository has no dedicated GitHub Actions workflow for this Ryot fork. A fork-owned, minimal CI workflow should be created before functional Ryot code is merged. It should use a clean Python environment and avoid relying on the developer's Windows installation.

## Commit identity

Commits created by the development agent use:

```text
Codex <codex@openai.com>
```

Set it at repository or per-command scope and do not alter historical authorship.
