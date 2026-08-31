# Copyright 2026, University of Maryland, All Rights Reserved

import sys
import os
import re

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


# Commented out since the python binaries are in /opt/envs/python
# def test_base_env():
#     CommonTests._test_uv_env_file(jupyter_env, jupyter_root)


def test_notebooks_folder():
    assert os.path.exists(notebook_dir)
    assert os.path.exists(f'{notebook_dir}/fornax-demo-notebooks')
    assert os.path.exists(f'{notebook_dir}/irsa-tutorials')
    assert os.path.exists(f'{notebook_dir}/heasarc-tutorials')
    assert os.path.exists(f'{notebook_dir}/mast-tutorials')


def test_env_dir_not_exist():
    assert not os.path.exists(os.environ['ENV_DIR'])


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
        envs += _envs

    jupyter_envs = _extract_env_vars(f'{wdir}/../fornax-jupyter/Dockerfile')
    # we can have vars in jupyter_envs but not in the other images
    assert set(envs).issubset(set(jupyter_envs))

    assert 'FORNAX_SOFTWARE_VERSION' in os.environ


def _extract_env_vars(dockerfile):
    """Extract all ENV variables from a Dockerfile"""
    env_vars = []
    with open(dockerfile, 'r') as fp:
        lines = fp.readlines()

    # Join lines that end with backslash
    combined_lines = []
    current = ''
    for line in lines:
        sline = line.strip()
        if not sline or sline.startswith('#'):
            continue
        if sline[-1] == '\\':
            current += sline[:-1] + ' '
        else:
            current += sline
            combined_lines.append(current)
            current = ''
    # now look for the ENV
    pattern = re.compile(r'^\s*ENV\s+(.*)')
    for line in combined_lines:
        match = pattern.match(line)
        if match:
            parts = match.group(1)
            for var in re.findall(r'(\S+?)(?:=)', parts):
                env_vars.append(var)
    return env_vars
