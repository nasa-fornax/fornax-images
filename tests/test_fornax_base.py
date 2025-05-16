import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests, conda_dir, env_dir  # noqa E402


def test_python_path():
    CommonTests._test_python_path('notebook', is_conda=False)


def test_which_python():
    CommonTests._test_which_python('notebook', is_conda=False)


def test_env_file():
    CommonTests._test_uv_env_file('notebook')


def test_env_vars():
    assert os.environ['DEFAULT_ENV'] == 'notebook'
    assert os.environ['ENV_DIR'] == '/opt/envs'
    assert os.environ['ENV_DIR'] == env_dir


def test_base_env():
    CommonTests._test_conda_env_file('base', f'{conda_dir}/base-lock.yml')
