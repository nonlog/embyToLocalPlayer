# CI Contract

GitHub Actions is the canonical clean verification environment for this fork.

The workflow performs:

- syntax compilation on Python 3.8 and 3.13 for the server, standalone GUI, utils, Bangumi code and tests;
- import smoke tests for the existing Trakt/Simkl/Bangumi provider modules;
- Python 3.13 unit tests for Floppy mapping/failure isolation, request/config persistence and PotPlayer compatibility helpers.

CI is credential-free. It does not require Windows-log, a media server, Floppy, or any provider token. Real PotPlayer behavior remains a separate Windows-log runtime validation step because the Win32 window-message API cannot be meaningfully exercised on GitHub's Linux test job.
