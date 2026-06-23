/**
 * Sleepwalker adapter — wraps the canonical sleepwalker `StateDetector` and
 * derives deterministic continuity events from host facts.
 *
 * Two sources feed the Sleepwalker shape:
 *   * Protective-state detection (dissociation / numbing / avoidance /
 *     detachment) and crisis indicators come from the canonical `StateDetector`
 *     (`@neurolift-technologies/sleepwalker-protocol`), wrapped — its regex
 *     pattern sets are NOT copied into the SDL.
 *   * Deterministic continuity events (model/version change, handoff, memory
 *     gap, tone shift, new session) are derived HERE by diffing the turn's host
 *     facts against the prior turn's facts. These are facts, not guesses, and
 *     bypass any confidence floor (R14). `computeEvents` is adapter-side policy,
 *     not canon — it is ported from the Python reference's `compute_events`.
 */

import { StateDetector } from '@neurolift-technologies/sleepwalker-protocol';

import { RUPTURE_EVENTS } from '../contract.js';
import { RuntimeError } from '../failclosed.js';
import type { SleepwalkerRaw, TurnInput } from '../types.js';

/** A memory gap longer than this (seconds) is treated as a continuity rupture. */
export const MEMORY_GAP_SECONDS = 7 * 24 * 60 * 60; // 7 days

/** Derive deterministic continuity events from host facts (R14). */
export function computeEvents(inp: TurnInput): string[] {
  const events: string[] = [];
  const prior = inp.prior ?? {};

  if (inp.newSession) {
    events.push('new_session');
  }
  if (prior.model && inp.model && prior.model !== inp.model) {
    events.push('model_change');
  }
  if (prior.version && inp.version && prior.version !== inp.version) {
    events.push('version_change');
  }
  if (inp.handoff) {
    events.push('handoff');
  }
  if (prior.tone && inp.tone && prior.tone !== inp.tone) {
    events.push('tone_shift');
  }
  const gap = inp.gapSeconds;
  if (typeof gap === 'number' && !Number.isNaN(gap) && gap > MEMORY_GAP_SECONDS) {
    events.push('memory_gap');
  }
  return events;
}

/**
 * Return the coarse Sleepwalker raw shape for the contract assembler.
 *
 * Output: `{ vulnerable: boolean, events: string[], signals: string[],
 * crisis: boolean }`. Throws on injected faults or real failures so the
 * boundary can fail closed.
 *
 * `StateDetector.detect` is SYNC (no await).
 */
export function detectSleepwalker(inp: TurnInput): SleepwalkerRaw {
  const inject = inp.inject ?? {};
  if (inject.sleepwalkerError) {
    throw new RuntimeError('injected sleepwalker error');
  }

  const events = computeEvents(inp);
  const rupture = events.some((e) => RUPTURE_EVENTS.has(e));

  const detector = new StateDetector();
  const message = inp.message ?? '';
  const state = detector.detect(message);

  const signals: string[] =
    state.protective && state.stateType && state.stateType !== 'neutral'
      ? [state.stateType]
      : [];

  const crisis = Boolean(
    state.explicitSuicidalIdeation || state.selfHarmIndicators || state.inabilityToEnsureSafety,
  );

  return {
    vulnerable: Boolean(state.protective) || rupture,
    events,
    signals,
    crisis,
  };
}
