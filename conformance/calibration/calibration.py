#!/usr/bin/env python3
"""
NLT-SDL calibration harness — Expected & Maximum Calibration Error.

This is the **first cut** of the calibration measurement called for by
``NLT-SPEC-SDL-1.0.0`` and the repo README ("certified on calibration ... not
'accuracy'"). It computes two standard reliability metrics over a labeled
dataset of ``(confidence, label)`` pairs using equal-width confidence binning:

  * **ECE** — Expected Calibration Error: the sample-weighted mean gap between
    each bin's mean predicted confidence and its empirical accuracy.

        ECE = Σ_b (n_b / N) * | acc(b) - conf(b) |

  * **MCE** — Maximum Calibration Error: the single worst bin gap.

        MCE = max_b | acc(b) - conf(b) |

where, for bin ``b`` containing the samples whose confidence falls in that bin:
  - ``conf(b)`` = mean predicted confidence of the samples in the bin
  - ``acc(b)``  = fraction of those samples whose ground-truth label is 1
  - ``n_b``     = number of samples in the bin, ``N`` = total samples

A perfectly calibrated detector has ECE = MCE = 0 (every bin's predicted
confidence matches its observed positive rate).

------------------------------------------------------------------------------
FIRST-CUT / SYNTHETIC DATA — READ THIS
------------------------------------------------------------------------------
The default dataset (``dataset.synthetic.json``) is a **clearly-labeled
synthetic placeholder**. Its labels are hand-authored to exercise the binning
math end-to-end; they are NOT clinician-labeled and NOT mPACT ground truth.
**Any number this prints from the synthetic file is a smoke-test of the harness,
not a measurement of detector calibration.** Swap in the real clinician /
mPACT-labeled benchmark (Joshua-owned) before quoting any calibration figure.

The math here is real and reusable; only the *labels* are placeholder. When the
real benchmark exists, point ``--dataset`` at it — no code change required.

Usage:
    python conformance/calibration/calibration.py
    python conformance/calibration/calibration.py --dataset path/to/real.json --bins 10
"""

from __future__ import annotations

import argparse
import json
import pathlib
from dataclasses import dataclass

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_DATASET = HERE / "dataset.synthetic.json"


@dataclass
class Bin:
    lo: float
    hi: float
    count: int
    mean_confidence: float
    accuracy: float
    gap: float


@dataclass
class CalibrationReport:
    n_samples: int
    n_bins: int
    ece: float
    mce: float
    bins: list[Bin]
    synthetic: bool
    dataset_id: str


def load_samples(path: pathlib.Path) -> tuple[list[tuple[float, int]], dict]:
    """Load (confidence, label) pairs and surface dataset metadata.

    Validates that confidences are in [0, 1] and labels are binary {0, 1}.
    """
    data = json.loads(path.read_text(encoding="utf-8"))
    raw = data.get("samples", [])
    if not raw:
        raise ValueError(f"dataset has no samples: {path}")

    samples: list[tuple[float, int]] = []
    for i, row in enumerate(raw):
        c = float(row["confidence"])
        y = int(row["label"])
        if not (0.0 <= c <= 1.0):
            raise ValueError(f"sample {i}: confidence {c} out of [0,1]")
        if y not in (0, 1):
            raise ValueError(f"sample {i}: label {y} is not binary 0/1")
        samples.append((c, y))

    meta = {
        "dataset_id": data.get("_dataset_id", path.name),
        # Treat the dataset as synthetic unless it explicitly clears the markers.
        "synthetic": bool(
            data.get("_README") or data.get("_warning") or data.get("synthetic", False)
        ),
    }
    return samples, meta


def _bin_index(confidence: float, n_bins: int) -> int:
    """Map a confidence to an equal-width bin index in [0, n_bins-1].

    Bins are half-open [lo, hi) except the top bin, which includes 1.0.
    """
    if confidence >= 1.0:
        return n_bins - 1
    idx = int(confidence * n_bins)
    if idx < 0:
        idx = 0
    if idx >= n_bins:
        idx = n_bins - 1
    return idx


