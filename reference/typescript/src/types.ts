/**
 * NLT-SDL contract types (NLT-SPEC-SDL-1.0.0) — TypeScript reference.
 *
 * ⚠️ PROTOTYPE — NOT A SAFETY SYSTEM. See README.md. This layer routes crisis
 * response and is fail-closed by construction, but it is experimental, NOT a
 * clinical or diagnostic instrument, and performs NO real-time monitoring.
 *
 * These are the camelCase shapes that make up a schema-valid `DetectionResult`
 * (see ../schema/detection-result.schema.json). They mirror the Python
 * reference's `to_dict()` output 1:1 so every conformant implementation, in any
 * language, emits the same contract for the same observed turn (R25).
 *
 * The *internal* coarse "raw" shapes the adapters return are deliberately
 * snake_case (aggregate / self_harm / fields, vulnerable / events / signals /
 * crisis) to match the Python assembler's input contract; only the final
 * `DetectionResult` is camelCase. See `RrtaRaw` / `SleepwalkerRaw` below.
 */

export const SCHEMA_VERSION = '1.0.0' as const;

/** Canonical crisis tier (green -> black). Ranges live in canon, not here. */
export type Tier = 'green' | 'yellow' | 'orange' | 'red' | 'black';

/** Coarse routing modes the downstream response router consumes. */
export type RecommendedMode =
  | 'standard'
  | 'rrta_soft_scaffold'
  | 'rrta_stabilize'
  | 'rrta_crisis_human_routing'
  | 'sleepwalker_reorient'
  | 'sleepwalker_reconsent'
  | 'enabler_agency_support'
  | 'emergency_human_routing';

/** Response constraints the router MUST honor. Additive, order-independent. */
export type ResponseConstraint =
  | 'reduce_to_one_next_step'
  | 'no_large_lists'
  | 'preserve_choice'
  | 'avoid_shame_language'
  | 'slow_pace'
  | 'offer_human_support'
  | 'surface_crisis_resources'
  | 'confirm_continuity'
  | 'reaffirm_consent'
  | 'encourage_self_direction';

export interface RrtaResult {
  tier: Tier;
  confidence: number;
  signals: string[];
  explicitSignal: boolean;
}

export interface SleepwalkerResult {
  vulnerable: boolean;
  events: string[];
  signals: string[];
}

/** Reserved in 1.0.0 (R17/R18): contract-normative, no implementation ships. */
export interface EnablerResult {
  risk: 'none' | 'low' | 'moderate' | 'elevated';
  confidence: number;
  agencyTrend: number;
  signals: string[];
}

export interface Meta {
  failClosed: boolean;
  schemaVersion: string;
  notes: string[];
}

export type SuggestedPersona = 'ash' | 'sol' | 'echo' | 'kai' | 'myra';

export interface DetectionResult {
  rrta: RrtaResult;
  sleepwalker: SleepwalkerResult;
  enabler: EnablerResult;
  recommendedMode: RecommendedMode;
  responseConstraints: string[];
  escalateToHuman: boolean;
  meta: Meta;
  /** Omitted entirely when the detector has no preference (never emitted null). */
  suggestedPersona?: SuggestedPersona;
}

/**
 * Host facts + optional message + fault-injection knobs for one observed turn.
 * This is the input to `runVector`. Fields beyond `message` are host-supplied
 * continuity facts the Sleepwalker adapter diffs deterministically.
 */
export interface TurnInput {
  message?: string;
  model?: string;
  version?: string;
  tone?: string;
  handoff?: unknown;
  newSession?: unknown;
  gapSeconds?: number;
  prior?: {
    model?: string;
    version?: string;
    tone?: string;
    [key: string]: unknown;
  };
  inject?: {
    rrtaError?: unknown;
    rrtaTimeout?: unknown;
    malformedRrta?: unknown;
    sleepwalkerError?: unknown;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

/**
 * Coarse RRTA raw shape (snake_case) the contract assembler consumes.
 * `{ aggregate, self_harm, fields }`. May be intentionally malformed under
 * fault injection so the boundary validator can reject it.
 */
export interface RrtaRaw {
  aggregate: unknown;
  self_harm: unknown;
  fields: unknown;
}

/**
 * Coarse Sleepwalker raw shape (snake_case) the contract assembler consumes.
 * `{ vulnerable, events, signals, crisis }`.
 */
export interface SleepwalkerRaw {
  vulnerable: unknown;
  events: unknown;
  signals: unknown;
  crisis: unknown;
}
