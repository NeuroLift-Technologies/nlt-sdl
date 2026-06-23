#!/usr/bin/env node
/**
 * NLT-SDL TypeScript conformance CLI shim.
 *
 * Reads ONE JSON object (a vector's `input`) from stdin, runs it through
 * `runVector`, and prints the resulting schema-valid `DetectionResult` as JSON
 * to stdout. This is the bridge the Python conformance runner's
 * `load_typescript_impl` subprocesses, so the same conformance vectors gate both
 * the Python and TypeScript references (R25 equivalence).
 *
 * Contract:
 *   stdin  : a single JSON object (the turn input). Empty stdin -> `{}`.
 *   stdout : exactly one JSON object (the DetectionResult).
 *   exit 0 : on success; non-zero with a diagnostic on stderr on failure.
 */

import { runVector } from './index.js';

async function readStdin(): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of process.stdin) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk as string));
  }
  return Buffer.concat(chunks).toString('utf8');
}

async function main(): Promise<void> {
  const raw = (await readStdin()).trim();
  const input = raw.length > 0 ? JSON.parse(raw) : {};
  const result = await runVector(input);
  process.stdout.write(JSON.stringify(result));
  process.stdout.write('\n');
}

main().catch((err: unknown) => {
  const message = err instanceof Error ? `${err.name}: ${err.message}` : String(err);
  process.stderr.write(`conformance-cli failed: ${message}\n`);
  process.exit(1);
});
