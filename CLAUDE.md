# CLAUDE.md — nlt-sdl
## Governance: ORG-DEV-OTOI-1.0.0 | Authority: Joshua W. Dorsey, Sr.

Repo-specific context for Claude Code / GitHub Copilot agents operating in
`nlt-sdl`. Read `AGENTS.md` first (coordination gateway), then this file.

**Final authority: Joshua W. Dorsey, Sr. Escalate. Do not guess.**

---

## What this repo is

`nlt-sdl` is the **State Detection Layer** — a *language-agnostic specification*,
not a single codebase. It has three parts:

1. **Spec** (`spec/`) — `NLT-SPEC-SDL-1.0.0`: the `DetectionResult` contract
   (`spec/detection-result.schema.json`, JSON Schema draft 2020-12) plus the
   normative requirements (`spec/nlt-sdl-spec.md`, IDs `R1..Rn`).
2. **Conformance suite** (`conformance/`) — the **safety gate**. Every
   requirement is covered by ≥1 vector. Fail-closed vectors are mandatory and
   **must not be stubbed green**.
3. **Reference implementations** (`reference/`) — conformant wrappers. The Python
   reference (`reference/python/nlt_sdl`) *wraps* the canonical rrt-advocate and
   sleepwalker detectors behind the contract with a fail-closed boundary.

The SDL unifies three detection **shapes** behind one contract:
- **RRTA** — acute, in-session crisis (graduated tiers; red/black require an
  explicit signal).
- **Sleepwalker** — deterministic continuity/rupture + protective states.
- **Enabler** — longitudinal agency erosion. **Reserved in 1.0.0** (contract-only).

---

## ⚠️ Safety-critical. Read before changing anything.

This layer routes crisis response. It is **fail-closed by construction**,
**abstention-first**, and **NOT a clinical or diagnostic tool**. Coarse crisis
detection → human routing only.

**Hard rules (escalate, do not self-approve):**
- **Do NOT modify, copy, or reimplement** the canonical detectors. The adapters
  *wrap* `rrt-advocate` and `sleepwalker`. Canon stays in canon.
- **Do NOT invent lexicons or thresholds.** Tiers come from
  `rrt-advocate config/crisis_thresholds.yaml`; lexicons live in
  `keyword_layer.py`. The SDL consumes them.
- **Do NOT weaken a fail-closed test** to make CI green. A green stub of a
  fail-closed vector is a governance violation.
- **Do NOT add diagnostic logic or any method/means content.**
- **Do NOT create or modify `LICENSE`.** Claude Code is blocked from LICENSE
  files — route LICENSE changes to GHCPT or Joshua.
- Changing escalation/recall semantics, the confidence clamp (R11), or the
  explicit-signal override (R12) requires Joshua's approval.

---

## Certification target

Conformant implementations are certified on **calibration, fail-closed behavior,
recall on explicit signals, and cross-implementation equivalence** — **NOT** on
"accuracy." Stronger detection is a clinician/eval-data track (mPACT-style ground
truth), not a code change here: swap a detector behind the same contract.

---

## How the Python reference resolves canon

The adapters locate the sibling canonical repos via, in order:
1. Env vars `RRT_ADVOCATE_SRC` (→ `rrt-advocate/src`) and `SLEEPWALKER_ROOT`
   (→ `sleepwalker`).
2. Sibling directories next to the `nlt-sdl` checkout.

If canon cannot be imported, the boundary fails closed (escalates) rather than
returning a silent green. Missing canon is safe by construction.

---

## Key commands

```bash
# Full conformance suite (needs sibling canon checkouts)
python conformance/runner/conformance.py --impl python

# Canon-free gate (fault-injection vectors only)
python conformance/runner/conformance.py --impl python --category failclosed

# Unit tests (policy + fail-closed; no canon needed)
python -m pytest reference/python/tests -q
```

Run the conformance suite before every commit that touches `reference/` or
`spec/`. CI (`.github/workflows/conformance.yml`) runs it on every PR.

---

## Map

| Path | Purpose |
|---|---|
| `spec/nlt-sdl-spec.md` | Normative spec + requirement IDs |
| `spec/detection-result.schema.json` | The contract (JSON Schema) |
| `conformance/README.md` | Vector format + runner contract |
| `conformance/vectors/` | The safety-gate vectors by category |
| `conformance/runner/conformance.py` | Executable gate |
| `reference/python/nlt_sdl/contract.py` | Policy brain (tiers, clamp, routing) |
| `reference/python/nlt_sdl/failclosed.py` | Fail-closed boundary (R20–R24) |
| `reference/python/nlt_sdl/adapters/` | Canon wrappers (RRTA, Sleepwalker) |
| `docs/active-threads.md` | Live work state — check before any thread |
| `docs/agent-log/handoffs/` | OTOI session handoff/handback records |

---

## Commit format

```
[AGENT_NAME] type(scope): description
```
Types: `feat`, `fix`, `docs`, `refactor`, `chore`, `test`, `ci`.
Open PRs as **draft**.
