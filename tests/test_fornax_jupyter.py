# Copyright 2026, University of Maryland, All Rights Reserved

import sys
import os
import re
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests  # noqa E402
from common import env_root, jupyter_env, jupyter_root  # noqa E402
from test_fornax_nb import notebook_dir  # noqa E402


default_kernel = 'python3'


def test_env_vars():
    assert os.environ['DEFAULT_ENV'] == default_kernel
    assert os.environ['ENV_DIR'] == '/opt/envs'
    assert os.environ['ENV_DIR'] == env_root
    for var in [
        'DEFAULT_ENV', 'JUPYTER_DIR', 'MAMBA_ROOT_PREFIX', 'NOTEBOOK_DIR',
        'SUPPORT_DATA_DIR', 'ENV_DIR',
        'NB_USER', 'NB_UID', 'NB_GID',
        'PYTHON_VERSION', 'CACHE_DIR',
        # from misc-setup.sh
        'USER_ENV_DIR', 'UV_PYTHON_INSTALL_DIR', 'CONDA_ENVS_PATH',
        'CODE_EXECUTABLE', 'CODE_EXTENSIONSDIR', 'FIREFLY_URL',
        'DASK_DISTRIBUTED__DASHBOARD__LINK', 'FORNAX_SOFTWARE_VERSION'
    ]:
        assert var in os.environ
    assert os.environ['CODE_EXECUTABLE'] == 'code-server'


def test_base_env():
    CommonTests._test_uv_env_file(jupyter_env, jupyter_root)


def test_notebooks_folder():
    assert os.path.exists(notebook_dir)
    assert os.path.exists(f'{notebook_dir}/fornax-demo-notebooks')
    assert os.path.exists(f'{notebook_dir}/irsa-tutorials')
    assert os.path.exists(f'{notebook_dir}/heasarc-tutorials')
    assert os.path.exists(f'{notebook_dir}/mast-tutorials')

# commented out because we need envdir for the python binary
# def test_env_dir_not_exist():
#     assert not os.path.exists(os.environ['ENV_DIR'])


def test_support_data_dirs():
    for dir_name in ['SUPPORT_DATA_DIR', 'SUPPORT_DATA_MOUNT']:
        assert dir_name in os.environ, f'{dir_name} not set in environment'

    data_dir = Path(os.environ['SUPPORT_DATA_DIR'])
    mount_dir = Path(os.environ['SUPPORT_DATA_MOUNT'])

    assert mount_dir.exists()
    assert data_dir.exists()
    assert data_dir.is_symlink()
    assert data_dir.resolve() == mount_dir


def test_notebook_folders_group_writable():
    """Notebook folders are group-writable (group 100) at build time"""
    import stat
    for root, dirs, files in os.walk(notebook_dir):
        st = os.stat(root)
        assert st.st_gid == 100, f'{root}: gid={st.st_gid}, expected 100'
        assert st.st_mode & stat.S_IWGRP, f'{root}: not group-writable'


def test_env_vars_from_other_images():
    """ensure all variables defined in fornax-base and subsequent images
    are propagated to fornax-slim
    """
    images = [
        'jupyter-base', 'fornax-base', 'fornax-nb', 'archive-nb',
        'env-core', 'env-heasoft', 'env-ciao', 'env-fermi', 'env-sas'
    ]
    wdir = os.path.dirname(__file__)
    envs = []
    for image in images:
        _envs = _extract_env_vars(f'{wdir}/../{image}/Dockerfile')
        envs += list(_envs.keys())

    jupyter_envs = _extract_env_vars(f'{wdir}/../fornax-jupyter/Dockerfile')
    jupyter_envs = list(jupyter_envs.keys())
    # we can have vars in jupyter_envs but not in the other images
    assert set(envs).issubset(set(jupyter_envs))

    assert 'FORNAX_SOFTWARE_VERSION' in os.environ


