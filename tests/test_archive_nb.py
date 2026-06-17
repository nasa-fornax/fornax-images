import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests, change_dir  # noqa E402
from common import env_root, jupyter_env, jupyter_root  # noqa E402

notebook_dir = os.environ.get(
    'NOTEBOOK_DIR', f"{os.environ['HOME']}/fornax-notebooks")

default_kernel = 'jupyter'


KERNELS = ['py-irsa-tutorials', 'py-mast-tutorials', 'py-spherex_sdt']


def test_env_vars():
    assert os.environ['DEFAULT_ENV'] == default_kernel
    assert os.environ['ENV_DIR'] == '/opt/envs'
    assert os.environ['ENV_DIR'] == env_root


def test_base_env():
    CommonTests._test_uv_env_file(jupyter_env, jupyter_root)


def test_kernels():
    """Kernel defnitions should exist"""
    CommonTests.test_kernels_exist(KERNELS)


def test_notebooks_folder():
    assert os.path.exists(notebook_dir)
    assert os.path.exists(f'{notebook_dir}/irsa-tutorials')
    assert os.path.exists(f'{notebook_dir}/mast-tutorials')
    assert os.path.exists(f'{notebook_dir}/heasarc-tutorials')


def test_check_packages():
    for env in ['py-irsa-tutorials', 'py-mast-tutorials']:
        CommonTests._test_uv_env_file(env, env_root)
    CommonTests._test_conda_env_file('py-spherex_sdt', env_root)

# TODO: add import tests for archive notebooks.
