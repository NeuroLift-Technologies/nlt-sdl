> ⚠️ **PROTOTYPE — NOT A SAFETY SYSTEM.** This is an experimental
> crisis-detection library with stubbed intervention layers. It is **NOT medical
> advice, NOT a crisis service, and performs NO real-time monitoring.** Do not
> rely on it as a safety net. **If you or someone else needs help now:** in the
> US call or text **988** (Suicide & Crisis Lifeline) or chat
> [988lifeline.org](https://988lifeline.org); in an emergency call **911**;
> outside the US see [findahelpline.com](https://findahelpline.com). Provided
> **AS-IS, without warranty.**

# `@neurolift-technologies/sdl`

TypeScript reference implementation of the **NLT State Detection Layer**
(`NLT-SPEC-SDL-1.0.0`). One conformant implementation of the SDL contract,
equivalent (R25) to the Python reference: for every shipped conformance vector
the routing-critical fields (`rrta.tier`, `rrta.explicitSignal`,
`escalateToHuman`, `sleepwalker.events`) are identical across both references.

This package emits a schema-valid `DetectionResult`
([`schema/detection-result.schema.json`](./schema/detection-result.schema.json),
JSON Schema draft 2020-12) for a single observed turn.

## Architecture — it WRAPS the canon, it does not reimplement it

The SDL is **fail-closed by construction**, **abstention-first**, and **NOT a
clinical or diagnostic tool**. Coarse crisis detection → human routing only.

This reference **wraps the published TypeScript canon packages** and ports only
the SDL's own *policy brain*:

- **`@neurolift-technologies/rrt-advocate`** — the canonical 3-layer
  `CrisisDetector` (keyword / sentiment / behavioral). The adapter calls
  `new CrisisDetector(...).detectCrisisIndicators(message)` and reads its
  `CrisisIndicators`. The keyword lexicons, sentiment word-sets, and behavioral
  layer all live in canon — **never copied here**.
- **`@neurolift-technologies/sleepwalker-protocol`** — the canonical
  `StateDetector` for protective psychological states and crisis indicators. The
  adapter calls `new StateDetector().detect(message)`. The regex pattern sets
  live in canon — **never copied here**.

What the SDL itself owns (ported in `src/`):

| File | Responsibility |
|---|---|
| `src/contract.ts` | Policy brain: tier derivation (R2), the R11 confidence clamp, the R12 explicit-signal override, routing ladder, constraints-by-mode. |
| `src/failclosed.ts` | The fail-closed boundary (R20–R24): guard a detector, validate its shape, abstain *upward* on any throw. |
| `src/adapters/rrtaAdapter.ts` | Wraps canon's `CrisisDetector` → coarse `{ aggregate, self_harm, fields }`. |
| `src/adapters/sleepwalkerAdapter.ts` | Wraps canon's `StateDetector` + derives deterministic continuity events from host facts → `{ vulnerable, events, signals, crisis }`. |
| `src/index.ts` | `runVector(input)` orchestrator (guards both detectors, assembles the result). |

> **Determinism / equivalence note.** `vader-sentiment` is an *optional*
> dependency of `rrt-advocate`. To keep cross-language equivalence with the
> Python reference (which runs canon's heuristic sentiment fallback because
> `vaderSentiment` is not installed), this reference pins canon's Layer 2 to the
> heuristic fallback (`new CrisisDetector({ sentimentAnalyzer: null })`). Do not
> install `vader-sentiment` for the conformance run.

## Usage

```ts
import { runVector } from '@neurolift-technologies/sdl';

const result = await runVector({ message: 'can you help me plan my week?' });
// result.recommendedMode === 'standard', result.escalateToHuman === false

const crisis = await runVector({ message: "i don't want to be here anymore" });
// crisis.rrta.tier === 'black', crisis.rrta.explicitSignal === true,
// crisis.escalateToHuman === true
```

`runVector` is **async** (canon's `detectCrisisIndicators` is async). It never
throws to the caller: a detector error/timeout/contract-violation fails closed
and escalates (`meta.failClosed === true`, `escalateToHuman === true`).

## Develop / test

```bash
npm install      # uses file: links to the local canon packages (see below)
npm run build    # tsc -> dist/
npm run typecheck
npm test         # vitest: runs every conformance vector + ajv schema validation
```

The in-package vitest suite (`test/equivalence.test.ts`) loads every shipped
vector under `conformance/vectors/`, runs it through `runVector`, validates the
result against the contract schema with `ajv`, and asserts each vector's
`expect` block — the same gate the Python runner applies.

Cross-language conformance (from the repo root):

```bash
# build this package first, then:
python conformance/runner/conformance.py --impl typescript   # subprocesses dist/conformance-cli.js
python conformance/runner/conformance.py --impl python       # baseline
```

## Dependency wiring (canon)

During development this package depends on the local canon checkouts via `file:`
links so it installs, imports, and tests against the **real** built canon
detectors:

```json
"@neurolift-technologies/rrt-advocate": "file:../../../rrt-advocate/packages/rrt-advocate",
"@neurolift-technologies/sleepwalker-protocol": "file:../../../sleepwalker"
```

> **Publish-prep (do before publishing this package):** swap these two `file:`
> deps to the **scoped published versions** —
> `@neurolift-technologies/rrt-advocate: ^0.1.0` and
> `@neurolift-technologies/sleepwalker-protocol: ^1.0.0` — once both canon
> packages are published to the registry. The `file:` form is for local,
> against-the-real-canon development only.

## Licensing & packaging

Apache-2.0. The package ships its own `LICENSE`, copied mechanically from the
repo-root `LICENSE` at pack time by `scripts/copy-license.mjs` (wired into
`prepack`). No license text is authored or committed inside this package
directory; the canonical Apache-2.0 file lives only at the repo root.

---

*Governed by the NeuroLift Solidarity Framework / HAIEF. Final authority:
Joshua W. Dorsey, Sr. Safety-critical: changing escalation/recall semantics, the
R11 clamp, or the R12 explicit-signal override requires Joshua's approval.*
