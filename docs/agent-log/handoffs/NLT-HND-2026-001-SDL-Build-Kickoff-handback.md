# Handback — NLT-HND-2026-001-SDL-Build-Kickoff

- **Governance:** ORG-DEV-OTOI-1.0.0
- **Authority:** Joshua W. Dorsey, Sr.
- **Agent:** Claude Code (Opus 4.8)
- **Date:** 2026-06-04
- **Thread:** SDL build kickoff (RRTA + Sleepwalker first cut)
- **Status:** Delivered as **draft PR** for review.

---

## 1. Scope delivered

Per the kickoff and Joshua's scope decision ("add Sleepwalker too"), this cut
delivers, in build order RRTA → Sleepwalker:

1. **Spec** — `NLT-SPEC-SDL-1.0.0`:
   - `spec/detection-result.schema.json` — the `DetectionResult` contract
     (JSON Schema draft 2020-12).
   - `spec/nlt-sdl-spec.md` — normative requirements `R1..R25`, the certification
     target (calibration / fail-closed / recall / equivalence — **not** accuracy),
     and the canonical tier table.
2. **Conformance suite** (the safety gate) — `conformance/`:
   - Vectors across `rrta/`, `sleepwalker/`, `failclosed/`, `equivalence/`,
     `adversarial/`, `false-positive/`. Every requirement is covered.
   - `conformance/runner/conformance.py` — validates each result against the
     schema and checks routing-critical expectations. **28/28 vectors pass.**
3. **Python reference implementation** — `reference/python/nlt_sdl/`:
   - `contract.py` — policy brain (tier derivation, R11 confidence clamp, R12
     explicit override, routing).
   - `failclosed.py` — fail-closed boundary (R20–R24).
   - `adapters/rrta_adapter.py`, `adapters/sleepwalker_adapter.py` — **wrappers**
     around canon (no rewrite).
   - `tests/` — 22 unit + integration tests pass.
4. **Governance + CI** — `AGENTS.md`, `CLAUDE.md`, `docs/active-threads.md`, and
   `.github/workflows/conformance.yml` (canon-free gate always runs; full
   canon-backed suite runs when `CANON_REPO_TOKEN` is present).

Verified locally: `28/28` conformance vectors and `22` pytest tests pass against
the live canonical detectors (Python 3.14, VADER absent — fallback path).

---

## 2. Real state of the pre-existing detectors (corrections to the kickoff)

The kickoff's assumptions were verified against the actual repos and corrected:

1. **RRTA detector path** is `rrt-advocate/src/crisis/detectors/` (plural
   `detectors`), not `detector/`. The detector is real and functional — a 3-layer
   pipeline (keyword 0.45 / sentiment 0.35 / behavioral 0.20).
2. **Lexicons are hard-coded in `keyword_layer.py`**, *not* in
   `crisis_thresholds.yaml`. The YAML owns the tier ranges, weights, and
   intervention mappings only. The SDL consumes both; it invents neither.
3. **Sleepwalker already ships a `StateDetector`** (`sleepwalker_protocol/
   state_detection.py`). Its reference impl is a *wrap*, not greenfield.
4. **Sleepwalker crisis patterns require apostrophes** (`can\'t`, `don\'t`) while
   RRTA's are apostrophe-optional (`can'?t`). Conformance vectors use
   apostrophe-independent crisis phrases so they fire regardless.
5. The cited TypeScript WIP files (`state-detector.ts`, `detector-agent.ts`) were
   never committed; the repo `README.md` describes them as intent.

---

## 3. Deviations from the kickoff (captured in canon)

1. **Contract shape adopted from the repo's founding `README.md`** (richer than
   the kickoff sketch): adds `recommendedMode`, `responseConstraints`,
   `suggestedPersona`, `escalateToHuman`, and `meta`. The README and the kickoff
   are compatible — the README defines the contract; the kickoff directs wrapping
   canon behind it.
2. **R11 enforced via a confidence clamp.** A non-explicit turn's reported
   `rrta.confidence` is clamped just below the red threshold (0.7) so it can never
   derive a red/black tier. This keeps `tier == derive(confidence)` a clean
   universal invariant (R2) while honoring the README's "crisis tier requires an
   explicit signal." **This is a deliberate safety policy — flagged for your
   review.**
3. **`suggestedPersona` is omitted (not emitted)** rather than guessed. The
   persona→mode mapping (Ash/Sol/Echo/Kai/Myra) is flagged in the README for
   reconciliation; I did not invent one.
4. **Enabler is reserved** (contract-only). No longitudinal implementation ships;
   the fade-vs-restrict response decision is decoupled and escalated to you.

---

## 4. Decisions that need Joshua

1. **Approve or adjust the R11 confidence clamp** (deviation #2 above) — it is the
   load-bearing false-positive control and changes the relationship between the
   canonical aggregate and the SDL's reported tier.
2. **Persona→mode mapping** — provide the canonical mapping, or confirm
   `suggestedPersona` stays omitted in 1.0.0.
3. **Enabler shape** — direction on the longitudinal detector and the
   fade-vs-restrict response ladder.
4. **CI canon access** — add a `CANON_REPO_TOKEN` secret with read access to
   `rrt-advocate` and `sleepwalker` so CI runs the full canon-backed suite (the
   canon-free gate runs without it).

---

## 5. Constraints honored

- Wrapped (did not rewrite or modify) the canonical detector source.
- Did not invent lexicons or thresholds; tiers loaded from
  `crisis_thresholds.yaml`.
- No diagnostic logic; no method/means enumeration. Coarse detection → human
  routing only.
- Fail-closed by construction; abstain upward; 100% recall on explicit signals.
- No persistent external storage of user crisis data; `meta.notes` carries no
  message content or PII.
- Did not create or modify `LICENSE`.
- Commits use `[CLAUDE] type(scope): description`; PR opened as draft.
