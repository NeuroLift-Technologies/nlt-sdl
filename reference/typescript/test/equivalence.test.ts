/**
 * NLT-SDL TypeScript reference — conformance + equivalence test (R25).
 *
 * Loads every shipped conformance vector under ../../../conformance/vectors,
 * runs each through `runVector`, validates the result against the contract
 * schema (JSON Schema draft 2020-12, via ajv), and asserts the vector's
 * `expect` block — mirroring the Python conformance runner's `check_expect` so
 * the TS reference is gated by the SAME vectors as the Python reference.
 *
 * This is the in-package safety gate. `npm test` runs it. The cross-language
 * (Python vs TypeScript) byte-equivalence over the same vectors is enforced by
 * the repo conformance runner (`python conformance/runner/conformance.py --impl
 * typescript` vs `--impl python`).
 */

import { readdirSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';

import Ajv2020, { type ValidateFunction } from 'ajv/dist/2020.js';
import { describe, expect, it } from 'vitest';

import { runVector } from '../src/index.js';
import type { DetectionResult } from '../src/types.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(HERE, '..', '..', '..');
const SCHEMA_PATH = resolve(REPO_ROOT, 'spec', 'detection-result.schema.json');
const VECTORS_DIR = resolve(REPO_ROOT, 'conformance', 'vectors');

/** Portable recursive *.json walk (no Node-22+ globSync dependency). */
function walkJson(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      out.push(...walkJson(full));
    } else if (entry.isFile() && entry.name.endsWith('.json')) {
      out.push(full);
    }
  }
  return out.sort();
}

const TIER_ORDER = ['green', 'yellow', 'orange', 'red', 'black'] as const;

interface Vector {
  id: string;
  requirement?: string[];
  description?: string;
  requiresCanon?: boolean;
  input: Record<string, unknown>;
  expect: Record<string, any>;
}

function loadValidator(): ValidateFunction {
  const schema = JSON.parse(readFileSync(SCHEMA_PATH, 'utf8'));
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const ajv = new (Ajv2020 as any)({ allErrors: true, strict: false });
  return ajv.compile(schema);
}

function loadVectors(): Vector[] {
  const files = walkJson(VECTORS_DIR);
  const vectors: Vector[] = [];
  for (const file of files) {
    const parsed = JSON.parse(readFileSync(file, 'utf8')) as Vector[];
    vectors.push(...parsed);
  }
  return vectors;
}

function tierAtMost(actual: string, ceiling: string): boolean {
  return (
    TIER_ORDER.indexOf(actual as (typeof TIER_ORDER)[number]) <=
    TIER_ORDER.indexOf(ceiling as (typeof TIER_ORDER)[number])
  );
}

function tierAtLeast(actual: string, floor: string): boolean {
  return (
    TIER_ORDER.indexOf(actual as (typeof TIER_ORDER)[number]) >=
    TIER_ORDER.indexOf(floor as (typeof TIER_ORDER)[number])
  );
}

const validate = loadValidator();
const vectors = loadVectors();

describe('NLT-SDL TypeScript reference — conformance vectors', () => {
  it('ships at least the 28 known main vectors', () => {
    expect(vectors.length).toBeGreaterThanOrEqual(28);
  });

  for (const vector of vectors) {
    it(`vector ${vector.id}`, async () => {
      const result: DetectionResult = await runVector(vector.input ?? {});
      const exp = vector.expect ?? {};

      if (exp.schemaValid) {
        const ok = validate(result);
        if (!ok) {
          throw new Error(
            `schema validation failed for ${vector.id}: ${JSON.stringify(validate.errors)}`,
          );
        }
        expect(ok).toBe(true);
      }

      if ('escalateToHuman' in exp) {
        expect(result.escalateToHuman).toBe(exp.escalateToHuman);
      }

      if ('recommendedModeIn' in exp) {
        expect(exp.recommendedModeIn).toContain(result.recommendedMode);
      }

      const rrtaExp = exp.rrta ?? {};
      if ('tier' in rrtaExp) {
        expect(result.rrta.tier).toBe(rrtaExp.tier);
      }
      if ('tierAtMost' in rrtaExp) {
        expect(tierAtMost(result.rrta.tier, rrtaExp.tierAtMost)).toBe(true);
      }
      if ('tierAtLeast' in rrtaExp) {
        expect(tierAtLeast(result.rrta.tier, rrtaExp.tierAtLeast)).toBe(true);
      }
      if ('explicitSignal' in rrtaExp) {
        expect(result.rrta.explicitSignal).toBe(rrtaExp.explicitSignal);
      }
      if ('signalsInclude' in rrtaExp) {
        for (const sig of rrtaExp.signalsInclude as string[]) {
          expect(result.rrta.signals).toContain(sig);
        }
      }

      const swExp = exp.sleepwalker ?? {};
      if ('vulnerable' in swExp) {
        expect(result.sleepwalker.vulnerable).toBe(swExp.vulnerable);
      }
      if ('eventsInclude' in swExp) {
        for (const ev of swExp.eventsInclude as string[]) {
          expect(result.sleepwalker.events).toContain(ev);
        }
      }
      if ('signalsInclude' in swExp) {
        for (const sig of swExp.signalsInclude as string[]) {
          expect(result.sleepwalker.signals).toContain(sig);
        }
      }

      const metaExp = exp.meta ?? {};
      if ('failClosed' in metaExp) {
        expect(result.meta.failClosed).toBe(metaExp.failClosed);
      }

      // Schema invariant: suggestedPersona must never be emitted as null.
      expect(result).not.toHaveProperty('suggestedPersona', null);
    });
  }
});