def test_env_vars_values_from_other_images():
    """ensure key variables defined in jupyter-base are the same
    in fornax-jupyter"""
    images = ['jupyter-base', 'fornax-base', 'fornax-jupyter']
    wdir = os.path.dirname(__file__)
    envs = {}
    for image in images:
        _envs = _extract_env_vars(f'{wdir}/../{image}/Dockerfile')
        envs[image] = _envs

    jupyter_base_envs = envs['jupyter-base']
    jupyter_base_envs.update(envs['fornax-base'])
    fornax_jupyter_envs = envs['fornax-jupyter']

    for key in jupyter_base_envs:
        if key in ['PATH', 'DEFAULT_ENV']:
            continue
        assert key in fornax_jupyter_envs, f"{key} missing in fornax-jupyter"
        assert jupyter_base_envs[key] == fornax_jupyter_envs[key], (
            f"{key} value mismatch: jupyter-base={jupyter_base_envs[key]}, "
            f"fornax-jupyter={fornax_jupyter_envs[key]}"
        )


def test_jupyter_env_settings():
    """Check the env vars that control jupyter settings"""
    for name in [
        'JUPYTER_RUNTIME_DIR', 'JUPYTER_DATA_DIR',
        'JUPYTER_CONFIG_DIR', 'IPYTHONDIR'
    ]:
        assert name in os.environ
        assert os.environ[name] == '/scratch/.jupyter'


def test_sos_kernel_registered():
    """Checks to see if the SoS kernel is registered"""
    CommonTests.test_kernels_exist(['sos'])


def test_sos_notebook_basic():
    """Check if we can import sos_notebook in the Jupyter environment"""
    imp_cmd = (
        f"{jupyter_root}/{jupyter_env}/bin/python -c 'import sos_notebook'"
    )
    CommonTests.run_cmd(imp_cmd)


