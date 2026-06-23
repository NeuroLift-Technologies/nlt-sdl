#!/usr/bin/env python3
"""
NLT-SDL conformance runner.

Loads every vector under ``conformance/vectors/``, runs each through the chosen
implementation, validates the result against the contract schema, and checks the
vector's ``expect`` block. Exits non-zero on any failure.

Usage:
    python conformance/runner/conformance.py --impl python [--category failclosed]

The runner is the safety gate. Fail-closed vectors must pass against real code,
never a green stub.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from typing import Any, Callable

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "spec" / "detection-result.schema.json"
VECTORS_DIR = REPO_ROOT / "conformance" / "vectors"

TIER_ORDER = ["green", "yellow", "orange", "red", "black"]


def load_python_impl() -> Callable[[dict[str, Any]], dict[str, Any]]:
    sys.path.insert(0, str(REPO_ROOT / "reference" / "python"))
    from nlt_sdl import run_vector  # type: ignore

    return run_vector


def load_typescript_impl() -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Drive the built TypeScript reference via its conformance CLI shim.

    The TS reference (``reference/typescript``) wraps the published TS canon
    packages and ports only the SDL's own policy brain. It exposes the same
    single-turn contract as the Python reference. This impl subprocesses the
    compiled ``dist/conformance-cli.js``: the vector input is passed as JSON on
    stdin, and the JSON object on stdout is parsed as the DetectionResult. The
    same conformance vectors therefore gate both references (R25 equivalence).
    """
    cli = REPO_ROOT / "reference" / "typescript" / "dist" / "conformance-cli.js"
    if not cli.exists():
        raise FileNotFoundError(
            f"TypeScript conformance CLI not built at {cli}. "
            "Run: (cd reference/typescript && npm install && npm run build)"
        )

    def run_vector(inp: dict[str, Any]) -> dict[str, Any]:
        proc = subprocess.run(
            ["node", str(cli)],
            input=json.dumps(inp),
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"typescript conformance-cli exited {proc.returncode}: "
                f"{proc.stderr.strip()}"
            )
        return json.loads(proc.stdout)

    return run_vector


IMPLS: dict[str, Callable[[], Callable[[dict[str, Any]], dict[str, Any]]]] = {
    "python": load_python_impl,
    "typescript": load_typescript_impl,
}


def load_schema_validator():
    import jsonschema

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)
    return cls(schema)


def iter_vectors(category: str | None):
    for path in sorted(VECTORS_DIR.rglob("*.json")):
        if category and path.parent.name != category:
            continue
        vectors = json.loads(path.read_text(encoding="utf-8"))
        for vector in vectors:
            yield path.relative_to(REPO_ROOT), vector


def _tier_at_most(actual: str, ceiling: str) -> bool:
    return TIER_ORDER.index(actual) <= TIER_ORDER.index(ceiling)


def _tier_at_least(actual: str, floor: str) -> bool:
    return TIER_ORDER.index(actual) >= TIER_ORDER.index(floor)


