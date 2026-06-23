/**
 * NLT-SDL TypeScript reference implementation (NLT-SPEC-SDL-1.0.0).
 *
 * ⚠️ PROTOTYPE — NOT A SAFETY SYSTEM. See README.md. Experimental
 * crisis-detection with stubbed intervention layers; NOT medical advice, NOT a
 * crisis service, NO real-time monitoring. If you need help now: in the US call
 * or text 988, or in an emergency call 911; outside the US see findahelpline.com.
 *
 * One conformant implementation of the State Detection Layer. It WRAPS the
 * published TypeScript canon packages (`@neurolift-technologies/rrt-advocate`
 * and `@neurolift-technologies/sleepwalker-protocol`) behind the SDL contract
 * and guards them with the fail-closed boundary. It ports only the SDL's OWN
 * policy brain (tier derivation, the R11 clamp, the R12 override, routing, and
 * the fail-closed boundary) — never canon's lexicons, sentiment word-sets,
 * behavioral layer, or StateDetector patterns.
 *
 * Conformance entrypoint: `runVector(input) -> DetectionResult` returns a
 * schema-valid result for a single observed turn (R25-equivalent to the Python
 * reference's `run_vector`).
 */

import { assemble, SCHEMA_VERSION } from './contract.js';
import { detectRrta } from './adapters/rrtaAdapter.js';
import { detectSleepwalker } from './adapters/sleepwalkerAdapter.js';
import {
  guarded,
  validateRrtaRaw,
  validateSleepwalkerRaw,
} from './failclosed.js';
import type { DetectionResult, TurnInput } from './types.js';

export { SCHEMA_VERSION };
export type {
  DetectionResult,
  TurnInput,
  RrtaResult,
  SleepwalkerResult,
  EnablerResult,
  Meta,
  Tier,
  RecommendedMode,
  ResponseConstraint,
} from './types.js';
export { assemble, deriveTier, CANONICAL_TIER_RANGES, RUPTURE_EVENTS } from './contract.js';

/**
 * Run one turn through the SDL and return a schema-valid result.
 *
 * Each shape detector runs behind the fail-closed boundary. If either fails,
 * the result is marked `meta.failClosed` and escalates (abstain upward).
 * Routing-critical guarantees hold even when a detector is down:
 *   * an explicit RRTA signal still escalates even if Sleepwalker fails (R22)
 *   * a total outage still escalates via emergency_human_routing (R22/R23)
 */
export async function runVector(inp: TurnInput): Promise<DetectionResult> {
  const input = (inp ?? {}) as Record<string, unknown>;

  const rrtaOutcome = await guarded('rrta', detectRrta, input, validateRrtaRaw);
  const swOutcome = await guarded('sleepwalker', detectSleepwalker, input, validateSleepwalkerRaw);

  const notes: string[] = [];
  for (const outcome of [rrtaOutcome, swOutcome]) {
    if (outcome.note) {
      notes.push(outcome.note);
    }
  }

  const failClosed = rrtaOutcome.failed || swOutcome.failed;

  return assemble(rrtaOutcome.value, swOutcome.value, failClosed, notes);
}

/** Host-friendly wrapper: `observe({ message, model, ... })`. */
export function observe(input: TurnInput): Promise<DetectionResult> {
  return runVector(input);
}
