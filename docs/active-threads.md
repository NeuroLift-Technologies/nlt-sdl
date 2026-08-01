# Active Threads — nlt-sdl

> Live work state. Check before starting any thread. Update when you start/finish.

| Thread | Status | Owner | Notes |
|---|---|---|---|
| `NLT-HND-2026-001-SDL-Build-Kickoff` | **In review (draft PR)** | Claude Code | First cut: spec (NLT-SPEC-SDL-1.0.0) + conformance suite + RRTA & Sleepwalker Python reference adapters. Handback in `docs/agent-log/handoffs/`. |
| `ts-reference-impl` | **In review (draft PR)** | Claude Code | TypeScript reference (`reference/typescript/`, `@neurolift-technologies/sdl` v1.0.0). WRAPS the published TS canon packages; ports only the SDL's own policy brain. Passes the SAME 40 vectors as the Python reference (R25 equivalence verified). Branch `claude/ts-reference-impl`. Decision 1A (Joshua-approved). |
| `sdl-publish-prep` | **In progress** | Claude Code | npm publish-prep for the TS reference (branch `claude/otoi-1.0.2-sweep`). Joshua-authorized via `docs/agent-log/approvals/vibe-approval.txt`. Swap canon `file:` deps → `^0.1.0`/`^1.0.0`; regenerate lockfile; add TS to `.github/workflows/conformance.yml` matrix. TS: 40/40 vectors + 41/41 vitest verified. |

## Open / deferred

- **Enabler/Anti-Dependency shape** — reserved in 1.0.0 (contract field only). The
  longitudinal detector + the fade-vs-restrict *response* decision are deferred
  and escalated to Joshua separately. Do not implement without his direction.
- **TypeScript reference implementation** — ✅ **DELIVERED + PUBLISH-PREP COMPLETE**
  (branch `claude/otoi-1.0.2-sweep`). `reference/typescript/` wraps the published TS
  canon packages and ports only the SDL's own policy brain; passes all **40**
  conformance vectors (R25 equivalence with the Python reference, verified
  field-by-field). Publish-prep (Joshua-authorized via `docs/agent-log/approvals/vibe-approval.txt`):
  (1) swapped canon `file:` deps → `^0.1.0` / `^1.0.0` (`rrt-advocate@0.1.1`,
  `sleepwalker-protocol@1.0.2` from npm); (2) regenerated `package-lock.json`;
  (3) applied `.github/workflows/conformance.yml` matrix change gating both
  `[python, typescript]` references against the same 40 vectors.
  Verified: `npm run build` (clean) + `npm test` (41/41 vitest) +
  `--impl typescript` (40/40 conformance). The TS reference wraps **published npm**
  canon packages, so it runs the full suite without checking out private source repos.
- **Python reference canon resolution (BLOCKER — pre-existing, escalated)** —
  The canonical repos were restructured (rrt-advocate commit `eb1592d`: "archive
  legacy Python, rewrite docs to match published APIs"), archiving the legacy
  `crisis` package and moving `sleepwalker_protocol` to `src/`. The Python
  reference's `_canon.py` + adapters still import the old `crisis.detectors...`
  and `sleepwalker_protocol` (root) paths. The fail-closed boundary behaves
  **correctly** (safe escalation to human, never silent green), but the full
  Python suite (40 vectors) cannot resolve canon in the current environment.
  The canon-free gate passes for both impls (TS: 5/5 + 40/40; Python: 5/5).
  Updating the Python adapter import paths to match the new canonical repo
  layout is a **separate task requiring Joshua's direction** (touches canon
  resolution semantics) — do not bundle with publish-prep.
- **Calibration measurement (ECE/MCE)** — the certification target includes
  calibration of `confidence`, including within the high-risk band. A measurement
  harness is not yet in this repo; tracked for a follow-up thread.
- **External clinician benchmark (mPACT-style)** — release gate for real users;
  not a code change to this layer.
