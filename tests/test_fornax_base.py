import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests  # noqa E402
from common import env_root, jupyter_env, jupyter_root  # noqa E402


default_kernel = 'python3'


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


def test_update_notebooks_script():
    # needed by fornax-labextension >= 0.1.5
    os.path.exists('/usr/local/bin/update-notebooks.sh')