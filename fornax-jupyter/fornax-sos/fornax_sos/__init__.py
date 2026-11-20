# Copyright 2026, University of Maryland, All Rights Reserved
"""
`fornax_sos` package initialization.

This package provides the `fornax_Python` language plugin (`fornax_sos.kernel:fornax_Python`)
for `sos-notebook`. It is loaded automatically by `SoS_Kernel` via the
`"sos_languages"` entry points generated at install time by `setup.py`.

See `fornax_sos/kernel.py` for full documentation of:
  1. How Python object transfers (`%get` / `%put`) work between isolated Fornax
     conda/uv environments without unpickling inside `/opt/jupyter`.
  2. How installed Python kernel specs are discovered and assigned distinct
     JupyterLab sidebar colors.
  3. The compatibility shim for `SoS_Kernel.do_inspect` with modern `ipykernel`.
"""