def test_fornax_sos_languages_registered():
    """
    Verify that the `fornax-sos` package dynamically registered an SoS language
    entry point, kernel mapping, and distinct sidebar color for every Python
    kernel present in `/opt/jupyter/share/jupyter/kernels/`.

    Why this matters:
    -----------------
    `sos-notebook` requires every sub-kernel language name to have:
      1. An entry point in `importlib.metadata.entry_points(group="sos_languages")`
      2. A corresponding key in `fornax_Python.supported_kernels`
      3. A corresponding `#RRGGBB` hex color in `fornax_Python.background_color`
    If any Python kernel in `/opt/jupyter/share/jupyter/kernels/` is missing
    from these structures, either `%get`/`%put` variable passing of scientific
    objects (like Astropy Quantities) will fail by trying to unpickle inside
    `/opt/jupyter`, or the kernel will fall back to the default yellow color.
    """
    import json
    from importlib.metadata import entry_points
    from fornax_sos.kernel import fornax_Python

    kernels_root = Path(f"{jupyter_root}/{jupyter_env}/share/jupyter/kernels")
    assert kernels_root.is_dir(), f"Kernels directory missing: {kernels_root}"

    # 1. Scan `/opt/jupyter/share/jupyter/kernels/*/kernel.json` to find every
    # Python kernel that was copied into `fornax-jupyter` from `env-assets`.
    # We skip `sos` itself because it is the central orchestrator kernel rather
    # than a Python sub-kernel.
    python_kernels = set()
    for kernel_json in kernels_root.glob("*/kernel.json"):
        kernel_name = kernel_json.parent.name
        if kernel_name == "sos":
            continue
        spec = json.loads(kernel_json.read_text(encoding="utf-8"))
        if spec.get("language", "").lower() == "python":
            python_kernels.add(kernel_name)

    # Sanity-check that the standard `python3` kernel and the High Energy
    # Astrophysics (HEA) kernels are present in the kernel specs directory.
    assert "python3" in python_kernels
    for hea_kernel in ("heasoft", "ciao", "sas", "fermi"):
        assert hea_kernel in python_kernels, (
            f"Expected HEA kernel '{hea_kernel}' in {kernels_root}"
        )

    # 2. Query all installed `"sos_languages"` package entry points in `/opt/jupyter`.
    sos_eps = {
        ep.name: ep.value for ep in entry_points(group="sos_languages")
    }

    # Verify that the non-Python language plugins (`sos-r` and `sos-julia`) are
    # also registered alongside our Python languages.
    assert "R" in sos_eps, "sos-r language entry point 'R' is not registered"
    assert "Julia" in sos_eps, (
        "sos-julia language entry point 'Julia' is not registered"
    )

    # 3. Build the expected set of SoS language names managed by `fornax-sos`:
    # - The `python3` kernel spec uses the canonical SoS language name `Python3`
    #   (capital P).
    # - Every other discovered Python kernel (`heasoft`, `ciao`, `py-*`, etc.)
    #   uses its own kernel name as its SoS language name.
    # - `FornaxPython` is the wildcard (`py-*`) fallback language for any kernel
    #   a user creates at runtime after the image was built.
    expected_fornax_langs = (
        (python_kernels - {"python3"}) | {"Python3", "FornaxPython"}
    )
    for lang in expected_fornax_langs:
        # Must have a package entry point pointing to `fornax_Python`
        assert lang in sos_eps, (
            f"Python kernel language '{lang}' missing from sos_languages "
            f"entry points"
        )
        assert sos_eps[lang] == "fornax_sos.kernel:fornax_Python", (
            f"Expected '{lang}' to point to fornax_sos.kernel:fornax_Python, "
            f"got '{sos_eps[lang]}'"
        )
        # Must be present in `fornax_Python.supported_kernels`
        assert lang in fornax_Python.supported_kernels, (
            f"'{lang}' missing from fornax_Python.supported_kernels"
        )
        # Must have a valid 6-digit hex color in `fornax_Python.background_color`
        color = fornax_Python.background_color.get(lang, "")
        assert re.match(r"^#[0-9A-Fa-f]{6}$", color), (
            f"Invalid or missing hex background_color for '{lang}': {color!r}"
        )

    # 4. Verify that the core and HEA kernels each have their own distinct
    # sidebar color so cells from different missions/environments are visually
    # distinguishable in JupyterLab.
    hea_langs = ["Python3", "heasoft", "ciao", "sas", "fermi", "fermi-gbm"]
    present_hea_colors = [
        fornax_Python.background_color[k]
        for k in hea_langs
        if k in fornax_Python.background_color
    ]
    assert len(present_hea_colors) == len(set(present_hea_colors)), (
        f"Expected distinct colors for {hea_langs}, got {present_hea_colors}"
    )


