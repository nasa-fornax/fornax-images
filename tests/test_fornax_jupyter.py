import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests  # noqa E402
from common import env_root, jupyter_env, jupyter_root  # noqa E402
from test_fornax_nb import notebook_dir  # noqa E402


default_kernel = 'jupyter'


def test_python_path():
    CommonTests._test_python_path('jupyter', jupyter_root)


def test_which_python():
    CommonTests._test_which_python('jupyter', jupyter_root)


def test_env_file():
    CommonTests._test_uv_env_file('jupyter', jupyter_root)


def test_env_vars():
    assert os.environ['DEFAULT_ENV'] == default_kernel
    assert os.environ['ENV_DIR'] == '/opt/envs'
    assert os.environ['ENV_DIR'] == env_root
    for var in [
        'DEFAULT_ENV', 'JUPYTER_DIR', 'MAMBA_ROOT_PREFIX', 'NOTEBOOK_DIR',
        'SUPPORT_DATA_DIR', 'ENV_DIR',
        'NB_USER', 'NB_UID', 'NB_GID',
        'PYTHON_VERSION', 'CACHE_DIR',
        # from misc-setup.sh
        'USER_ENV_DIR', 'UV_PYTHON_INSTALL_DIR', 'CONDA_ENVS_PATH',
        'CODE_EXECUTABLE', 'CODE_EXTENSIONSDIR', 'FIREFLY_URL',
        'DASK_DISTRIBUTED__DASHBOARD__LINK', 'FORNAX_SOFTWARE_VERSION'
    ]:
        assert var in os.environ
    assert os.environ['CODE_EXECUTABLE'] == 'code-server'


def test_base_env():
    CommonTests._test_uv_env_file(jupyter_env, jupyter_root)


def test_notebooks_folder():
    assert os.path.exists(notebook_dir)
    assert os.path.exists(f'{notebook_dir}/fornax-demo-notebooks')
    assert os.path.exists(f'{notebook_dir}/irsa-tutorials')
    assert os.path.exists(f'{notebook_dir}/heasarc-tutorials')
    assert os.path.exists(f'{notebook_dir}/mast-tutorials')
