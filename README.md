# State Detection Layer — WIP v0.1

A conservative, rules-based state detector for the Solidarity Framework. One
interface, three detectors (RRTA / Sleepwalker / Enabler). Built to be dropped
into your Cloudflare agent and tested — **not** to ship to real users yet.

---

## This repo is a spec, not a single codebase

The SDL is defined as a **language-agnostic specification** + a **conformance
suite** + one or more **conformant reference implementations**. Any
implementation, in any language, is "SDL-conformant" iff it passes the
conformance suite.

| Part | Where | What |
|---|---|---|
| **Spec** | [`spec/nlt-sdl-spec.md`](spec/nlt-sdl-spec.md) · [`spec/detection-result.schema.json`](spec/detection-result.schema.json) | `NLT-SPEC-SDL-1.0.0`: the `DetectionResult` contract + requirements `R1..R25` |
| **Conformance suite** | [`conformance/`](conformance/README.md) | The safety gate. Every requirement ≥1 vector; fail-closed vectors mandatory |
| **Python reference** | [`reference/python/nlt_sdl/`](reference/python/nlt_sdl) | Conformant impl that **wraps** the canonical rrt-advocate + sleepwalker detectors behind the contract, with a fail-closed boundary |

```bash
python conformance/runner/conformance.py --impl python   # the safety gate
python -m pytest reference/python/tests -q                # policy + fail-closed unit tests
```

> **Certified on calibration / fail-closed / recall / equivalence — not
> "accuracy."** Coarse crisis detection → human routing. **Not** a clinical or
> diagnostic tool.

The TypeScript files below are the **planned host-agnostic implementation** (a
future conformant impl that must pass the same suite, R25). They describe the
contract shape this repo's spec now formalizes.

---

## Planned TypeScript implementation

- `state-detector.ts` — the detector. Host-agnostic, zero deps, fail-closed.
- `detector-agent.ts` — thin Cloudflare Agents-SDK wrapper (one DO per user).

## What it emits (the contract)

Every turn returns a `DetectionResult`:

```jsonc
{
  "rrta":        { "tier": "orange", "confidence": 0.59, "signals": ["overwhelm","task_paralysis"] },
  "sleepwalker": { "vulnerable": false, "events": [], "signals": [] },
  "enabler":     { "risk": "none", "confidence": 0.3, "agencyTrend": 0, "signals": [] },
  "recommendedMode": "rrta_soft_scaffold",
  "responseConstraints": ["reduce_to_one_next_step","no_large_lists","preserve_choice","avoid_shame_language"],
  "suggestedPersona": "kai",
  "escalateToHuman": false,
  "meta": { "failClosed": false, "notes": [] }
}
```

Your response router consumes `recommendedMode` + `responseConstraints` (and
`suggestedPersona`) when assembling the model call.

## The three shapes (why it's not one classifier)

- **Sleepwalker — deterministic.** Fires off *facts* the agent already knows:
  model/version change, handoff, memory gap (time since last turn), tone shift.
  The wrapper derives these by diffing `model`/`tone`/timestamp against stored
  state. Bypasses the confidence floor — these aren't guesses.
- **RRTA — acute, in-session.** Soft signal groups → graduated yellow/orange.
  Red/black require an **explicit** hard-distress signal; never inferred from
  soft overwhelm. Conservative by design.
- **Enabler — longitudinal.** Reads cross-session counters as a *trend*. Reports
  low confidence until it's watched `minSessionsForConfidence` sessions. Never
  labels dependency from a single message.

## Drop it in

In `detector-agent.ts` the Agent is a Durable Object per user. Call `observe(...)`
each turn **before** you call the model:

```ts
import { getAgentByName } from "agents";
const agent = await getAgentByName(env.StateDetectorAgent, userId);
const detection = await agent.observe({
  message: userMessage,
  model: currentModelId,   // diff vs last => model_change
  tone: currentToneId,     // diff vs last => tone_shift
  newSession: isNewSession,
  humanResourceReachable: true,
  toi: usersToiSupportPrefs,
});
// feed detection.recommendedMode + detection.responseConstraints into your router
```

`wrangler.jsonc`:

```jsonc
{
  "compatibility_flags": ["nodejs_compat"],
  "durable_objects": {
    "bindings": [{ "name": "StateDetectorAgent", "class_name": "StateDetectorAgent" }]
  },
  "migrations": [{ "tag": "v1", "new_sqlite_classes": ["StateDetectorAgent"] }]
}
```

(Do **not** enable `experimentalDecorators` in tsconfig — it breaks `@callable`.)

Run the detector demo standalone: `npx -y tsx state-detector.ts`

## The knobs

- `CONFIG` in `state-detector.ts` — confidence floor, RRTA signal weights/cutoffs,
  Enabler session/drift thresholds. In canon these live in
  `config/crisis_thresholds.yaml`.
- The signal lexicons (`SOFT_SIGNALS`, `HARD_DISTRESS_SIGNALS`, `ATTACHMENT_SIGNALS`)
  and the drift-phrase lists in the agent — coarse and tunable.
- **TODO knob:** counters accumulate with no decay yet. Add per-session decay so
  old behavior ages out of the trend window.

## Safety invariants (deliberate — loosen only with eval evidence)

1. Defaults to green/standard; asserts nothing below the confidence floor.
2. Crisis tier requires an explicit signal — never inferred from soft overwhelm.
3. On uncertainty the posture is *gentle* (reduce pressure, preserve choice,
   surface support) — never dramatic, never silent when distress is explicit.
4. The crisis path **surfaces human support and escalates**. It is a routing net,
   **not** clinical assessment and **not** a substitute for real crisis services.
   It contains no method/means language by design.
5. Longitudinal state holds counts/trends only — no message content.

## Notes before this leaves WIP

- **Reconcile against canon:** the RRTA lexicons and tier cutoffs here are my
  coarse starting point — map them to `config/crisis_thresholds.yaml` and the
  canonical tier definitions (green/yellow/orange/red/black). Same for the
  persona→mode mapping (Ash/Sol/Echo/Kai/Myra).
- **Decoupled from fade-vs-restrict:** the detector only emits `enabler.risk`.
  The fade-vs-restrict choice governs the *response* ladder downstream, not the
  detector — so that decision doesn't block this.
- **The real accuracy ceiling:** a rules engine is the right WIP, but it can't be
  *accurate* about internal state. Stronger detection is the clinician/eval-data
  track (mPACT-style ground truth), not a code change. Swap `detectRRTA` for a
  calibrated classifier behind the same interface when that data exists.
- **Validation gate:** before real users, this needs adversarial fail-closed
  tests (detector-down, ambiguous-but-fine ND communication, weak-signal-no-crisis)
  and a measured false-positive rate. Do not stub those green.
