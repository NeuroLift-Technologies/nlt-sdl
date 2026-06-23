/**
 * Fail-closed boundary (NLT-SPEC-SDL-1.0.0 R20-R24) — TypeScript reference.
 *
 * Faithful port of the Python reference's `failclosed.py`. The boundary's job is
 * simple and load-bearing: run an underlying detector, and if it raises, times
 * out, or returns a value that violates its contract, do NOT let that turn pass
 * silently. Instead surface a failure the assembler turns into an escalating
 * `failClosed` result. Abstention is always *upward*.
 *
 * This is the SDL's core value-add over the raw canonical detectors: the canon
 * produces scores; the boundary guarantees that an *absence* of a usable score
 * escalates rather than defaulting to safe.
 *
 * Cross-language equivalence note (R25): the fail-closed `note` is
 * `${name}_failclosed:${error.constructor.name}` — PII-free, only the failing
 * detector name + the exception *type*. To make these notes byte-identical to
 * the Python reference (which uses `type(exc).__name__`), the error classes
 * below are deliberately named `RuntimeError`, `TimeoutError`, and `ValueError`
 * so `error.constructor.name` matches Python's exception names exactly.
 */

import type { RrtaRaw, SleepwalkerRaw } from './types.js';

/* eslint-disable @typescript-eslint/no-shadow */

/** Named to match Python's `RuntimeError` for cross-language note equivalence. */
export class RuntimeError extends Error {
  constructor(message?: string) {
    super(message);
    this.name = 'RuntimeError';
    // Force `constructor.name` to be 'RuntimeError' even after minification.
    Object.defineProperty(this, 'constructor', {
      value: RuntimeError,
      enumerable: false,
      writable: true,
      configurable: true,
    });
  }
}

/** Named to match Python's `TimeoutError` for cross-language note equivalence. */
export class TimeoutError extends Error {
  constructor(message?: string) {
    super(message);
    this.name = 'TimeoutError';
    Object.defineProperty(this, 'constructor', {
      value: TimeoutError,
      enumerable: false,
      writable: true,
      configurable: true,
    });
  }
}

/** Named to match Python's `ValueError` for cross-language note equivalence. */
export class ValueError extends Error {
  constructor(message?: string) {
    super(message);
    this.name = 'ValueError';
    Object.defineProperty(this, 'constructor', {
      value: ValueError,
      enumerable: false,
      writable: true,
      configurable: true,
    });
  }
}

/** Result of running one detector behind the fail-closed boundary. */
export interface GuardOutcome<T> {
  value: T | null;
  failed: boolean;
  note: string | null;
}

/**
 * Run `fn(inp)` behind the boundary.
 *
 * On success (and passing `validator`), returns the value. On *any* throw —
 * including injected faults, import failures, timeouts, and contract violations
 * raised by the validator — returns a failed outcome carrying a PII-free note
 * (R4: only the failing detector name + exception type, never message content).
 *
 * `fn` may be sync or async; a returned Promise is awaited.
 */
export async function guarded<T>(
  name: string,
  fn: (inp: Record<string, unknown>) => T | Promise<T>,
  inp: Record<string, unknown>,
  validator?: (value: unknown) => void,
): Promise<GuardOutcome<T>> {
  try {
    const value = await fn(inp);
    if (validator !== undefined) {
      validator(value);
    }
    return { value, failed: false, note: null };
  } catch (err) {
    // The boundary must catch everything.
    const errName =
      err && typeof err === 'object' && 'constructor' in err && err.constructor
        ? (err.constructor as { name?: string }).name ?? 'Error'
        : 'Error';
    return { value: null, failed: true, note: `${name}_failclosed:${errName}` };
  }
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/**
 * Reject malformed RRTA detector output (R20).
 *
 * A conformant RRTA raw output is an object with a finite `aggregate` in [0,1],
 * a strictly-boolean `self_harm`, and an array `fields`. Anything else is a
 * contract violation that MUST fail closed rather than be coerced.
 */
export function validateRrtaRaw(value: unknown): asserts value is RrtaRaw {
  if (!isPlainObject(value)) {
    throw new ValueError('rrta raw output is not an object');
  }
  const agg = value['aggregate'];
  if (typeof agg !== 'number' || Number.isNaN(agg)) {
    throw new ValueError('rrta aggregate is not a number');
  }
  if (!(agg >= 0.0 && agg <= 1.0)) {
    throw new ValueError('rrta aggregate out of range');
  }
  if (typeof value['self_harm'] !== 'boolean') {
    throw new ValueError('rrta self_harm is not a bool');
  }
  if (!Array.isArray(value['fields'])) {
    throw new ValueError('rrta fields is not a list');
  }
}

/** Reject malformed Sleepwalker detector output (R20). */
export function validateSleepwalkerRaw(value: unknown): asserts value is SleepwalkerRaw {
  if (!isPlainObject(value)) {
    throw new ValueError('sleepwalker raw output is not an object');
  }
  for (const key of ['vulnerable', 'crisis'] as const) {
    if (typeof value[key] !== 'boolean') {
      throw new ValueError(`sleepwalker ${key} is not a bool`);
    }
  }
  for (const key of ['events', 'signals'] as const) {
    if (!Array.isArray(value[key])) {
      throw new ValueError(`sleepwalker ${key} is not a list`);
    }
  }
}
