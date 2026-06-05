"""
Canonical-source discovery for the Python reference implementation.

The SDL reference adapters *wrap* the canonical detectors — they never copy or
reimplement them. Those detectors live in sibling repositories:

  * rrt-advocate  -> ``<repo>/src``       (package ``crisis``)
  * sleepwalker   -> ``<repo>``           (package ``sleepwalker_protocol``)

Resolution order for each:
  1. Explicit env var (``RRT_ADVOCATE_SRC`` / ``SLEEPWALKER_ROOT``)
  2. Sibling directory next to the nlt-sdl checkout

If a source cannot be found or imported, the adapter raises — and the
fail-closed boundary turns that into an escalating ``failClosed`` result rather
than a silent green. Missing canon is therefore *safe by construction*.
"""

from __future__ import annotations

import os
import pathlib
import sys

# .../nlt-sdl/reference/python/nlt_sdl/_canon.py
#   parents[0]=nlt_sdl  [1]=python  [2]=reference  [3]=nlt-sdl  [4]=<siblings>
_SIBLINGS = pathlib.Path(__file__).resolve().parents[4]


def rrta_src() -> str:
    env = os.environ.get("RRT_ADVOCATE_SRC")
    if env:
        return env
    return str(_SIBLINGS / "rrt-advocate" / "src")


def sleepwalker_root() -> str:
    env = os.environ.get("SLEEPWALKER_ROOT")
    if env:
        return env
    return str(_SIBLINGS / "sleepwalker")


def _ensure_on_path(path: str) -> None:
    if path and os.path.isdir(path):
        if path not in sys.path:
            sys.path.insert(0, path)
    else:
        raise ModuleNotFoundError(f"canonical source not found at: {path}")


def ensure_rrta() -> None:
    _ensure_on_path(rrta_src())


def ensure_sleepwalker() -> None:
    _ensure_on_path(sleepwalker_root())
