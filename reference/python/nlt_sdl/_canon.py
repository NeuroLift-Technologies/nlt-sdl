"""
Canonical-source discovery for the Python reference implementation.

The SDL reference adapters *wrap* the canonical detectors — they never copy or
reimplement them. The canonical detectors are consumed as PUBLISHED PyPI
packages:

  * rrt-advocate  -> PyPI package ``rrt_advocate``   (provides ``CrisisDetector``)
  * sleepwalker   -> PyPI package ``sleepwalker-protocol`` (provides ``sleepwalker_protocol``)

Resolution order for each:
  1. Published PyPI packages (preferred — ``pip install rrt-advocate
     sleepwalker-protocol``)
  2. Sibling source checkouts (legacy local-dev fallback via env var or
     adjacent directory). The restructured canon repos place the Python package
     under ``src/`` (e.g. ``rrt-advocate/src/rrt_advocate/``), so the fallback
     adds ``src/`` to ``sys.path``.

If a package cannot be found by either means, the adapter raises — and the
fail-closed boundary turns that into an escalating ``failClosed`` result rather
than a silent green. Missing canon is therefore *safe by construction*.

The bundled ``config/crisis_thresholds.yaml`` is read via ``importlib.resources``
from the installed PyPI package (see ``rrta_adapter.load_tier_ranges``).
"""

from __future__ import annotations

import importlib
import os
import pathlib
import sys

# .../nlt-sdl/reference/python/nlt_sdl/_canon.py
#   parents[0]=nlt_sdl  [1]=python  [2]=reference  [3]=nlt-sdl  [4]=<siblings>
_SIBLINGS = pathlib.Path(__file__).resolve().parents[4]


def _ensure_import(pkg_name: str, env_var: str, *src_candidates: str) -> None:
    """Ensure a canonical package is importable.

    Tries the published PyPI package first. Falls back to adding legacy source
    checkout paths (env var or sibling ``src/`` dirs) to ``sys.path``.

    Raises ``ModuleNotFoundError`` if neither works.
    """
    # 1. Try the published PyPI package.
    try:
        importlib.import_module(pkg_name)
        return
    except ImportError:
        pass

    # 2. Fall back to sibling source checkout.
    for candidate in (
        c for c in [os.environ.get(env_var)] + list(src_candidates) if c
    ):
        if os.path.isdir(candidate):
            if candidate not in sys.path:
                sys.path.insert(0, candidate)
            try:
                importlib.import_module(pkg_name)
                return
            except ImportError:
                pass

    pip_name = pkg_name.replace("_", "-")
    raise ModuleNotFoundError(
        f"Canonical package '{pkg_name}' not found. Install it with "
        f"`pip install {pip_name}`, or set {env_var} to the source checkout."
    )


def rrta_src() -> str:
    """Return the rrt-advocate source path (legacy, for local-dev YAML loading).

    With the PyPI package installed, YAML loading uses ``importlib.resources``
    instead — see ``rrta_adapter.load_tier_ranges``.
    """
    env = os.environ.get("RRT_ADVOCATE_SRC")
    if env:
        return env
    return str(_SIBLINGS / "rrt-advocate" / "src")


def sleepwalker_root() -> str:
    """Return the sleepwalker source path (legacy local-dev fallback)."""
    env = os.environ.get("SLEEPWALKER_ROOT")
    if env:
        return env
    return str(_SIBLINGS / "sleepwalker" / "src")


def ensure_rrta() -> None:
    """Ensure the canonical rrt-advocate detector is importable (PyPI or source)."""
    _ensure_import(
        "rrt_advocate",
        "RRT_ADVOCATE_SRC",
        str(_SIBLINGS / "rrt-advocate" / "src"),
    )


def ensure_sleepwalker() -> None:
    """Ensure the canonical sleepwalker detector is importable (PyPI or source)."""
    _ensure_import(
        "sleepwalker_protocol",
        "SLEEPWALKER_ROOT",
        str(_SIBLINGS / "sleepwalker" / "src"),
    )
