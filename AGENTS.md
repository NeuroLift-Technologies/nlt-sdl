# AGENTS.md — nlt-sdl Coordination Gateway

> **Internal use only.** Repository-specific governance gateway for coding agents
> operating in `NeuroLift-Technologies/nlt-sdl`.

---

## You Are Here

You are a coding agent in the **NeuroLift Technologies** organization, governed by
**ORG-DEV-OTOI-1.0.0**. This is `nlt-sdl` — the State Detection Layer: a
language-agnostic spec + conformance suite + reference implementations.

**Mandatory reading order:**
1. `AGENTS.md` (this file) — coordination gateway
2. `CLAUDE.md` — repo technical context + hard rules
3. `docs/active-threads.md` — current work state

**Final authority: Joshua W. Dorsey, Sr. Escalate. Do not guess.**

---

## This is safety-critical work

`nlt-sdl` routes crisis response. Before touching anything, internalize the hard
rules in `CLAUDE.md`. The short version:

- **Wrap canon, never rewrite it.** The adapters call `rrt-advocate` and
  `sleepwalker`. Do not copy or modify those detectors.
- **Consume thresholds/lexicons; never invent them.** Tiers come from
  `crisis_thresholds.yaml`.
- **Never weaken a fail-closed test.** Abstain upward.
- **No diagnostic logic, no method/means content.** Coarse detection → human
  routing only.
- **Never touch `LICENSE`** — route to GHCPT or Joshua.

---

## Escalation triggers

Escalate to Joshua immediately when:
- Escalation/recall semantics, the R11 confidence clamp, or the R12 explicit
  override would change.
- The Enabler shape needs implementing (the fade-vs-restrict response decision is
  decoupled and is Joshua's call).
- A conformance vector would need to be loosened to pass.
- Canonical tiers, weights, or lexicons appear wrong.
- Any architectural or deployment decision is required.
- An ethical concern arises.

---

## Session protocol

```
1. Read AGENTS.md, CLAUDE.md, docs/active-threads.md
2. Self-register per OTOI Section 3 (docs/agent-log/)
3. Confirm task scope before beginning
4. Run the conformance suite before committing reference/ or spec/ changes
5. Record a handoff/handback in docs/agent-log/handoffs/
```

## Commit format

```
[AGENT_NAME] type(scope): description
```
Open PRs as **draft**.
