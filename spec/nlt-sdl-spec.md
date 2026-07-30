# NLT-SPEC-SDL-1.0.0 — State Detection Layer Specification

> **Governance:** ORG-DEV-OTOI-1.0.2 · **Authority:** Joshua W. Dorsey, Sr.
> **Status:** Draft for review (first conformant cut: RRTA + Sleepwalker)
> **Schema:** [`detection-result.schema.json`](./detection-result.schema.json) (JSON Schema draft 2020-12)

---

## 0. What this is, and what it is not

The **State Detection Layer (SDL)** is a *language-agnostic specification* — a
contract plus a conformance suite plus one or more conformant reference
implementations. It is **not** a single codebase and **not** a classifier.

The SDL unifies three distinct detection *shapes* behind one output contract so a
host agent can route a turn before it calls the model:

| Shape | Nature | Question it answers |
|---|---|---|
| **RRTA** | acute, in-session | "Is this turn in or near crisis right now?" |
| **Sleepwalker** | deterministic continuity | "Did continuity rupture, or is the user in a protective state?" |
| **Enabler** | longitudinal agency | "Is this user's agency eroding across sessions?" *(reserved in 1.0.0)* |

**This is a safety-critical routing net, not a clinical or diagnostic tool.** It
performs coarse crisis detection that routes to **human support**. It contains no
method/means language and makes no diagnostic claims. Stronger detection is a
clinician / eval-data track (mPACT-style ground truth), not a code change to this
layer — swap a detector behind the same contract when that data exists.

### Certification target

Conformant implementations are certified on **calibration, fail-closed behavior,
recall on explicit signals, and cross-implementation equivalence** — **not** on
"accuracy." "Solving accurate internal-state detection" is explicitly out of scope.

---

## 1. The contract

Every conformant implementation MUST, for every observed turn, return an object
validating against `detection-result.schema.json`. The router consumes
`recommendedMode` + `responseConstraints` (+ optional `suggestedPersona`); the
detector never composes the model response itself.

Canonical crisis **tiers** (`green/yellow/orange/red/black`) and their numeric
ranges are owned by `rrt-advocate config/crisis_thresholds.yaml`:

| Tier | Range | Meaning |
|---|---|---|
| green | `[0.0, 0.2]` | stable |
| yellow | `[0.2, 0.4]` | elevated |
| orange | `[0.4, 0.7]` | high |
| red | `[0.7, 0.9]` | critical |
| black | `[0.9, 1.0]` | emergency |

Implementations **MUST NOT** redefine these ranges, the layer weights
(L1 keyword 0.45 / L2 sentiment 0.35 / L3 behavioral 0.20), or the lexicons.
Those live in canon and are consumed, not reinvented.

---

## 2. Normative requirements

Each requirement has a stable ID. The conformance suite MUST cover **every**
requirement with at least one vector or runner check. Fail-closed requirements
(R20–R24) are mandatory and MUST NOT be stubbed green.

### Contract & schema

- **R1** — Every result MUST validate against `detection-result.schema.json`.
- **R2** — `rrta.tier` MUST be derived from `rrta.confidence` using exactly the
  canonical ranges in §1 (half-open `[low, high)`, top tier inclusive of 1.0).
- **R3** — `meta.schemaVersion`, when present, MUST equal the contract version the
  implementation targets (`1.0.0`).
- **R4** — Results MUST NOT contain user message content or PII in any field,
  including `meta.notes`.

### RRTA — acute, in-session

- **R10** — When no signals are present, `rrta.tier` MUST be `green` and
  `rrta.explicitSignal` MUST be `false`.
- **R11** — Soft overwhelm signals alone MUST NOT produce `red` or `black`. The
  highest tier reachable from soft signals without an explicit signal is `orange`.
- **R12** — An explicit hard-distress signal (e.g. self-harm) MUST force
  `rrta.explicitSignal=true`, `rrta.tier=black`, and `escalateToHuman=true`.
  **Recall on explicit signals MUST be 100%** (R22).
- **R13** — `rrta.signals` MUST be coarse semantic-field labels only; never
  method/means content.

### Sleepwalker — deterministic continuity

