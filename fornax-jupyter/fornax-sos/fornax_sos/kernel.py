# Copyright 2026, University of Maryland, All Rights Reserved
"""
Custom SoS language plugin (`fornax_Python`) for all Fornax Python environments.

===============================================================================
ARCHITECTURE & WHY THIS MODULE EXISTS
===============================================================================

In Fornax, the JupyterLab server and the central `SoS` orchestrator kernel live
in `/opt/jupyter`, which only contains Jupyter server packages (`jupyterlab`,
`sos-notebook`, `ipykernel`, etc.). Scientific Python packages (`astropy`,
`numpy`, `heasoftpy`, `ciao`, `fermitools`, etc.) live in separate isolated
environments under `/opt/envs/<env_name>` exposed as individual Jupyter kernels.

When using `sos-notebook` with upstream `sos-python` (`sos_python.kernel.sos_Python`),
three issues arise:

1. Passing non-builtin Python objects (e.g. `astropy.units.Quantity`) between
   sub-kernels via `%get` / `%put` fails with `ModuleNotFoundError`:
   -----------------------------------------------------------------
   When `SoS_Kernel.put_vars_to()` transfers variables from a source sub-kernel
   to a destination sub-kernel, it calls the source language plugin's
   `lan.put_vars(items, to_kernel=to_kernel_language_name)` method:

   - **Indirect path (returns a `dict`)**:
     By default, `sos_Python.put_vars()` pickles the objects inside the source
     sub-kernel, sends the pickle bytes back to the central `SoS` kernel in
     `/opt/jupyter`, and **unpickles them inside `/opt/jupyter`** (`pickle.loads`)
     to store them in `env.sos_dict` before forwarding them to `to_kernel`.
     Because `/opt/jupyter` does not have `astropy` (or other domain libraries)
     installed, `pickle.loads` inside `/opt/jupyter` immediately crashes with:
     `Failed to import variables [...]: No module named 'astropy'`.

   - **Direct Python-to-Python path (returns a `str`)**:
     `sos_Python.put_vars()` has a fast path specifically for Python-to-Python
     transfers: instead of unpickling inside `/opt/jupyter` and returning a `dict`,
     it returns a Python code string:
         `f"import pickle;globals().update(pickle.loads({dumped_bytes}))"`
     When `SoS_Kernel.put_vars_to()` receives a `str` from `put_vars()`, it
     switches directly to the destination sub-kernel and executes that code
     string inside the destination sub-kernel's Python interpreter. The central
     `SoS` kernel in `/opt/jupyter` only passes the raw bytes string through and
     never unpickles anything!
     However, upstream `sos_Python.put_vars()` hardcodes the check:
         `if self.kernel_name == 'python3' and to_kernel == 'Python3':`
     so custom Python kernels like `heasoft`, `ciao`, `sas`, or `py-*` never hit
     that direct path unless we subclass `sos_Python`.

2. All Python sub-kernels get the same yellow sidebar color in JupyterLab:
   -----------------------------------------------------------------------
   `sos-notebook` (`sos_notebook.subkernel.Subkernels`) keys cell/sidebar
   background colors by *SoS language name* (`background_color = {lang: "#HEX"}`),
   not by kernel spec name. If all Python kernels are grouped under the single
   `"Python3"` language name, every Python sub-kernel in a notebook gets the
   exact same yellow color (`#FFD91A`), making it hard to tell at a glance which
   cell belongs to `heasoft` vs. `ciao` vs. `sas`.
   By giving each discovered Python kernel its own language name in
   `supported_kernels` and `background_color` (matching the entry points created
   by `setup.py`), each environment gets its own distinct color in the UI.

3. `Shift+Tab` docstring inspection throws `TypeError` in `SoS_Kernel.do_inspect`:
   -------------------------------------------------------------------------------
   Modern `ipykernel` passes 4 arguments (`code, cursor_pos, detail_level, omit_sections`)
   to `Kernel.do_inspect()`, whereas upstream `sos-notebook` (<= 0.24.4) defines
   `SoS_Kernel.do_inspect(self, code, cursor_pos, detail_level=0)` with only 3
   arguments. We apply a signature-guarded compatibility wrapper at import time.
"""

import inspect
import json
import os
from pathlib import Path
import pickle

from sos.utils import env
from sos_notebook.kernel import SoS_Kernel
from sos_python.kernel import sos_Python


# =============================================================================
# 1. Compatibility Shim for `SoS_Kernel.do_inspect`
# =============================================================================

