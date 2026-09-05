# Upstream Maintenance

- Upstream: `kjtsune/embyToLocalPlayer`
- Fork: `nonlog/embyToLocalPlayer`
- Recorded upstream baseline: `0554fd9c8b6759f41448927f4fdf4922d1f54ce3`
- Foundation branch: `feat/ryot-foundation` (historical name; pre-functional fork/docs baseline)
- Current feature branch: `feat/floppy-gui-potplayer`

Keep fork-specific changes small and separated by responsibility so upstream player/parser changes can still be merged or cherry-picked.

When updating from upstream:

1. fetch upstream and review player/parser/config diffs before merging;
2. preserve Floppy callback hooks without changing original player return contracts;
3. retain standalone GUI independence;
4. re-run unit/compile CI and Windows PotPlayer validation if `players.py`, `windows_tool.py`, config parsing or request parsing changed.

Never merge committed credentials or local deployment configuration from either side.
