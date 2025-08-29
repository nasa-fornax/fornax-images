import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests, change_dir  # noqa E402
from common import uv_root, jupyter_env, jupyter_root  # noqa E402

default_kernel = 'sas'

notebook_dir = os.environ.get('NOTEBOOK_DIR', '/home/jovyan/fornax-notebooks')
notebooks = {}


def test_python_path():
    CommonTests._test_python_path(default_kernel, uv_root)


def test_which_python():
    CommonTests._test_which_python(default_kernel, uv_root)


def test_env_vars():
    assert os.environ['ENV_DIR'] == uv_root


def test_base_env():
    CommonTests._test_uv_env_file(jupyter_env, jupyter_root)


def test_conda_env():
    CommonTests._test_conda_env_file(
        'sas', f'{uv_root}/sas/sas-lock.yml')


def test_version():
    subprocess.check_call(["sas", "--version"])


def test_ccf():
    # Runs the SAS cifbuild routine, but set to generate a master index file (MIF). Users never need to do
    #  this, but it means we don't have to point cifbuild at a particular XMM observation, and it will raise
    #  a warning if it can't find any CCFs
    output = subprocess.run(["cifbuild", "masterindex=yes"], stderr=subprocess.PIPE)
    output = output.stderr.decode('utf-8')
    # Check if the stderr has any entries in it - it shouldn't if all went well
    assert len(output) == 0
    # If we're here we need to clean up the output file from the cifbuild call
    os.remove('ccf.cif')
