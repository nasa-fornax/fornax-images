import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests, change_dir  # noqa E402
from common import env_root, jupyter_env, jupyter_root  # noqa E402


notebook_dir = os.environ.get('NOTEBOOK_DIR', '/home/jovyan/fornax-notebooks')


def test_python_path():
    CommonTests._test_python_path(jupyter_env, jupyter_root)


def test_which_python():
    CommonTests._test_which_python(jupyter_env, jupyter_root)


def test_env_file():
    CommonTests._test_uv_env_file(jupyter_env, jupyter_root)


def test_env_vars():
    for var in [
        'DEFAULT_ENV', 'JUPYTER_DIR', 'MAMBA_ROOT_PREFIX', 'NOTEBOOK_DIR',
        'SUPPORT_DATA_DIR', 'ENV_DIR', 'FIREFLY_URL',
        'NB_USER', 'NB_UID', 'NB_GID',
        'PYTHON_VERSION', 'CACHE_DIR',
    ]:
        assert var in os.environ
    assert os.environ['CODE_EXECUTABLE'] == 'code-server'


def test_env_dir_not_exist():
    assert not os.path.exists(os.environ['ENV_DIR'])


def test_notebooks_folder():
    assert os.path.exists(notebook_dir)
    assert os.path.exists(f'{notebook_dir}/fornax-documentation')
    assert os.path.exists(f'{notebook_dir}/fornax-demo-notebooks')