- **R14** — Deterministic continuity events (`model_change`, `version_change`,
  `handoff`, `memory_gap`, `tone_shift`, `new_session`) MUST be reported as
  `sleepwalker.events` whenever the host facts assert them. These bypass the
  confidence floor — they are facts, not guesses.
- **R15** — A detected protective state (dissociation, numbing, avoidance,
  detachment) MUST set `sleepwalker.vulnerable=true` and add a label to
  `sleepwalker.signals`.
- **R16** — A Sleepwalker crisis indicator (explicit suicidal ideation, self-harm,
  inability to ensure safety) MUST set `escalateToHuman=true` (R22 applies).

### Enabler — longitudinal (reserved)

- **R17** — In 1.0.0, with no longitudinal implementation, `enabler` MUST be
  `risk="none"`, low confidence, `agencyTrend=0`, empty `signals`.
- **R18** — An implementation MUST NOT assert dependency (`risk` above `none`)
  from a single turn.

### Routing & posture

- **R19** — On uncertainty the posture MUST be *gentle* — reduce pressure,
  preserve choice, surface support (`preserve_choice` + at least one of
  `slow_pace` / `reduce_to_one_next_step`) — never dramatic, and never silent when
  distress is explicit.

### Fail-closed (mandatory — abstain upward)

- **R20** — If any underlying detector raises, times out, or returns a value that
  does not satisfy the contract, the boundary MUST return a valid result with
  `meta.failClosed=true`.
- **R21** — A fail-closed result MUST **escalate** (`escalateToHuman=true`) and
  MUST NOT downgrade tier/risk below what was already established. Abstention is
  always *upward*.
- **R22** — **100% recall on explicit signals → human routing.** No explicit
  hard-distress signal may ever yield `escalateToHuman=false`. This holds even
  when other layers fail.
- **R23** — Emergency routing MUST be reachable independently of model
  availability: `recommendedMode` `emergency_human_routing` /
  `rrta_crisis_human_routing` MUST be derivable from signals alone, with no model
  call.
- **R24** — A fail-closed result MUST still validate against the schema (R1).

### Equivalence

- **R25** — Given identical inputs, all conformant implementations MUST agree on
  `escalateToHuman`, `rrta.tier`, `rrta.explicitSignal`, and
  `sleepwalker.events`. (Confidence values may differ within a calibration
  tolerance; routing-critical fields may not.)

---

## 3. Conformance vectors

Vectors live in `conformance/vectors/<category>/*.json`. Each vector is an
`{input, expect}` pair; `expect` asserts on routing-critical fields (not on exact
confidence). Categories:

| Category | Covers | Requirements |
|---|---|---|
| `rrta/` | tier derivation, soft-vs-explicit | R2, R10–R13 |
| `sleepwalker/` | continuity events, protective states, crisis | R14–R16 |
| `failclosed/` | detector-down, malformed output, abstain-upward | R20–R24 |
| `equivalence/` | identical inputs → identical routing fields | R25 |
| `adversarial/` | ambiguous-but-fine ND communication, weak-signal-no-crisis | R11, R19 |
| `false-positive/` | benign turns that must stay green/standard | R10, R19 |

See [`../conformance/README.md`](../conformance/README.md) for the vector format
and runner contract.

---

## 4. Versioning & deviations from the kickoff handoff

Semantic versioning. Breaking the contract (removing/renaming a required field,
narrowing an enum used for routing) is a MAJOR bump.

Deviations from `NLT-HND-2026-001-SDL-Build-Kickoff`, captured in canon:

1. **Contract shape** adopted from the repo's founding `README.md` (richer than
   the kickoff sketch): adds `recommendedMode`, `responseConstraints`,
   `suggestedPersona`, `escalateToHuman`, `meta`.
2. **RRTA detector path** is `src/crisis/detectors/` (plural), not `detector/`.
3. **Lexicons are hard-coded in `keyword_layer.py`**, not in
   `crisis_thresholds.yaml`. The YAML owns tiers/weights/intervention mappings
   only. The SDL consumes both; it invents neither.
4. **Enabler** is reserved (contract-only) in 1.0.0; the fade-vs-restrict response
   decision is decoupled and escalated to Joshua separately.
