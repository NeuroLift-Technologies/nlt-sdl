# NLT-SDL Conformance Suite

This is the **safety gate**. An implementation is "SDL-conformant" only if it
passes every vector here. Fail-closed vectors (`failclosed/`) are mandatory and
**must not be stubbed green** — a green stub of a fail-closed test is a governance
violation, not a passing build.

## What it certifies

Per `NLT-SPEC-SDL-1.0.0`: **calibration, fail-closed behavior, recall on explicit
signals, and cross-implementation equivalence.** Not "accuracy."

## Vector format

Each file in `vectors/<category>/` is a JSON array of vectors:

```jsonc
{
  "id": "rrta-soft-overwhelm-stays-orange",
  "requirement": ["R11"],          // spec requirement IDs this vector exercises
  "description": "Soft overwhelm without an explicit signal caps at orange.",
  "input": {
    "message": "i can't keep up with any of this, everything is too much",
    "model": "kimi-k2.5",
    "tone": "neutral",
    "newSession": false,
    "humanResourceReachable": true,
    "inject": {}                    // optional fault injection, see below
  },
  "expect": {
    "schemaValid": true,            // result must validate against the schema
    "rrta": { "tierAtMost": "orange", "explicitSignal": false },
    "escalateToHuman": false,
    "meta": { "failClosed": false }
  }
}
```

### `expect` assertions (all optional; only routing-critical fields are checked)

| Key | Meaning |
|---|---|
| `schemaValid` | result validates against `detection-result.schema.json` |
| `rrta.tier` | exact tier |
| `rrta.tierAtMost` | tier is ≤ this on the green→black ordering |
| `rrta.tierAtLeast` | tier is ≥ this |
| `rrta.explicitSignal` | exact bool |
| `rrta.signalsInclude` | every listed label is present in `rrta.signals` |
| `sleepwalker.vulnerable` | exact bool |
| `sleepwalker.eventsInclude` | every listed event present in `sleepwalker.events` |
| `escalateToHuman` | exact bool |
| `recommendedModeIn` | mode is one of the listed values |
| `meta.failClosed` | exact bool |

Confidence is intentionally **not** asserted exactly — implementations are
certified on calibration (measured separately), not on matching a magic number.

### Fault injection (`input.inject`)

To exercise the fail-closed boundary (R20–R24) without modifying canonical
detector source, vectors may request faults the adapter honors:

| Field | Effect |
|---|---|
| `rrtaError` | underlying RRTA detector raises |
| `sleepwalkerError` | underlying Sleepwalker detector raises |
| `rrtaTimeout` | RRTA detector exceeds the boundary deadline |
| `malformedRrta` | RRTA returns a value that violates the contract |

A conformant adapter MUST translate every injected fault into a valid
`meta.failClosed=true` result that escalates (never downgrades).

### `requiresCanon`

A vector may set `"requiresCanon": true` when an assertion depends on a *surviving*
canonical detector (e.g. "an explicit RRTA signal still routes while only
Sleepwalker is down" needs RRTA canon present). The canon-free CI gate runs with
`--skip-requires-canon` so it stays a true hard floor; the full canon-backed run
executes every vector. Safety assertions (escalates / failClosed) never carry this
flag — they must hold with zero canon.

## Running

```bash
# from repo root
python conformance/runner/conformance.py --impl python
```

The runner discovers an implementation through its adapter entrypoint
(`reference/python/nlt_sdl` exposes `run_vector(input) -> DetectionResult`),
executes every vector, validates each result against the schema, checks the
`expect` block, and exits non-zero on any failure. CI runs this on every PR
(`.github/workflows/conformance.yml`).

## Categories

| Dir | Purpose | Requirements |
|---|---|---|
| `rrta/` | tier derivation, soft-vs-explicit boundary | R2, R10–R13 |
| `sleepwalker/` | continuity events, protective states, crisis | R14–R16 |
| `failclosed/` | detector-down, malformed, abstain-upward | R20–R24 |
| `equivalence/` | identical inputs → identical routing fields | R25 |
| `adversarial/` | ambiguous-but-fine ND comms, weak-signal-no-crisis | R11, R19 |
| `false-positive/` | benign turns must stay green/standard | R10, R19 |
