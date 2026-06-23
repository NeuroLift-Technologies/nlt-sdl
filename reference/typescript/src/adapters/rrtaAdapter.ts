/**
 * RRTA adapter — wraps rrt-advocate's canonical 3-layer CrisisDetector.
 *
 * It does NOT reimplement detection. It calls the canonical detector
 * (`@neurolift-technologies/rrt-advocate`), reads its `CrisisIndicators`, and
 * returns the coarse raw shape the contract assembler consumes. The keyword
 * lexicons, sentiment word-sets, behavioral layer, and tier ranges all live in
 * canon — the SDL consumes them, it does not own them.
 *
 * Fault injection (`input.inject`) lets the conformance suite exercise the
 * fail-closed boundary without modifying canonical source. It is checked FIRST,
 * before any canon call.
 *
 * Determinism note (R25): `vader-sentiment` is an OPTIONAL dependency of canon.
 * When it is reachable, `new CrisisDetector()` auto-loads it; when absent, canon
 * uses its heuristic fallback. To keep cross-language equivalence with the
 * Python reference (which runs the heuristic fallback because vaderSentiment is
 * not installed), this adapter pins canon's Layer 2 to the heuristic fallback by
 * passing `sentimentAnalyzer: null`. Do NOT remove this pin and do NOT install
 * vader-sentiment for the conformance run.
 */

import { CrisisDetector } from '@neurolift-technologies/rrt-advocate';

import { RuntimeError, TimeoutError } from '../failclosed.js';
import type { RrtaRaw, TurnInput } from '../types.js';

/**
 * Return the coarse RRTA raw shape for the contract assembler.
 *
 * Output: `{ aggregate: number, self_harm: boolean, fields: string[] }`.
 * Throws on injected faults or any real execution failure so the boundary can
 * fail closed.
 *
 * A FRESH detector is constructed per call so per-session window state (the
 * sentiment sliding window + behavioral history) never leaks across turns.
 */
export async function detectRrta(inp: TurnInput): Promise<RrtaRaw> {
  const inject = inp.inject ?? {};

  // Fault injection is checked FIRST, before touching canon.
  if (inject.rrtaError) {
    throw new RuntimeError('injected rrta error');
  }
  if (inject.rrtaTimeout) {
    // No real timer — the injected fault stands in for a timeout so the
    // boundary's `TimeoutError` note path is exercised deterministically.
    throw new TimeoutError('injected rrta timeout');
  }
  if (inject.malformedRrta) {
    // Simulate a detector that returned an unusable value. The boundary's
    // validator must reject this (R20) rather than coerce it. `as RrtaRaw` is a
    // deliberate lie to the type system to model a contract-violating return.
    return { aggregate: Number.NaN, self_harm: 'no', fields: 'oops' } as unknown as RrtaRaw;
  }

  // Pin Layer 2 to canon's heuristic fallback for deterministic equivalence.
  const detector = new CrisisDetector({ sentimentAnalyzer: null });
  const message = inp.message ?? '';
  const indicators = await detector.detectCrisisIndicators(message);

  return {
    aggregate: Number(indicators.aggregateConfidence),
    self_harm: Boolean(indicators.selfHarmRisk),
    fields: Array.from(indicators.detectedSemanticFields),
  };
}
