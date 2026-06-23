# State Detection Layer (SDL)

> **Spec:** `NLT-SPEC-SDL-1.0.0` · **Status:** first conformant cut (RRTA + Sleepwalker)
> **Governance:** ORG-DEV-OTOI-1.0.2 · **Authority:** Joshua W. Dorsey, Sr.

A conservative, fail-closed state detector for the Solidarity Framework. It reads
a turn **before** the host agent calls the model and emits a routing decision —
how to respond, whether to surface human support, whether to escalate.

**This is a safety-critical routing net, not a clinical or diagnostic tool.** It
performs coarse crisis detection that routes to **human support**. It contains no
method/means language and makes no diagnostic claims. It is **not** ready to ship
to real users — see [Status](#status--before-this-ships-to-users).

The SDL is a **language-agnostic specification**, not a single file you drop in:

- **The spec** — a contract (`DetectionResult`) plus normative requirements `R1–R25`.
- **The conformance suite** — the safety gate. An implementation is "SDL-conformant"
  only if it passes every vector.
- **Reference implementation(s)** — currently one, in Python, that *wraps* the
  canonical `rrt-advocate` and `sleepwalker` detectors behind the contract.

## The three shapes (why it's not one classifier)

The SDL unifies three distinct detection *shapes* behind one output contract:

| Shape | Nature | Question it answers |
|---|---|---|
| **RRTA** | acute, in-session | "Is this turn in or near crisis right now?" |
| **Sleepwalker** | deterministic continuity | "Did continuity rupture, or is the user in a protective state?" |
| **Enabler** | longitudinal agency | "Is this user's agency eroding across sessions?" *(reserved in 1.0.0)* |

- **RRTA — acute.** Soft signal groups → graduated yellow/orange. Red/black require
  an **explicit** hard-distress signal; never inferred from soft overwhelm.
- **Sleepwalker — deterministic.** Fires off *facts* the host already knows
  (model/version change, handoff, memory gap, tone shift). These bypass the
  confidence floor — they aren't guesses.
- **Enabler — longitudinal, reserved.** Contract-only in 1.0.0; ships `risk="none"`.
  Never labels dependency from a single turn.

## What it emits (the contract)

Every observed turn returns a `DetectionResult` validating against
[`spec/detection-result.schema.json`](spec/detection-result.schema.json):

```jsonc
{
  "rrta":        { "tier": "orange", "confidence": 0.59, "signals": ["overwhelm","task_paralysis"], "explicitSignal": false },
  "sleepwalker": { "vulnerable": false, "events": [], "signals": [] },
  "enabler":     { "risk": "none", "confidence": 0.0, "agencyTrend": 0, "signals": [] },
  "recommendedMode": "rrta_soft_scaffold",
  "responseConstraints": ["reduce_to_one_next_step","no_large_lists","preserve_choice","avoid_shame_language","slow_pace"],
  "escalateToHuman": false,
  "meta": { "failClosed": false, "schemaVersion": "1.0.0", "notes": [] }
}
```

The host's response router consumes `recommendedMode` + `responseConstraints` (and
the optional `suggestedPersona`) when assembling the model call. The detector never
composes the model response itself.

Canonical crisis **tiers** and their numeric ranges are owned by
`rrt-advocate config/crisis_thresholds.yaml` and consumed here, never reinvented:

| Tier | Range | Meaning |
|---|---|---|
| green | `[0.0, 0.2)` | stable |
| yellow | `[0.2, 0.4)` | elevated |
| orange | `[0.4, 0.7)` | high |
| red | `[0.7, 0.9)` | critical |
| black | `[0.9, 1.0]` | emergency |

## Repository layout

