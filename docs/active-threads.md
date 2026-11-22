# Active Threads — nlt-sdl

> Live work state. Check before starting any thread. Update when you start/finish.

### Thread: sdl-published-detector-imports
**Status:** pending review
**Owner:** Codex
**Branch:** `codex/retire-sdl-source-fallback`
**Task:** Verify published detector dependencies and remove retired Python source discovery.
**Scope:** Python adapters and integration tests, conformance setup, and dependency docs.
**Related PR:** Pending.
**Started:** 2026-11-22
**Last updated:** 2026-11-22
**Next action:** Review the dependency cleanup PR.

## Open / deferred

- **Enabler/Anti-Dependency shape** — reserved in 1.0.0 (contract field only). The
  longitudinal detector + the fade-vs-restrict *response* decision are deferred
  and escalated to Joshua separately. Do not implement without his direction.
- **Calibration measurement (ECE/MCE)** — the certification target includes
  calibration of `confidence`, including within the high-risk band. A measurement
  harness runs on [synthetic data](../conformance/calibration/README.md).
  Measured calibration remains pending the external benchmark.
- **External clinician benchmark (mPACT-style)** — release gate for real users;
  not a code change to this layer.

## Resolved threads

| Thread | Status | Owner | Notes |
|---|---|---|---|
| `NLT-HND-2026-001-SDL-Build-Kickoff` | Merged in [#1](https://github.com/NeuroLift-Technologies/nlt-sdl/pull/1) | Claude Code | Initial spec, conformance suite, and Python reference adapters. |
| `ts-reference-impl` | Merged in [#5](https://github.com/NeuroLift-Technologies/nlt-sdl/pull/5) | Claude Code | Added the TypeScript reference and checked R25 equivalence. |
| `sdl-publish-prep` | Merged in [#7](https://github.com/NeuroLift-Technologies/nlt-sdl/pull/7) | poolside | Switched both references to registry packages and enabled full conformance in CI. |