def compute_calibration(
    samples: list[tuple[float, int]], n_bins: int = 10
) -> tuple[float, float, list[Bin]]:
    """Compute ECE, MCE, and per-bin reliability over (confidence, label) pairs.

    Returns ``(ece, mce, bins)``. Empty bins contribute nothing to ECE and are
    excluded from MCE (no samples => no measurable gap).
    """
    if n_bins < 1:
        raise ValueError("n_bins must be >= 1")

    total = len(samples)
    sums = [0.0] * n_bins  # sum of confidences per bin
    pos = [0] * n_bins  # count of positive labels per bin
    counts = [0] * n_bins  # number of samples per bin

    for confidence, label in samples:
        b = _bin_index(confidence, n_bins)
        sums[b] += confidence
        pos[b] += label
        counts[b] += 1

    ece = 0.0
    mce = 0.0
    bins: list[Bin] = []
    width = 1.0 / n_bins

    for b in range(n_bins):
        lo = b * width
        hi = (b + 1) * width
        n_b = counts[b]
        if n_b == 0:
            bins.append(Bin(lo=lo, hi=hi, count=0, mean_confidence=0.0, accuracy=0.0, gap=0.0))
            continue
        mean_conf = sums[b] / n_b
        accuracy = pos[b] / n_b
        gap = abs(accuracy - mean_conf)
        ece += (n_b / total) * gap
        mce = max(mce, gap)
        bins.append(
            Bin(
                lo=lo,
                hi=hi,
                count=n_b,
                mean_confidence=mean_conf,
                accuracy=accuracy,
                gap=gap,
            )
        )

    return ece, mce, bins


def build_report(path: pathlib.Path, n_bins: int) -> CalibrationReport:
    samples, meta = load_samples(path)
    ece, mce, bins = compute_calibration(samples, n_bins)
    return CalibrationReport(
        n_samples=len(samples),
        n_bins=n_bins,
        ece=ece,
        mce=mce,
        bins=bins,
        synthetic=meta["synthetic"],
        dataset_id=meta["dataset_id"],
    )


def print_report(report: CalibrationReport, dataset_path: pathlib.Path) -> None:
    print("NLT-SDL calibration (first cut)")
    print(f"  dataset    : {dataset_path}")
    print(f"  dataset_id : {report.dataset_id}")
    print(f"  samples    : {report.n_samples}")
    print(f"  bins       : {report.n_bins} (equal width)")
    if report.synthetic:
        print(
            "  WARNING    : SYNTHETIC placeholder labels — these numbers smoke-test "
            "the harness,\n"
            "               they are NOT a calibration measurement. Replace with the "
            "real\n"
            "               clinician / mPACT-labeled benchmark before quoting any figure."
        )
    print()
    print("  bin            n   mean_conf   accuracy   |gap|")
    print("  ----------   ---   ---------   --------   -----")
    for b in report.bins:
        if b.count == 0:
            print(f"  [{b.lo:0.2f},{b.hi:0.2f})    0          -          -       -")
            continue
        print(
            f"  [{b.lo:0.2f},{b.hi:0.2f}) {b.count:5d}   "
            f"{b.mean_confidence:9.4f}   {b.accuracy:8.4f}   {b.gap:5.4f}"
        )
    print()
    print(f"  ECE = {report.ece:.4f}")
    print(f"  MCE = {report.mce:.4f}")


def main() -> int:
    parser = argparse.ArgumentParser(description="NLT-SDL ECE/MCE calibration harness")
    parser.add_argument(
        "--dataset",
        type=pathlib.Path,
        default=DEFAULT_DATASET,
        help="path to a labeled (confidence,label) dataset JSON (default: synthetic placeholder)",
    )
    parser.add_argument(
        "--bins",
        type=int,
        default=10,
        help="number of equal-width confidence bins (default: 10)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the report as JSON instead of a table",
    )
    args = parser.parse_args()

    report = build_report(args.dataset, args.bins)

    if args.json:
        print(
            json.dumps(
                {
                    "dataset": str(args.dataset),
                    "dataset_id": report.dataset_id,
                    "synthetic": report.synthetic,
                    "n_samples": report.n_samples,
                    "n_bins": report.n_bins,
                    "ece": round(report.ece, 6),
                    "mce": round(report.mce, 6),
                    "bins": [
                        {
                            "lo": round(b.lo, 4),
                            "hi": round(b.hi, 4),
                            "count": b.count,
                            "mean_confidence": round(b.mean_confidence, 6),
                            "accuracy": round(b.accuracy, 6),
                            "gap": round(b.gap, 6),
                        }
                        for b in report.bins
                    ],
                },
                indent=2,
            )
        )
    else:
        print_report(report, args.dataset)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
