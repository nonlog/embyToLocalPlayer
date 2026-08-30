# Roadmap

## S0 - Fork initialization and architecture discovery

- [x] Create `nonlog/embyToLocalPlayer` as a real fork of `kjtsune/embyToLocalPlayer`.
- [x] Record baseline commit and upstream branch.
- [x] Audit Trakt API/sync implementation.
- [x] Locate the shared third-party completion dispatcher.
- [x] Document current >90% completion and per-provider dedupe behavior.
- [x] Define Ryot scope, identity rules and non-goals.
- [x] Add upstream/agent maintenance rules.

No functional Ryot code belongs to S0.

## S0.5 - GitHub CI baseline

- [x] Add a GitHub Actions workflow for branch pushes, pull requests and manual dispatches.
- [x] Verify the documented Python 3.8 minimum and Python 3.13 current baseline.
- [x] Add credential-free compile checks for the Python source tree.
- [x] Add credential-free import smoke tests for Trakt, Simkl and Bangumi provider API modules.
- [x] Defer provider-dispatch helper unit tests until a testable helper is extracted during Ryot integration instead of refactoring playback code solely for CI.
- [x] Verify the baseline on GitHub Actions run `33319956224`.

See `docs/CI.md` for the verified contract.
## S1 - Ryot connection contract

- Deploy/select a Ryot v10 test instance.
- Validate sink versus GraphQL behavior for external-ID based writes.
- Finalize `[ryot]` configuration keys.
- Implement a connection/configuration test.
- Verify credential redaction in logs.

## S2 - Completed item sync

- Add Ryot to the existing third-party completion dispatcher.
- Add movie completion using the current >90% semantics.
- Add TV episode completion with deterministic external-ID mapping.
- Test duplicate calls, network failure and unknown-media behavior.
- Confirm media-server progress still succeeds when Ryot fails.

## S3 - In-progress tracking

- Reuse existing player position events.
- Add bounded progress updates only for players where position/duration are reliable.
- Define stop/pause/resume semantics based on the validated Ryot API.
- Avoid unnecessary polling and new long-running loops.

## S4 - Provider cleanup and release

If four providers make the current hard-coded loops difficult to maintain, extract a small provider registry with regression tests. Do not turn this into a general plugin framework unless a real fifth-provider use case justifies it.

Then add release packaging/documentation through GitHub Actions.
