import sys
import os
import subprocess
import glob

sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests, change_dir  # noqa E402
from common import env_root, jupyter_env, jupyter_root  # noqa E402

default_kernel = 'esassdr1'

KERNELS = ['esassdr1']


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
    # eSASS needs heasoft, so we check the lock file
    CommonTests._test_conda_env_file(
        'heasoft', f'{env_root}/heasoft/heasoft-lock.yml')
    CommonTests._test_conda_env_file(
        'esassdr1', f'{env_root}/esassdr1/esassdr1-lock.yml')


def test_kernels():
    """Kernel definitions should exist"""
    CommonTests.test_kernels_exist(KERNELS)


def test_pysas_import():
    import pysas  # noqa E401


def test_srctool_version():
    subprocess.check_call(["srctool", "--version"])


# def test_data_dir():
#     """Check data directories"""
#     dirname = glob.glob(f'{env_root}/sas/xmmsas_*')
#     assert len(dirname) == 1
#     dirname = dirname[0].split('/')[-1]
#     version = dirname.split("_", 1)[1].split("-", 1)[0]
#     support_dir = os.environ['SUPPORT_DATA_DIR']
#     assert os.path.exists(f'{support_dir}/xmmsas-{version}/data')
#     assert len(glob.glob(f'{support_dir}/xmmsas-{version}/data/*')) != 0
#
#     # check for symlinks
#     assert os.path.exists(f'{env_root}/sas/{dirname}/lib/data')
#     assert os.path.islink(f'{env_root}/sas/{dirname}/lib/data')