```
spec/
  nlt-sdl-spec.md               # NLT-SPEC-SDL-1.0.0 — requirements R1–R25
  detection-result.schema.json  # the DetectionResult contract (JSON Schema 2020-12)
conformance/
  README.md                     # vector format + runner contract
  runner/conformance.py         # the safety gate
  vectors/                      # rrta/ sleepwalker/ failclosed/ equivalence/ adversarial/ false-positive/
reference/python/
  nlt_sdl/                      # the reference implementation
    contract.py                 #   policy brain: tier derivation, R11 clamp, routing
    failclosed.py               #   fail-closed boundary (R20–R24)
    adapters/                   #   wrappers around canonical rrt-advocate / sleepwalker
  tests/                        # unit + integration tests
.github/workflows/conformance.yml
```

## Run the conformance suite

The reference implementation *wraps* canon — it does not vendor it. Point it at
the canonical sibling repos via env vars (or place them as siblings of this
checkout):

```bash
pip install jsonschema pyyaml pytest     # pytest needed only for the unit suite
export RRT_ADVOCATE_SRC=/path/to/rrt-advocate/src
export SLEEPWALKER_ROOT=/path/to/sleepwalker
export PYTHONPATH=reference/python

# Conformance (the safety gate)
python conformance/runner/conformance.py --impl python

# Unit + integration tests
python -m pytest reference/python/tests -q
```

Without canon reachable, run the **canon-free gate** — fail-closed vectors still
run; canon-backed vectors are skipped:

```bash
python conformance/runner/conformance.py --impl python --skip-requires-canon
```

CI (`.github/workflows/conformance.yml`) always runs the canon-free gate; the full
canon-backed suite runs when a `CANON_REPO_TOKEN` secret with read access to
`rrt-advocate` and `sleepwalker` is present.

> Installing `vaderSentiment` improves Layer 2 calibration but is optional — the
> routing-critical guarantees do not depend on it.

## Safety invariants (deliberate — loosen only with eval evidence)

1. Defaults to green/standard; asserts nothing below the confidence floor.
2. Crisis tier (red/black) requires an **explicit** signal — never inferred from
   soft overwhelm (enforced by a confidence clamp; spec **R11**).
3. On uncertainty the posture is *gentle* — reduce pressure, preserve choice,
   surface support — never dramatic, never silent when distress is explicit (**R19**).
4. **Fail-closed (R20–R24).** Any detector that raises, times out, or returns
   malformed output yields an escalating `meta.failClosed` result. Abstention is
   always *upward*, never silent green.
5. **100% recall on explicit signals → human routing (R22).** No explicit
   hard-distress signal may ever yield `escalateToHuman=false`, even under partial
   outage. Emergency routing is derivable from signals alone, with no model call (**R23**).
6. Longitudinal state holds counts/trends only — no message content; results carry
   no PII (**R4**).

## Status — before this ships to users

The spec, conformance suite, and Python reference are merged and green
(28/28 conformance vectors, 22 unit/integration tests). The following are open and
**gated on Joshua** (see
[`docs/agent-log/handoffs/NLT-HND-2026-001-SDL-Build-Kickoff-handback.md`](docs/agent-log/handoffs/NLT-HND-2026-001-SDL-Build-Kickoff-handback.md)):

1. **R11 confidence clamp** — approve/adjust the load-bearing false-positive control.
2. **Persona→mode mapping** — `suggestedPersona` is currently omitted, not guessed.
3. **Enabler shape** + the decoupled fade-vs-restrict response ladder.
4. **`CANON_REPO_TOKEN`** CI secret so CI runs the full canon-backed suite.

Beyond those, a real-user gate still needs adversarial fail-closed coverage and a
**measured false-positive rate** — do not stub those green. Stronger detection is
the clinician / eval-data track (mPACT-style ground truth), not a code change:
swap a detector behind the same contract when that data exists.

## Reconcile against canon

The RRTA lexicons and tier cutoffs live in `rrt-advocate` (lexicons in
`keyword_layer.py`; tiers/weights in `config/crisis_thresholds.yaml`). Sleepwalker
wraps `sleepwalker_protocol/state_detection.py`. This layer **consumes** both and
**invents neither** — no lexicons or thresholds are defined here.
