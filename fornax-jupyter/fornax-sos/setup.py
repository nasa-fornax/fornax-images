# Copyright 2026, University of Maryland, All Rights Reserved
"""
Build-time setup script for `fornax-sos`.

How `sos-notebook` language discovery works (and why this script exists):
-------------------------------------------------------------------------
1. When an SoS notebook starts, `SoS_Kernel.get_supported_languages()` calls
   `importlib.metadata.entry_points(group="sos_languages")` to build a dictionary
   mapping `<entry_point_name> -> <plugin_class>`.
2. Next, `sos_notebook.subkernel.Subkernels` iterates over each registered plugin's
   `supported_kernels` dictionary (`{language_name: [kernel_spec_names...]}`) and
   `background_color` dictionary (`{language_name: "#HEX"}`).
3. Crucially:
   - `sos-notebook` assigns cell/sidebar colors in JupyterLab by *language name*
     (the keys of `supported_kernels` and `background_color`), NOT by individual
     Jupyter kernel spec name.
   - Whenever a sub-kernel is used, `SoS_Kernel` looks up its language plugin via
     `self.supported_languages[kinfo.language]`. Therefore, EVERY key in
     `fornax_Python.supported_kernels` MUST also exist as a named entry point in
     the `"sos_languages"` entry-point group.

Why we generate entry points dynamically at install time:
---------------------------------------------------------
Fornax builds Python environments across several separate images:
  - `env-core`: `python3`
  - `env-heasoft`, `env-ciao`, `env-sas`, `env-fermi`: `heasoft`, `ciao`, `sas`,
    `fermi`, `fermi-gbm`
  - `fornax-nb`: dynamically creates `py-<name>` kernels for every
    `requirements_*.txt` file found in the `fornax-demo-notebooks` repo
  - `archive-nb`: creates archive-specific `py-*` kernels

All of those kernel specs are collected into `env-assets` under `/kernels` and
copied into `/opt/jupyter/share/jupyter/kernels/` in `fornax-jupyter/Dockerfile`
before `fornax-sos` is installed. By scanning `/opt/jupyter/share/jupyter/kernels/`
here during `uv pip install /tmp/fornax-sos`, every Python environment in the
image automatically gets a matching `"sos_languages"` entry point without
developers ever having to maintain a hardcoded list of kernel names.
"""

import json
import os
from pathlib import Path
from setuptools import find_packages, setup

# Every generated entry point resolves to our `fornax_Python` subclass in
# `fornax_sos/kernel.py`.
PLUGIN_TARGET = "fornax_sos.kernel:fornax_Python"


def discover_entry_points() -> list[str]:
    """
    Scan `/opt/jupyter/share/jupyter/kernels/*/kernel.json` and return a list
    of `"<language_name> = fornax_sos.kernel:fornax_Python"` entry-point strings
    for every installed Python kernel.
    """
    # `JUPYTER_DIR` defaults to `/opt/jupyter` in Fornax images, which is where
    # all shared Jupyter kernel specs (`share/jupyter/kernels/<name>/kernel.json`)
    # are installed.
    jupyter_dir = os.environ.get("JUPYTER_DIR", "/opt/jupyter")
    kernels_root = Path(jupyter_dir) / "share" / "jupyter" / "kernels"

    # Seed the set of language names with two permanent entries:
    #
    # 1. `"Python3"`:
    #    Upstream `sos-python` registers `"Python3"` (capital P) for the standard
    #    `"python3"` (lowercase p) kernel spec. Registering `"Python3"` here
    #    ensures our `fornax_Python` class takes over for the default `python3`
    #    kernel as well, so variables can be passed between `python3` and any
    #    other Fornax Python kernel.
    #
    # 2. `"FornaxPython"`:
    #    A catch-all fallback language used in `fornax_sos/kernel.py` with the
    #    wildcard pattern `["py-*"]`. If a user creates a new `py-*` conda/venv
    #    kernel at runtime (after the image was built, so it wasn't present when
    #    `setup.py` ran), `sos-notebook` will match it to `"FornaxPython"` via
    #    `fnmatch` and still use `fornax_Python` for variable transfers.
    language_names = {"Python3", "FornaxPython"}

    if kernels_root.is_dir():
        # Sort for deterministic package metadata (`entry_points.txt`) across builds.
        for kernel_json in sorted(kernels_root.glob("*/kernel.json")):
            kernel_name = kernel_json.parent.name

            # Skip:
            # - `"sos"`: the central SoS orchestrator kernel itself (not a sub-kernel).
            # - `"python3"`: already registered above under its canonical SoS
            #   language name `"Python3"`.
            if kernel_name in {"sos", "python3"}:
                continue

            try:
                spec = json.loads(kernel_json.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                # Ignore malformed or unreadable kernel.json files rather than
                # breaking the image build.
                continue

            # Only register Python kernels (`"language": "python"`). Non-Python
            # kernels such as R (`"ir"`) and Julia (`"julia-*"`) are handled by
            # their own SoS language packages (`sos-r` and `sos-julia`).
            if spec.get("language", "").lower() == "python":
                language_names.add(kernel_name)

    # Format as setuptools entry-point specifications:
    # e.g. ["Python3 = fornax_sos.kernel:fornax_Python", "ciao = ...", ...]
    return [f"{name} = {PLUGIN_TARGET}" for name in sorted(language_names)]


setup(
    packages=find_packages(),
    entry_points={
        "sos_languages": discover_entry_points(),
    },
)
