import sys
import os
import glob
import shutil
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests  # noqa E402
from common import env_root, jupyter_env, jupyter_root  # noqa E402


default_kernel = 'python3'

KERNELS = ['python3', 'julia-1.8', 'ir']


def test_python_path():
    CommonTests._test_python_path(default_kernel, env_root)


def test_which_python():
    CommonTests._test_which_python(default_kernel, env_root)


def test_env_file():
    CommonTests._test_uv_env_file(default_kernel, env_root)


def test_conda_base_env():
    CommonTests._test_conda_env_file(
        'base', f'{env_root}/base/base-lock.yml')


def test_env_vars():
    assert os.environ['DEFAULT_ENV'] == default_kernel
    assert os.environ['ENV_DIR'] == '/opt/envs'
    assert os.environ['ENV_DIR'] == env_root


def test_base_env():
    CommonTests._test_uv_env_file(jupyter_env, jupyter_root)


def test_kernels():
    """Kernel defnitions should exist"""
    CommonTests.test_kernels_exist(KERNELS)


def test_julia():
    """Julia and its kernel defnitions should exist"""
    assert 'JULIA_DEPOT_PATH' in os.environ
    jpath = os.environ['JULIA_DEPOT_PATH']
    assert os.path.exists(jpath)
    assert glob.glob(f'{jpath}/*') != 0
    version = glob.glob(f'{jpath}/environments/v*')[0].split('/')[-1][1:]
    CommonTests.test_kernels_exist([f'julia-{version}'])


def test_r():
    """R and its kernel defnitions should exist"""
    assert os.path.exists(f'{env_root}/Renv')
    assert glob.glob(f'{env_root}/Renv/*') != 0
    CommonTests.test_kernels_exist(['ir'])


def test_base_tools_exist():
    for tool in [
        'vim', 'code-server', 'tectonic', 'zip', 'gcc', 'g++', 'gfortran'
    ]:
        if not shutil.which(tool):
            pytest.fail(f'base tool {tool} cannot run')
