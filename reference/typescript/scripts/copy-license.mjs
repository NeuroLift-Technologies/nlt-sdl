#!/usr/bin/env node
/**
 * Mechanical LICENSE copy for packaging.
 *
 * The Apache-2.0 LICENSE is authored once at the repo root. This script makes a
 * byte-for-byte copy of that existing file into the package directory at
 * pack/publish time so the published tarball carries its own LICENSE (per
 * `package.json` "files"). It does NOT author, edit, or generate license text —
 * it only copies the existing repo-root file. If the repo-root LICENSE is
 * missing, it fails loudly rather than synthesizing one.
 *
 * Wired into `prepack` so `npm pack` / `npm publish` include LICENSE without it
 * ever being committed inside the package directory.
 */

import { copyFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const pkgDir = resolve(here, '..'); // reference/typescript
const repoRoot = resolve(pkgDir, '..', '..'); // nlt-sdl
const src = resolve(repoRoot, 'LICENSE');
const dest = resolve(pkgDir, 'LICENSE');

if (!existsSync(src)) {
  console.error(
    `[copy-license] repo-root LICENSE not found at ${src}. ` +
      'Refusing to synthesize one — restore the Apache-2.0 LICENSE at the repo root.',
  );
  process.exit(1);
}

copyFileSync(src, dest);
console.error(`[copy-license] copied ${src} -> ${dest}`);
