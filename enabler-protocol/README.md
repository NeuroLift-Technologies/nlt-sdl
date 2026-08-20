# Enabler Protocol — Longitudinal Agency Detection

> **Status:** Reserved in SDL 1.0.0 (contract-only). Product feature spec: `NLT-PROD-EP-001 v2.0`.
> **Owner:** Joshua W. Dorsey, Sr. · **Repo:** `nlt-sdl` · **Related:** `Sleepwalker Protocol (NLT-PROD-SWP-001)`

---

## What it is

The Enabler shape is the third detection shape in the State Detection Layer — alongside
**RRTA** (acute, in-session) and **Sleepwalker** (deterministic continuity).

Where RRTA asks *"is this turn in or near crisis right now?"* and Sleepwalker asks
*"did continuity rupture, or is the user in a protective state?"*, the Enabler shape asks:

> **"Is this user's agency eroding across sessions?"**

It is a **longitudinal** detection shape — it operates across sessions, not within a single turn.
It never labels dependency from a single turn (R18).

---

## Where it sits in the SDL contract

Every conformant `DetectionResult` (schema: `spec/detection-result.schema.json`) carries an
`enabler` field:

```jsonc
{
  "rrta":        { "tier": "green", "confidence": 0.05, "signals": [], "explicitSignal": false },
  "sleepwalker": { "vulnerable": false, "events": [], "signals": [] },
  "enabler":     { "risk": "none", "confidence": 0.0, "agencyTrend": 0, "signals": [] },
  "recommendedMode": "standard",
  "responseConstraints": [],
  "escalateToHuman": false,
  "meta": { "failClosed": false, "schemaVersion": "1.0.0", "notes": [] }
}
```

The current `EnablerResult` type (TypeScript reference: `src/types.ts`) is:

```typescript
export interface EnablerResult {
  risk: 'none' | 'low' | 'moderate' | 'elevated';
  confidence: number;
  agencyTrend: number;
  signals: string[];
}
```

### Spec requirements (from `spec/nlt-sdl-spec.md`)

| Req | Meaning in 1.0.0 |
|---|---|
| **R17** | With no longitudinal implementation, `enabler` MUST be `risk="none"`, low confidence, `agencyTrend=0`, empty `signals`. |
| **R18** | An implementation MUST NOT assert dependency (`risk` above `none`) from a single turn. |

The contract field exists. The implementation is reserved.

---

## Relationship to the Enabler Protocol product feature

The SDL's **Enabler detection shape** is the detection half of a broader product feature called
the **Enabler Protocol** — documented in `NLT-PROD-EP-001 v2.0` (where it was rediscovered,
Feb 2026, after being authored ~Sept 2025).

The product feature spec defines:

- **Purpose:** promote healthy, empowered user relationships with AI assistance by surfacing
  measurable usage patterns and progressively gating non-essential features through transparent,
  rules-based product logic.
- **Core principle:** *AI should expand what you can do, not replace what you should do.*
- **Architectural position:** product layer only. Not AI/ML. Not TOI/OTOI. Deterministic,
  user-transparent logic, tied to the Sleepwalker Protocol.
- **Three-state feature access model:**
  ```
  Active ──► Prompted ──► Gated
    ▲                        │
    └─────── Unlocked ◄─────┘
  ```
- **Feature classification:** Essential Support / Guided Assistance / Convenience Amplifiers / Growth Features
- **Tier-based response:** Tier 1 (notification + growth prompt) → Tier 2 (non-essential convenience restricted) → Tier 3 (additional gates) → Unlock (progress demonstrated)
- **Override rights:** accessible, transparent, non-penalizing, logged for user reflection
- **Design constraints:** no essential support features ever gated; all thresholds visible; all unlock criteria defined and achievable; user agency preserved; tone encouraging never critical

**The SDL layer and the product feature are complementary, not the same thing:**

| Concern | Lives in |
|---|---|
| Longitudinal agency signal (is agency eroding across sessions?) | SDL Enabler detection shape |
| Feature gating decision (fade vs. restrict, which features, which thresholds) | Product feature layer — **deferred to Joshua** |
| Crisis routing / continuity detection / fail-closed boundary | SDL RRTA + Sleepwalker shapes |

---

## What 1.0.0 ships

**Now:**
- Contract field `enabler` present on every `DetectionResult`
- Reference implementations return `risk="none"`, `confidence=0.0`, `agencyTrend=0`, `signals=[]`
- `enabler_agency_support` is a reserved `RecommendedMode` in the TypeScript reference (`src/contract.ts`) — it is not selected by current routing logic

**Not in 1.0.0:**
- Any longitudinal agency measurement
- Any dependency detection, fade logic, or restrict logic
- Any `risk` value above `none`

A real implementation would swap in a longitudinal detector behind the same contract — same `DetectionResult` shape, populated data. Stronger detection is a clinician / eval-data track, not a code change to this layer.

---

## Open items (deferred)

The following are **decoupled from the SDL contract** and are **Joshua's call** before any
Enabler implementation ships:

1. **Fade vs. restrict decision.** When longitudinal agency signals indicate erosion, does the
   product *fade* support (gradually reduce assistance) or *restrict* features (gate access)?
   The response decision is separate from the detection shape and is not implemented without
   direction. See `docs/agent-log/handoffs/NLT-HND-2026-001-SDL-Build-Kickoff-handback.md`.

2. **Feature classification.** Complete product feature inventory classified into the four
   categories (Essential Support / Guided Assistance / Convenience Amplifiers / Growth Features).
   This is a product-team + community decision, not an SDL concern.

3. **Threshold values and time windows.** What longitudinal signals, at what magnitudes over what
   windows, produce `risk` above `none`? Requires usage data to calibrate; initial values should
   be conservative.

4. **Unlock criteria per feature category.** What counts as "demonstrated progress" for each
   gated feature? Must be achievable across cognitive profiles.

5. **User transparency interface.** How does the product communicate lock status and unlock
   requirements? MVP scope per v2.0 spec: usage transparency dashboard only, no automated gating.

---

## Source artifact

The Enabler Protocol product feature specification (`NLT-PROD-EP-001 v2.0`) was rediscovered in
Joshua's Claude data, conversation `dcf92462-518a-4c75-aa4c-0a1b5b680b84` ("Forgotten reminder",
Feb 2026), and is cross-referenced in the `AI business strategy blueprint` conversation
(`fcc1c3c6-3a5d-40d6-94ae-9a8bdb9aa97d`, June 2026).

This README is a placeholder capturing the SDL-side relationship. The canonical product feature
spec lives in the Claude data artifact, not in this repo — until a decision is made to vendor it.
