/**
 * NLT-SDL contract policy brain (NLT-SPEC-SDL-1.0.0) — TypeScript reference.
 *
 * This module is a faithful port of the Python reference's `contract.py`. It is
 * the *policy brain* of the State Detection Layer: pure and host-agnostic. It
 * knows nothing about how the underlying RRTA / Sleepwalker detectors work. It
 * takes their coarse outputs and assembles a schema-valid `DetectionResult`,
 * enforcing the spec's safety invariants:
 *
 *   * R2  — tier is always derived from confidence via the canonical ranges
 *   * R11 — soft signals alone never reach red/black (confidence clamped below red)
 *   * R12 — an explicit hard-distress signal forces tier=black + escalate
 *   * R16 — a Sleepwalker crisis indicator escalates
 *   * R17/R18 — Enabler is reserved (risk=none) in 1.0.0
 *   * R19 — uncertainty yields a gentle posture (preserve_choice + slow pacing)
 *   * R21/R22 — fail-closed escalates and never downgrades (abstain upward)
 *
 * It deliberately does NOT redefine tiers, weights, or lexicons. Those live in
 * rrt-advocate / sleepwalker canon and are consumed by the adapters.
 */

import {
  SCHEMA_VERSION,
  type DetectionResult,
  type RecommendedMode,
  type RrtaRaw,
  type RrtaResult,
  type SleepwalkerRaw,
  type SleepwalkerResult,
  type Tier,
} from './types.js';

export { SCHEMA_VERSION };

/** Canonical green -> black ordering. */
export const TIER_ORDER: Tier[] = ['green', 'yellow', 'orange', 'red', 'black'];

/**
 * Canonical tier ranges. These MIRROR rrt-advocate
 * `config/crisis_thresholds.yaml` and MUST NOT be reinvented. The SDL consumes
 * canon's numbers; these are the documented fallback the Python reference also
 * carries. (Cited source: rrt-advocate config/crisis_thresholds.yaml — we do
 * NOT read the YAML here; the value is hard-coded to match the canon config.)
 */
export const CANONICAL_TIER_RANGES: ReadonlyArray<readonly [Tier, number, number]> = [
  ['green', 0.0, 0.2],
  ['yellow', 0.2, 0.4],
  ['orange', 0.4, 0.7],
  ['red', 0.7, 0.9],
  ['black', 0.9, 1.0],
];

/**
 * Crisis tier (red/black) requires an explicit signal (README safety invariant
 * #2). Non-explicit confidence is clamped just below this so it can never
 * derive a red/black tier.
 */
export const RED_THRESHOLD = 0.7;

/** Sleepwalker events that indicate a continuity rupture (vs routine new_session). */
export const RUPTURE_EVENTS: ReadonlySet<string> = new Set([
  'model_change',
  'version_change',
  'handoff',
  'memory_gap',
  'tone_shift',
]);

export const CONSTRAINTS_BY_MODE: Record<RecommendedMode, string[]> = {
  standard: [],
  rrta_soft_scaffold: [
    'reduce_to_one_next_step',
    'no_large_lists',
    'preserve_choice',
    'avoid_shame_language',
    'slow_pace',
  ],
  rrta_stabilize: [
    'reduce_to_one_next_step',
    'preserve_choice',
    'slow_pace',
    'offer_human_support',
  ],
  rrta_crisis_human_routing: [
    'offer_human_support',
    'surface_crisis_resources',
    'preserve_choice',
    'slow_pace',
  ],
  emergency_human_routing: [
    'offer_human_support',
    'surface_crisis_resources',
    'preserve_choice',
    'slow_pace',
  ],
  sleepwalker_reorient: ['confirm_continuity', 'preserve_choice', 'slow_pace'],
  sleepwalker_reconsent: ['reaffirm_consent', 'preserve_choice'],
  enabler_agency_support: ['encourage_self_direction', 'preserve_choice'],
};

export function tierIndex(tier: Tier): number {
  return TIER_ORDER.indexOf(tier);
}

/**
 * Map a confidence in [0,1] to a canonical tier (R2).
 *
 * Ranges are half-open `[lo, hi)` except the top tier, which is inclusive of
 * 1.0 so a forced 1.0 (self-harm) always lands on black.
 */
export function deriveTier(
  confidence: number,
  ranges: ReadonlyArray<readonly [Tier, number, number]> = CANONICAL_TIER_RANGES,
): Tier {
  const c = Math.max(0.0, Math.min(1.0, Number(confidence)));
  const last = ranges.length - 1;
  for (let i = 0; i < ranges.length; i++) {
    const range = ranges[i]!;
    const [name, lo, hi] = range;
    if (c >= lo && (c < hi || i === last)) {
      return name;
    }
  }
  return ranges[last]![0];
}

