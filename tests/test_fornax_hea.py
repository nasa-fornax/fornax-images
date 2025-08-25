import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests, change_dir  # noqa E402
from common import env_root, jupyter_env, jupyter_root  # noqa E402

default_kernel = 'heasoft'

notebook_dir = os.environ.get('NOTEBOOK_DIR', '/home/jovyan/fornax-notebooks')
notebooks = {}


def test_python_path():
    CommonTests._test_python_path(default_kernel, env_root)


def test_which_python():
    CommonTests._test_which_python(default_kernel, env_root)


def test_env_vars():
    assert os.environ['DEFAULT_ENV'] == default_kernel
    assert os.environ['ENV_DIR'] == '/opt/envs'
    assert os.environ['ENV_DIR'] == env_root


def test_base_env():
    CommonTests._test_uv_env_file(jupyter_env, jupyter_root)


def test_conda_env():
    CommonTests._test_conda_env_file(
        'heasoft', f'{env_root}/heasoft/heasoft-lock.yml')


def test_check_packages():
    import heasoftpy # noqa 401
    import xspec  # noqa 401


def test_fversion():
    subprocess.check_call("fversion")

# TODO: add a test for running test_fversion inside a notebook


def test_ciao():
    """Tests for ciao; call separately"""
    script_dir = os.path.dirname(__file__)
    result = CommonTests.run_cmd(('micromamba run -n ciao pytest -v -s '
                                  f'{script_dir}/test_fornax_hea_ciao.py'))
    print()
    print(result.stdout)
    print()


def test_fermi():
    """Tests for fermi; call separately"""
    script_dir = os.path.dirname(__file__)
    result = CommonTests.run_cmd(('micromamba run -n fermi pytest -v -s '
                                  f'{script_dir}/test_fornax_hea_fermi.py'))
    print()
    print(result.stdout)
    print()