def test_fornax_sos_put_vars_and_inspect_shim():
    """
    Verify the two runtime behavioral overrides in `fornax_sos.kernel`:

      1. `SoS_Kernel.do_inspect` compatibility shim:
         Modern `ipykernel` calls `self.do_inspect(code, cursor_pos, detail_level, omit_sections)`
         with 5 positional arguments (including `self`) when a user presses
         Shift+Tab in JupyterLab, whereas upstream `sos-notebook` (<= 0.24.4)
         only accepts 4. Verify that importing `fornax_sos.kernel` ensures
         `SoS_Kernel.do_inspect` accepts all 5 positional arguments.

      2. Direct sub-kernel-to-sub-kernel pickle transfer in `fornax_Python.put_vars`:
         When transferring variables between two Fornax Python kernels (e.g.
         from `heasoft` to `ciao`), `put_vars` must return a `str` containing
         `import pickle;globals().update(pickle.loads(...))` (which `SoS_Kernel`
         executes directly inside the destination sub-kernel) rather than a
         `dict` (which would unpickle inside `/opt/jupyter` and fail on packages
         like `astropy` that aren't installed in `/opt/jupyter`).
    """
    import inspect
    from unittest.mock import MagicMock
    from sos_notebook.kernel import SoS_Kernel
    from fornax_sos.kernel import fornax_Python

    # 1. Check that `SoS_Kernel.do_inspect` accepts 5 positional arguments
    # (`self, code, cursor_pos, detail_level, omit_sections`) or `*args`.
    sig = inspect.signature(SoS_Kernel.do_inspect)
    params = list(sig.parameters.values())
    accepts_varargs = any(
        p.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        )
        for p in params
    )
    assert len(params) >= 5 or accepts_varargs, (
        f"SoS_Kernel.do_inspect signature {sig} does not accept 5 positional "
        f"arguments (self, code, cursor_pos, detail_level, omit_sections)"
    )

    # 2. Mock the `SoS_Kernel` instance used by `sos_Python.put_vars` so we can
    # test `fornax_Python.put_vars` without needing to launch live sub-kernels.
    # `sos_Python.put_vars` calls `self.sos_kernel.get_response(...)` to ask the
    # source sub-kernel for the pickled bytes representation of the variables;
    # here we return an empty pickled dict `b'\x80\x04}\x94.'`.
    mock_sos_kernel = MagicMock()
    mock_sos_kernel.get_response.return_value = [
        (
            "execute_result",
            {"data": {"text/plain": "repr(b'\\x80\\x04}\\x94.')"}},
        )
    ]

    # Instantiate `fornax_Python` as the `heasoft` sub-kernel and transfer a
    # variable `pingu` to the `ciao` sub-kernel.
    plugin = fornax_Python(mock_sos_kernel, kernel_name="heasoft")
    result = plugin.put_vars(["pingu"], to_kernel="ciao")

    # Because both `heasoft` and `ciao` are in `FORNAX_PYTHON_LANGUAGES`,
    # `put_vars` must take the direct Python-to-Python path and return a Python
    # statement string (`str`) to execute in `ciao`, NOT an unpickled `dict`.
    assert isinstance(result, str), (
        f"Expected direct Python statement string from put_vars, got "
        f"{type(result)}"
    )
    assert "pickle.loads" in result

    # Verify that `put_vars` restored `plugin.kernel_name` back to `"heasoft"`
    # after temporarily aliasing it to `"python3"` during `super().put_vars()`.
    assert plugin.kernel_name == "heasoft", (
        "fornax_Python.put_vars did not restore self.kernel_name after transfer"
    )




def _extract_env_vars(dockerfile):
    """Extract all ENV variables (names and values) from a Dockerfile"""
    env_vars = {}
    with open(dockerfile, 'r') as fp:
        lines = fp.readlines()

    # Join lines that end with backslash
    combined_lines = []
    current = ''
    for line in lines:
        sline = line.strip()
        if not sline or sline.startswith('#'):
            continue
        if sline.endswith('\\'):
            current += sline[:-1] + ' '
        else:
            current += sline
            combined_lines.append(current)
            current = ''

    # Regex to find the start of an ENV instruction
    pattern = re.compile(r'^\s*ENV\s+(.*)')
    # Regex to parse key=value formats, handling quoted and unquoted values
    kv_pattern = re.compile(r'([a-zA-Z_]\w*)=("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'|[^\s]+)')  # noqa

    for line in combined_lines:
        match = pattern.match(line)
        if match:
            parts = match.group(1).strip()

            # Check if it's the `ENV key value` (legacy) format
            # or `ENV key=value` format
            first_word = parts.split()[0] if parts.split() else ''

            if '=' not in first_word:
                # Legacy format: ENV key value (value is everything
                # after the first space)
                split_parts = parts.split(None, 1)
                if len(split_parts) == 2:
                    key, val = split_parts
                    # Strip optional surrounding quotes
                    if (
                        (val.startswith('"') and val.endswith('"')) or
                        (val.startswith("'") and val.endswith("'"))
                    ):
                        val = val[1:-1]
                    env_vars[key] = val
                elif len(split_parts) == 1:
                    env_vars[split_parts[0]] = ""
            else:
                # key=value format (allows multiple pairs on one line)
                for kv_match in kv_pattern.finditer(parts):
                    key = kv_match.group(1)
                    val = kv_match.group(2)

                    # Strip surrounding quotes if present
                    if (
                        (val.startswith('"') and val.endswith('"')) or
                        (val.startswith("'") and val.endswith("'"))
                    ):
                        val = val[1:-1]

                    env_vars[key] = val

    return env_vars
