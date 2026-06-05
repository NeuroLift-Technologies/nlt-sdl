# Active Threads — nlt-sdl

> Live work state. Check before starting any thread. Update when you start/finish.

| Thread | Status | Owner | Notes |
|---|---|---|---|
| `NLT-HND-2026-001-SDL-Build-Kickoff` | **In review (draft PR)** | Claude Code | First cut: spec (NLT-SPEC-SDL-1.0.0) + conformance suite + RRTA & Sleepwalker Python reference adapters. Handback in `docs/agent-log/handoffs/`. |

## Open / deferred

- **Enabler/Anti-Dependency shape** — reserved in 1.0.0 (contract field only). The
  longitudinal detector + the fade-vs-restrict *response* decision are deferred
  and escalated to Joshua separately. Do not implement without his direction.
- **TypeScript reference implementation** — the repo README describes a
  host-agnostic `state-detector.ts` WIP. When built, it must pass this exact
  conformance suite (R25 equivalence). Not in scope for the first PR.
- **Calibration measurement (ECE/MCE)** — the certification target includes
  calibration of `confidence`, including within the high-risk band. A measurement
  harness is not yet in this repo; tracked for a follow-up thread.
- **External clinician benchmark (mPACT-style)** — release gate for real users;
  not a code change to this layer.