def check_expect(result: dict[str, Any], expect: dict[str, Any]) -> list[str]:
    """Return a list of failure messages (empty == pass)."""
    failures: list[str] = []

    def fail(msg: str) -> None:
        failures.append(msg)

    if "escalateToHuman" in expect:
        if result.get("escalateToHuman") != expect["escalateToHuman"]:
            fail(
                f"escalateToHuman: expected {expect['escalateToHuman']}, "
                f"got {result.get('escalateToHuman')}"
            )

    if "recommendedModeIn" in expect:
        if result.get("recommendedMode") not in expect["recommendedModeIn"]:
            fail(
                f"recommendedMode {result.get('recommendedMode')!r} "
                f"not in {expect['recommendedModeIn']}"
            )

    rrta_exp = expect.get("rrta", {})
    rrta = result.get("rrta", {})
    if "tier" in rrta_exp and rrta.get("tier") != rrta_exp["tier"]:
        fail(f"rrta.tier: expected {rrta_exp['tier']}, got {rrta.get('tier')}")
    if "tierAtMost" in rrta_exp and not _tier_at_most(rrta.get("tier", "black"), rrta_exp["tierAtMost"]):
        fail(f"rrta.tier {rrta.get('tier')} exceeds ceiling {rrta_exp['tierAtMost']}")
    if "tierAtLeast" in rrta_exp and not _tier_at_least(rrta.get("tier", "green"), rrta_exp["tierAtLeast"]):
        fail(f"rrta.tier {rrta.get('tier')} below floor {rrta_exp['tierAtLeast']}")
    if "explicitSignal" in rrta_exp and rrta.get("explicitSignal") != rrta_exp["explicitSignal"]:
        fail(f"rrta.explicitSignal: expected {rrta_exp['explicitSignal']}, got {rrta.get('explicitSignal')}")
    if "signalsInclude" in rrta_exp:
        missing = set(rrta_exp["signalsInclude"]) - set(rrta.get("signals", []))
        if missing:
            fail(f"rrta.signals missing {sorted(missing)} (got {rrta.get('signals')})")

    sw_exp = expect.get("sleepwalker", {})
    sw = result.get("sleepwalker", {})
    if "vulnerable" in sw_exp and sw.get("vulnerable") != sw_exp["vulnerable"]:
        fail(f"sleepwalker.vulnerable: expected {sw_exp['vulnerable']}, got {sw.get('vulnerable')}")
    if "eventsInclude" in sw_exp:
        missing = set(sw_exp["eventsInclude"]) - set(sw.get("events", []))
        if missing:
            fail(f"sleepwalker.events missing {sorted(missing)} (got {sw.get('events')})")
    if "signalsInclude" in sw_exp:
        missing = set(sw_exp["signalsInclude"]) - set(sw.get("signals", []))
        if missing:
            fail(f"sleepwalker.signals missing {sorted(missing)} (got {sw.get('signals')})")

    meta_exp = expect.get("meta", {})
    meta = result.get("meta", {})
    if "failClosed" in meta_exp and meta.get("failClosed") != meta_exp["failClosed"]:
        fail(f"meta.failClosed: expected {meta_exp['failClosed']}, got {meta.get('failClosed')}")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="NLT-SDL conformance runner")
    parser.add_argument("--impl", default="python", choices=sorted(IMPLS))
    parser.add_argument("--category", default=None, help="run only one vector category dir")
    parser.add_argument(
        "--skip-requires-canon",
        action="store_true",
        help="skip vectors flagged requiresCanon (for the canon-free CI gate)",
    )
    args = parser.parse_args()

    run_vector = IMPLS[args.impl]()
    validator = load_schema_validator()

    total = 0
    passed = 0
    skipped = 0
    failures: list[tuple[str, str, list[str]]] = []

    for rel_path, vector in iter_vectors(args.category):
        if args.skip_requires_canon and vector.get("requiresCanon"):
            skipped += 1
            continue
        total += 1
        vid = vector.get("id", "<no-id>")
        expect = vector.get("expect", {})
        try:
            result = run_vector(vector.get("input", {}))
        except Exception as exc:  # an impl must never raise to the runner
            failures.append((str(rel_path), vid, [f"run_vector raised {type(exc).__name__}: {exc}"]))
            continue

        vec_failures: list[str] = []
        if expect.get("schemaValid"):
            schema_errors = sorted(validator.iter_errors(result), key=lambda e: e.path)
            for err in schema_errors:
                vec_failures.append(f"schema: {err.message} at {list(err.path)}")
        vec_failures.extend(check_expect(result, expect))

        if vec_failures:
            failures.append((str(rel_path), vid, vec_failures))
        else:
            passed += 1

    skip_note = f" ({skipped} skipped: requiresCanon)" if skipped else ""
    print(f"\nNLT-SDL conformance ({args.impl}): {passed}/{total} vectors passed{skip_note}")
    if failures:
        print("\nFAILURES:")
        for rel_path, vid, msgs in failures:
            print(f"  [{rel_path}] {vid}")
            for msg in msgs:
                print(f"      - {msg}")
        return 1
    print("All conformance vectors passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
