import sys
import os
import glob
import json
import subprocess

sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests, change_dir  # noqa E402
from common import env_root, jupyter_env, jupyter_root, notebook_dir  # noqa E402

default_kernel = 'ciao'

KERNELS = ['ciao']


def test_python_path():
    CommonTests._test_python_path(default_kernel, env_root)


def test_which_python():
    CommonTests._test_which_python(default_kernel, env_root)


def test_env_vars():
    # DEFAULT_ENV is jupyter because the container does not start
    # when set to ciao; something is not right in the ciao activation script
    assert os.environ['DEFAULT_ENV'] == 'jupyter'
    assert os.environ['ENV_DIR'] == '/opt/envs'
    assert os.environ['ENV_DIR'] == env_root


def test_base_env():
    CommonTests._test_uv_env_file(jupyter_env, jupyter_root)


def test_conda_env():
    CommonTests._test_conda_env_file(
        'ciao', f'{env_root}/ciao/ciao-lock.yml')


def test_kernels():
    """Kernel defnitions should exist"""
    CommonTests.test_kernels_exist(KERNELS)


def test_check_packages():
    import sherpa # noqa 401
    import ciao_contrib  # noqa 401


def test_version():
    subprocess.check_call(["ciaover"])


def test_caldb():
    assert 'CALDB' in os.environ
    assert os.environ['CALDB'] != ''
    assert 'CALDBCONFIG' in os.environ
    assert 'CALDBALIAS' in os.environ


def test_data_dir():
    """Check data directories"""
    conda_meta = glob.glob(f'{env_root}/ciao/conda-meta/ciao-?.*.json')
    assert len(conda_meta) == 1
    version = json.load(open(conda_meta[0]))['version']
    support_dir = os.environ['SUPPORT_DATA_DIR']
    assert os.path.exists(f'{support_dir}/ciao-{version}/spectral/modelData')
    assert len(glob.glob(
        f'{support_dir}/ciao-{version}/spectral/modelData/*')) != 0

    # check for symlinks
    assert os.path.exists(f'{env_root}/ciao/spectral/modelData')
    assert os.path.islink(f'{env_root}/ciao/spectral/modelData')