def _patch_sos_kernel_do_inspect() -> None:
    """
    Wrap `SoS_Kernel.do_inspect` if it does not yet accept `omit_sections`.

    What triggers this:
    -------------------
    In JupyterLab, pressing `Shift+Tab`, hovering with the Contextual Help
    inspector open, or triggering inline signature tooltips sends a Jupyter
    `inspect_request` message to the active kernel.

    Why it fails in upstream `sos-notebook`:
    ----------------------------------------
    In `ipykernel >= 6.x`, `ipykernel.kernelbase.Kernel.inspect_request` calls:
        `self.do_inspect(code, cursor_pos, detail_level, omit_sections)`
    passing 5 positional arguments including `self`.
    Upstream `sos-notebook` (<= 0.24.4) defines:
        `def do_inspect(self, code, cursor_pos, detail_level=0):`
    which only accepts 3 to 4 positional arguments (including `self`), raising:
        `TypeError: SoS_Kernel.do_inspect() takes from 3 to 4 positional arguments but 5 were given`

    What happens when upstream fixes this:
    --------------------------------------
    Before patching, we inspect `SoS_Kernel.do_inspect`'s parameter list via
    `inspect.signature`. If a future version of `sos-notebook` updates
    `do_inspect` to accept `omit_sections` (5+ parameters) or `*args`/`**kwargs`,
    `len(params) < 5 and not accepts_varargs` evaluates to `False` and this
    function becomes a complete no-op.
    """
    sig = inspect.signature(SoS_Kernel.do_inspect)
    params = list(sig.parameters.values())

    # Check if upstream added `*args` or `**kwargs` to `do_inspect`.
    accepts_varargs = any(
        p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        for p in params
    )

    # `params` includes `self`, so `< 5` means `omit_sections` is not accepted yet.
    if len(params) < 5 and not accepts_varargs:
        _orig_do_inspect = SoS_Kernel.do_inspect

        def _do_inspect_compat(
            self, code, cursor_pos, detail_level=0, omit_sections=()
        ):
            # Forward the 3 arguments that upstream `SoS_Kernel.do_inspect` expects.
            return _orig_do_inspect(self, code, cursor_pos, detail_level)

        SoS_Kernel.do_inspect = _do_inspect_compat


# Apply the `do_inspect` check/shim as soon as `SoS_Kernel` loads this plugin.
_patch_sos_kernel_do_inspect()


# =============================================================================
# 2. Kernel Auto-Discovery & Sidebar Color Assignment
# =============================================================================

# Explicit, stable sidebar colors for well-known Fornax Python environments so
# that the core and High Energy Astrophysics (HEA) kernels always have the same
# recognizable colors across sessions and builds.
FIXED_KERNEL_COLORS = {
    "Python3": "#FFD91A",       # Gold / standard SoS Python yellow
    "heasoft": "#66C2A5",       # Teal (ColorBrewer Set2)
    "ciao": "#8DA0CB",          # Periwinkle blue (ColorBrewer Set2)
    "sas": "#FC8D62",           # Coral orange (ColorBrewer Set2)
    "fermi": "#E78AC3",         # Orchid pink (ColorBrewer Set2)
    "fermi-gbm": "#A6D854",     # Lime green (ColorBrewer Set2)
    "FornaxPython": "#E5C494",  # Sand (fallback for runtime user-created `py-*` kernels)
}

# Curated palette of visually distinct, light-to-medium pastel hex colors used
# for dynamically discovered notebook kernels (such as `py-agn_zoo`,
# `py-light_curve_collector`, `py-irsa-tutorials`, etc. from `fornax-nb` and
# `archive-nb`). Light/medium tones are used so dark text in the JupyterLab
# kernel selector and cell prompt remains legible.
DYNAMIC_COLOR_PALETTE = [
    "#80B1D3",  # Sky blue
    "#FDB462",  # Apricot
    "#B3DE69",  # Light olive green
    "#FCCDE5",  # Soft rose
    "#BC80BD",  # Lavender purple
    "#CCEBC5",  # Mint green
    "#FFED6F",  # Pale yellow
    "#BEBADA",  # Lilac
    "#FB8072",  # Salmon
    "#8DD3C7",  # Aqua
    "#D9D9D9",  # Warm silver
    "#F4CAE4",  # Pastel magenta
    "#CBD5E8",  # Powder blue
    "#FDCDAC",  # Peach
    "#E6F5C9",  # Pale lime
    "#FFF2AE",  # Buttercream
]


