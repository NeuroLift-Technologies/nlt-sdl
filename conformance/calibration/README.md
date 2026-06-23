# NLT-SDL Calibration Harness (first cut)

> **Status:** first cut. The **math is real and reusable**; the **default labels
> are SYNTHETIC placeholders**. Do not quote any number this prints from the
> synthetic dataset as a calibration measurement.

`NLT-SPEC-SDL-1.0.0` certifies implementations on **calibration**, fail-closed
behavior, recall on explicit signals, and cross-implementation equivalence —
**not** "accuracy." This harness is the first runnable piece of the calibration
track: it measures how well a detector's confidence matches reality.

## What it computes

Over a labeled dataset of `(confidence, label)` pairs, using equal-width
confidence binning:

- **ECE — Expected Calibration Error** — sample-weighted mean gap between each
  bin's mean predicted confidence and its empirical positive rate:
  `ECE = Σ_b (n_b / N) · |acc(b) − conf(b)|`.
- **MCE — Maximum Calibration Error** — the single worst bin gap:
  `MCE = max_b |acc(b) − conf(b)|`.

A perfectly calibrated detector has `ECE = MCE = 0`.

## Run it

```bash
# default: the synthetic placeholder dataset (smoke-test only)
python conformance/calibration/calibration.py

# against a real labeled benchmark, with custom bin count
python conformance/calibration/calibration.py --dataset path/to/real.json --bins 10

# machine-readable
python conformance/calibration/calibration.py --json
```

No canon and no extra dependencies are required — the harness reads a dataset
file and computes the metrics from pure Python.

## Dataset format

```jsonc
{
  "_dataset_id": "…",
  "samples": [
    { "confidence": 0.41, "label": 0 },   // confidence in [0,1]; label ∈ {0,1}
    { "confidence": 0.88, "label": 1 }
  ]
}
```

`label = 1` means the turn is a true crisis-positive; `label = 0` means it is
not. `confidence` is the detector's aggregate crisis-positive confidence for
that turn.

## ⚠️ The synthetic dataset must be replaced

`dataset.synthetic.json` is **hand-authored, first-cut, synthetic** data that
exists only to drive the math end-to-end. It is **not** clinician-labeled and
**not** mPACT ground truth. The harness prints a `WARNING` whenever it loads a
dataset carrying the synthetic markers.

The real benchmark is the **clinician / mPACT-labeled** track and is
**Joshua-owned** — replacing the labels is a data task, not a code change. When
that benchmark exists, point `--dataset` at it; the harness is unchanged.
