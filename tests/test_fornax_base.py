import sys
import os
import shutil
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests  # noqa E402
from common import env_root, jupyter_env, jupyter_root  # noqa E402


default_kernel = 'jupyter'


def test_python_path():
    CommonTests._test_python_path(default_kernel, jupyter_root)


def test_which_python():
    CommonTests._test_which_python(default_kernel, jupyter_root)


def test_env_file():
    CommonTests._test_uv_env_file(default_kernel, jupyter_root)


def test_env_vars():
    assert os.environ['DEFAULT_ENV'] == default_kernel
    assert os.environ['ENV_DIR'] == '/opt/envs'
    assert os.environ['ENV_DIR'] == env_root


def test_dirs_exis():
    for dir_name in ['NOTEBOOK_DIR', 'LOCK_DIR', 'ENV_DIR']:
        if not os.path.exists(os.environ[dir_name]):
            pytest.fail(f'{dir_name}={os.environ[dir_name]} does not exist')


def test_scripts_exist():
    for script in [
        'apt-install.sh', 'clone-notebooks.sh',
        'link-notebooks.sh', 'map-data.sh', 'setup-conda-env',
        'setup-pip-env',
        'before-notebook.d/10activate-env.sh',
        'before-notebook.d/20link-notebooks.sh'
    ]:
        if not os.path.exists(f'/usr/local/bin/{script}'):
            pytest.fail(f'script={script} does not exist in /usr/local/bin')


def test_base_env():
    CommonTests._test_uv_env_file(jupyter_env, jupyter_root)


def test_base_tools_exist():
    for tool in ['jq', 'git']:
        if not shutil.which(tool):
            pytest.fail(f'base tool {tool} cannot run')


def test_build_version():
    file = f'{os.environ["LOCK_DIR"]}/build-fornax-base'
    if not os.path.exists(file):
        pytest.fail(f'Missing build version {file}')
