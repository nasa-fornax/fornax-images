import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests, change_dir  # noqa E402
from common import env_root, jupyter_env, jupyter_root, notebook_dir  # noqa E402

default_kernel = 'fermi'

notebooks = {}


def test_python_path():
    CommonTests._test_python_path(default_kernel, env_root)


def test_which_python():
    CommonTests._test_which_python(default_kernel, env_root)


def test_env_vars():
    assert os.environ['ENV_DIR'] == env_root


def test_base_env():
    CommonTests._test_uv_env_file(jupyter_env, jupyter_root)


def test_conda_env():
    CommonTests._test_conda_env_file(
        'fermi', f'{env_root}/fermi/fermi-lock.yml')


def test_check_packages():
    import fermipy # noqa 401
    import gt_apps  # noqa 401
