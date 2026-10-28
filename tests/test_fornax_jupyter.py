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
