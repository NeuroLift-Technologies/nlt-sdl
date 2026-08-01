# Active Threads — nlt-sdl

> Live work state. Check before starting any thread. Update when you start/finish.

| Thread | Status | Owner | Notes |
|---|---|---|---|
| `NLT-HND-2026-001-SDL-Build-Kickoff` | **In review (draft PR)** | Claude Code | First cut: spec (NLT-SPEC-SDL-1.0.0) + conformance suite + RRTA & Sleepwalker Python reference adapters. Handback in `docs/agent-log/handoffs/`. |
| `ts-reference-impl` | **In review (draft PR)** | Claude Code | TypeScript reference (`reference/typescript/`, `@neurolift-technologies/sdl` v1.0.0). WRAPS the published TS canon packages; ports only the SDL's own policy brain. Passes the SAME 40 vectors as the Python reference (R25 equivalence verified). Branch `claude/ts-reference-impl`. Decision 1A (Joshua-approved). |
| `sdl-publish-prep` | **Complete (draft PR #7)** | Claude Code | npm publish-prep for both references (branch `claude/otoi-1.0.2-sweep`). Joshua-authorized via `docs/agent-log/approvals/vibe-approval.txt`. (1) TS: swapped canon `file:` deps → `^0.1.0`/`^1.0.0` from npm; (2) Python: switched to wrapping published PyPI packages (`rrt-advocate` v0.1.1, `sleepwalker-protocol` v1.0.1); (3) CI matrix runs all 40 vectors for both impls unconditionally (no CANON_REPO_TOKEN needed). Both: 40/40 conformance + full unit suites pass. |

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
- **Python reference canon resolution — ✅ RESOLVED** — The Python reference now
  wraps the PUBLISHED PyPI packages (`rrt-advocate` v0.1.1, `sleepwalker-protocol`
  v1.0.1) instead of the restructured local source repos. `_canon.py` resolves
  PyPI packages first (with legacy source fallback for local dev), `rrta_adapter.py`
  imports `from rrt_advocate` with `sentiment_analyzer=None` (heuristic fallback
  pin, matching the TS reference's `sentimentAnalyzer: null`), and `load_tier_ranges()`
  reads the bundled YAML via `importlib.resources`. Full Python conformance: **40/40**
  (was 10/40 failing closed). Both references now wrap published packages (PyPI + npm)
  and share a CI matrix that runs all 40 vectors unconditionally — no CANON_REPO_TOKEN needed.
- **Calibration measurement (ECE/MCE)** — the certification target includes
  calibration of `confidence`, including within the high-risk band. A measurement
  harness is not yet in this repo; tracked for a follow-up thread.
- **External clinician benchmark (mPACT-style)** — release gate for real users;
  not a code change to this layer.
