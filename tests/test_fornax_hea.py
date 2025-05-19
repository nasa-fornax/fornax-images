import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests, conda_dir, env_dir  # noqa E402

notebook_dir = os.environ.get('NOTEBOOK_DIR', '/home/jovyan/notebooks')
notebooks = {}


def test_python_path():
    CommonTests._test_python_path('heasoft', is_conda=True)


def test_which_python():
    CommonTests._test_which_python('heasoft', is_conda=True)


def test_env_vars():
    assert os.environ['DEFAULT_ENV'] == 'heasoft'
    assert os.environ['ENV_DIR'] == '/opt/envs'
    assert os.environ['ENV_DIR'] == env_dir


def test_base_env():
    CommonTests._test_conda_env_file('base', f'{conda_dir}/base-lock.yml')


def test_conda_env():
    CommonTests._test_conda_env_file(
        'heasoft', f'{conda_dir}/envs/heasoft/heasoft-lock.yml')


def test_check_packages():
    import heasoftpy # noqa 401
    import xspec  # noqa 401