def _discover_python_kernels() -> tuple[dict[str, list[str]], dict[str, str], set[str]]:
    """
    Scan `/opt/jupyter/share/jupyter/kernels/*/kernel.json` at import time and
    construct the three data structures needed by `fornax_Python`:

    Returns
    -------
    supported_kernels : dict[str, list[str]]
        Maps `<SoS language name> -> [<Jupyter kernel spec name or glob>]`.
        Used by `sos_notebook.subkernel.Subkernels` to associate each installed
        Jupyter kernel with an SoS language name.
    background_color : dict[str, str]
        Maps `<SoS language name> -> "#RRGGBB"`.
        Used by `sos-notebook` and `jupyterlab-sos` to color the cell sidebar
        and kernel badge in JupyterLab.
    languages : set[str]
        The set of all SoS language names managed by `fornax_Python`. Used by
        `fornax_Python.put_vars()` to know whether `to_kernel` is another
        Fornax Python sub-kernel that supports direct pickle transfer.
    """
    jupyter_dir = os.environ.get("JUPYTER_DIR", "/opt/jupyter")
    kernels_root = Path(jupyter_dir) / "share" / "jupyter" / "kernels"

    # Always include the default `Python3` language -> `python3` kernel mapping.
    # Note the capitalization difference required by `sos-notebook`:
    #   - Language name: `"Python3"` (capital P)
    #   - Kernel spec directory name: `"python3"` (lowercase p)
    supported_kernels: dict[str, list[str]] = {
        "Python3": ["python3"],
    }
    background_color: dict[str, str] = {
        "Python3": FIXED_KERNEL_COLORS["Python3"],
    }

    # Find all other Python kernel specs installed in `/opt/jupyter/share/jupyter/kernels`.
    discovered_names: list[str] = []
    if kernels_root.is_dir():
        # Sort kernel directories alphabetically so palette color assignment is
        # deterministic for a given set of installed kernels.
        for kernel_json in sorted(kernels_root.glob("*/kernel.json")):
            kernel_name = kernel_json.parent.name

            # Skip the central `"sos"` kernel and `"python3"` (already handled above).
            if kernel_name in {"sos", "python3"}:
                continue

            try:
                spec = json.loads(kernel_json.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue

            # Only include kernels whose `kernel.json` declares `"language": "python"`.
            # R (`"ir"`) and Julia (`"julia-*"`) kernels are left to `sos-r` and `sos-julia`.
            if spec.get("language", "").lower() == "python":
                discovered_names.append(kernel_name)

    # Register each discovered Python kernel under a language name equal to its
    # kernel name (matching the entry points generated by `setup.py`), and assign
    # it either its fixed color (if in `FIXED_KERNEL_COLORS`) or the next color
    # from `DYNAMIC_COLOR_PALETTE`.
    palette_idx = 0
    for kernel_name in discovered_names:
        supported_kernels[kernel_name] = [kernel_name]
        if kernel_name in FIXED_KERNEL_COLORS:
            background_color[kernel_name] = FIXED_KERNEL_COLORS[kernel_name]
        else:
            background_color[kernel_name] = DYNAMIC_COLOR_PALETTE[
                palette_idx % len(DYNAMIC_COLOR_PALETTE)
            ]
            palette_idx += 1

    # Add `"FornaxPython": ["py-*"]` LAST in `supported_kernels`.
    #
    # Why this exists and why order matters:
    # `sos_notebook.subkernel.Subkernels` first matches exact kernel names in
    # `supported_kernels`, and then falls back to `fnmatch.fnmatch(spec, pattern)`
    # wildcard patterns. For all `py-*` kernels that existed at image build time,
    # their exact entries above take precedence (giving each its own language
    # name and distinct color). If a user creates a new `py-*` kernel at runtime
    # inside a running container (so it has no build-time entry point of its own),
    # it matches this `"FornaxPython": ["py-*"]` wildcard (whose `"FornaxPython"`
    # entry point WAS registered at build time in `setup.py`), allowing `%get`
    # and `%put` object transfers to work with user-created kernels too.
    supported_kernels["FornaxPython"] = ["py-*"]
    background_color["FornaxPython"] = FIXED_KERNEL_COLORS["FornaxPython"]

    return supported_kernels, background_color, set(supported_kernels.keys())


SUPPORTED_KERNELS, BACKGROUND_COLOR, FORNAX_PYTHON_LANGUAGES = _discover_python_kernels()


# =============================================================================
# 3. `fornax_Python` Language Plugin Class
# =============================================================================

class fornax_Python(sos_Python):
    """
    SoS language plugin for all Fornax Python sub-kernels.

    Subclasses `sos_python.kernel.sos_Python` so that we inherit all standard
    SoS Python behavior (`expand`, `preview`, `sessioninfo`, init statements,
    etc.) without forking `sos-python`, while overriding only the kernel map,
    color map, and variable transfer methods (`get_vars` and `put_vars`).
    """

    # Class attributes read by `sos_notebook` when registering languages/subkernels.
    supported_kernels = SUPPORTED_KERNELS
    background_color = BACKGROUND_COLOR

    async def get_vars(self, names, as_var=None):
        """
        Transfer variables from the central `SoS` workflow dictionary
        (`env.sos_dict`) into this Python sub-kernel.

        Why this override is needed:
        ----------------------------
        Upstream `sos_Python.get_vars()` checks `if self.kernel_name == 'python3':`
        before pickling variables from `env.sos_dict` into the sub-kernel, and
        otherwise falls through to a path that expects another language plugin.
        Overriding `get_vars` here removes that `self.kernel_name == 'python3'`
        restriction so any Fornax Python sub-kernel (`heasoft`, `ciao`, `py-*`,
        etc.) can receive variables from the central `SoS` kernel.
        """
        for name in names:
            # If the user passed `--as <new_name>`, bind the variable under `as_var`
            # in the destination sub-kernel; otherwise keep its original `name`.
            target_name = as_var if as_var else name

            # Serialize `{target_name: value}` from the central SoS dictionary
            # and execute `globals().update(pickle.loads(...))` silently inside
            # the sub-kernel (`silent=True, store_history=False`).
            dumped = pickle.dumps({target_name: env.sos_dict[name]})
            stmt = f"globals().update(pickle.loads({dumped!r}))\n"
            await self.sos_kernel.run_cell(
                stmt,
                True,
                False,
                on_error=f"Failed to get variable {name} from SoS to {self.kernel_name}",
            )

    def put_vars(self, items, to_kernel=None, as_var=None):
        """
        Transfer variables (`items`) from this Python sub-kernel to `to_kernel`
        (invoked by both `%put` and `%get var --from <other_kernel>`).

        How `SoS_Kernel.put_vars_to()` calls this method:
        -------------------------------------------------
        When transferring variables from sub-kernel A (e.g. `heasoft`) to
        sub-kernel B (e.g. `ciao`), `SoS_Kernel` looks up sub-kernel B's
        *language name* (`to_kernel = "ciao"`) and calls sub-kernel A's language
        instance:
            `lan.put_vars(items, to_kernel="ciao", as_var=as_var)`

        How upstream `sos_Python.put_vars()` behaves:
        ---------------------------------------------
        Inside `sos_Python.put_vars()`, it executes a helper expression inside
        the source sub-kernel to pickle the requested variables (`items`) into
        a `bytes` literal, and then checks:
            `if self.kernel_name == 'python3' and to_kernel == 'Python3':`
              -> returns `f"import pickle;globals().update(pickle.loads({response}))"`
                 (a `str` that `SoS_Kernel` executes directly in the destination
                 sub-kernel, completely bypassing `/opt/jupyter`!)
            `else:`
              -> calls `pickle.loads(...)` inside `/opt/jupyter` to return a `dict`
                 (which FAILS whenever the pickled object belongs to a library
                 like `astropy` that is installed in the sub-kernels but NOT in
                 `/opt/jupyter`).

        How this override works:
        ------------------------
        Whenever `to_kernel` is another Fornax Python sub-kernel
        (`to_kernel in FORNAX_PYTHON_LANGUAGES`), we temporarily set
        `self.kernel_name = "python3"` and `to_kernel = "Python3"` for the
        duration of the `super().put_vars(...)` call, restoring `self.kernel_name`
        in the `finally` block. That way:
          - Python-to-Python transfers between ANY two Fornax Python environments
            always take upstream's direct `str` execution path (so `astropy`
            Quantities, NumPy arrays, tables, etc. transfer directly between
            sub-kernels without `/opt/jupyter` ever unpickling them).
          - Transfers from a Fornax Python kernel to a non-Python kernel (such
            as `R`, `Julia`, or the central `SoS` kernel where `to_kernel` is
            `None` or `"R"` / `"Julia"`) still take upstream's standard cross-language
            conversion path untouched.
        """
        orig_name = self.kernel_name
        try:
            if to_kernel in FORNAX_PYTHON_LANGUAGES:
                self.kernel_name = "python3"
                to_kernel = "Python3"
            return super().put_vars(items, to_kernel=to_kernel, as_var=as_var)
        finally:
            # Always restore the sub-kernel's real kernel_name (e.g. "heasoft")
            # even if serialization raises an exception.
            self.kernel_name = orig_name