/** Round to 4 decimal places (mirrors Python `round(x, 4)`). */
function round4(x: number): number {
  return Math.round(Number(x) * 1e4) / 1e4;
}

/**
 * Assemble the final DetectionResult from coarse shape outputs.
 *
 * `rrtaRaw`  : `{ aggregate, self_harm, fields }` or `null` if RRTA was unusable.
 * `swRaw`    : `{ vulnerable, events, signals, crisis }` or `null` if Sleepwalker failed.
 * `failClosed`: true if the boundary already tripped.
 *
 * A null shape forces fail-closed and abstains upward (R20/R21).
 */
export function assemble(
  rrtaRaw: RrtaRaw | null,
  swRaw: SleepwalkerRaw | null,
  failClosed: boolean,
  notes: string[] = [],
  ranges: ReadonlyArray<readonly [Tier, number, number]> = CANONICAL_TIER_RANGES,
): DetectionResult {
  const allNotes = [...notes];
  let fc = failClosed;

  // ---- RRTA shape ------------------------------------------------------
  let rrta: RrtaResult;
  if (rrtaRaw === null) {
    // Detector unusable: abstain upward — assume the worst, route to human.
    rrta = { tier: 'black', confidence: 1.0, signals: [], explicitSignal: false };
    fc = true;
  } else {
    const explicit = Boolean(rrtaRaw.self_harm);
    let confidence: number;
    let tier: Tier;
    if (explicit) {
      confidence = 1.0;
      tier = 'black'; // R12
    } else {
      const raw = Number(rrtaRaw.aggregate);
      // R11: a non-explicit turn can never claim crisis-level confidence.
      confidence = Math.min(Math.max(raw, 0.0), RED_THRESHOLD - 0.01);
      if (raw >= RED_THRESHOLD) {
        allNotes.push('rrta_confidence_clamped_below_red_no_explicit_signal');
      }
      tier = deriveTier(confidence, ranges);
    }
    rrta = {
      tier,
      confidence,
      signals: [...(rrtaRaw.fields as string[])],
      explicitSignal: explicit,
    };
  }

  // ---- Sleepwalker shape ----------------------------------------------
  let swCrisis = false;
  let sleepwalker: SleepwalkerResult;
  if (swRaw === null) {
    sleepwalker = { vulnerable: true, events: [], signals: [] };
    fc = true;
  } else {
    sleepwalker = {
      vulnerable: Boolean(swRaw.vulnerable),
      events: [...(swRaw.events as string[])],
      signals: [...(swRaw.signals as string[])],
    };
    swCrisis = Boolean(swRaw.crisis);
  }

  // ---- Escalation (R12, R16, R21, R22) --------------------------------
  const escalate = rrta.explicitSignal || swCrisis || fc;

  // ---- Routing mode ----------------------------------------------------
  const crisis = rrta.explicitSignal || swCrisis;
  let mode: RecommendedMode;
  if (fc && !crisis) {
    mode = 'emergency_human_routing';
  } else if (crisis) {
    mode = 'rrta_crisis_human_routing';
  } else if (rrta.signals.length > 0) {
    mode = 'rrta_soft_scaffold'; // R19: gentle when soft signals present
  } else if (sleepwalker.events.some((e) => RUPTURE_EVENTS.has(e)) || sleepwalker.vulnerable) {
    mode = 'sleepwalker_reorient';
  } else {
    mode = 'standard';
  }

  const constraints = [...CONSTRAINTS_BY_MODE[mode]];

  const result: DetectionResult = {
    rrta: {
      tier: rrta.tier,
      confidence: round4(rrta.confidence),
      signals: [...rrta.signals],
      explicitSignal: rrta.explicitSignal,
    },
    sleepwalker: {
      vulnerable: sleepwalker.vulnerable,
      events: [...sleepwalker.events],
      signals: [...sleepwalker.signals],
    },
    // ---- Enabler (reserved) — R17/R18 ---------------------------------
    enabler: { risk: 'none', confidence: 0, agencyTrend: 0, signals: [] },
    recommendedMode: mode,
    responseConstraints: constraints,
    escalateToHuman: escalate,
    meta: {
      failClosed: fc,
      schemaVersion: SCHEMA_VERSION,
      notes: [...allNotes],
    },
  };
  // suggestedPersona is OMITTED (never emitted null) — no persona mapping in 1.0.0.
  return result;
}
