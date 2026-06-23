# Active Threads — nlt-sdl

> Live work state. Check before starting any thread. Update when you start/finish.

| Thread | Status | Owner | Notes |
|---|---|---|---|
| `NLT-HND-2026-001-SDL-Build-Kickoff` | **In review (draft PR)** | Claude Code | First cut: spec (NLT-SPEC-SDL-1.0.0) + conformance suite + RRTA & Sleepwalker Python reference adapters. Handback in `docs/agent-log/handoffs/`. |
| `ts-reference-impl` | **In review (draft PR)** | Claude Code | TypeScript reference (`reference/typescript/`, `@neurolift-technologies/sdl` v1.0.0). WRAPS the published TS canon packages; ports only the SDL's own policy brain. Passes the SAME 28 vectors as the Python reference (R25 equivalence verified). Branch `claude/ts-reference-impl`. Decision 1A (Joshua-approved). |

## Open / deferred

- **Enabler/Anti-Dependency shape** — reserved in 1.0.0 (contract field only). The
  longitudinal detector + the fade-vs-restrict *response* decision are deferred
  and escalated to Joshua separately. Do not implement without his direction.
- **TypeScript reference implementation** — ✅ **DELIVERED** (draft PR, branch
  `claude/ts-reference-impl`). `reference/typescript/` wraps the published TS
  canon packages and ports only the SDL's own policy brain; passes the same 28
  vectors as the Python reference (R25 equivalence verified field-by-field).
  Publish-prep: swap the two canon `file:` deps to the scoped published versions
  (`^0.1.0` / `^1.0.0`); and apply the `.github/workflows/conformance.yml` matrix
  change returned as an artifact (token lacks `workflow` scope).
- **Calibration measurement (ECE/MCE)** — the certification target includes
  calibration of `confidence`, including within the high-risk band. A measurement
  harness is not yet in this repo; tracked for a follow-up thread.
- **External clinician benchmark (mPACT-style)** — release gate for real users;
  not a code change to this layer.
