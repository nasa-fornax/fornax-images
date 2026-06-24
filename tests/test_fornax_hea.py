import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests, change_dir  # noqa E402
from common import env_root, jupyter_env, jupyter_root  # noqa E402

default_kernel = 'heasoft'

KERNELS = ['heasoft', 'sas', 'ciao', 'fermi']


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


@pytest.mark.parametrize("env",  KERNELS)
def test_conda_env(env):
    CommonTests._test_conda_env_file(
        env, f'{env_root}/{env}/{env}-lock.yml')


@pytest.mark.parametrize("env",  KERNELS)
def test_lock_and_files(env):
    if not os.path.exists(f'{env_root}/lock/{env}-lock.yml'):
        pytest.fail(f'No lock file for {env}')
    if not os.path.exists(f'{env_root}/lock/build-env-{env}'):
        pytest.fail(f'No build file for {env}')


@pytest.mark.parametrize("env",  KERNELS)
def test_envs(env):
    """Tests individual environments"""
    script_dir = os.path.dirname(__file__)
    envs = os.environ.copy()
    envs['DEFAULT_ENV'] = env
    res = CommonTests.run_cmd(
        (f'micromamba run -p {env_root}/{env} pytest -v -s '
         f'{script_dir}/test_env_{env}.py'), env=envs
    )
    print()
    print(res.stdout)
    print()
