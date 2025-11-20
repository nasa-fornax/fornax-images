import sys
import os
import ast
import re
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests, change_dir  # noqa E402
from common import env_root, jupyter_env, jupyter_root  # noqa E402

default_kernel = 'python3'

notebook_dir = os.environ.get('NOTEBOOK_DIR', '/home/jovyan/fornax-notebooks')

notebooks = {
    'multiband_photometry': {
        'file': ('fornax-demo-notebooks/forced_photometry/'
                 'multiband_photometry.md'),
        'env': 'py-multiband_photometry'
    },
    'light_curve_classifier': {
        'file': 'fornax-demo-notebooks/light_curves/light_curve_classifier.md',
        'env': 'py-light_curve_classifier'
    },
    'light_curve_collector': {
        'file': 'fornax-demo-notebooks/light_curves/light_curve_collector.md',
        'env': 'py-light_curve_collector'
    },
    'scale_up': {
        'file': 'fornax-demo-notebooks/light_curves/scale_up.md',
        'env': 'py-scale_up'
    },
    'ml_agnzoo': {
        'file': 'fornax-demo-notebooks/light_curves/ML_AGNzoo.md',
        'env': 'py-ml_agnzoo'
    },
    'spectra_collector': {
        'file': 'fornax-demo-notebooks/spectroscopy/spectra_collector.md',
        'env': 'py-spectra_collector'
    },
    'ztf_ps1_crossmatch': {
        'file': 'fornax-demo-notebooks/crossmatch/ztf_ps1_crossmatch.md',
        'env': 'py-ztf_ps1_crossmatch'
    }
}

KERNELS = ['python3'] + [val['env'] for val in notebooks.values()]

def test_python_path():
    CommonTests._test_python_path(default_kernel, env_root)


def test_which_python():
    CommonTests._test_which_python(default_kernel, env_root)


def test_env_file():
    CommonTests._test_uv_env_file(default_kernel, env_root)


def test_env_vars():
    assert os.environ['DEFAULT_ENV'] == default_kernel
    assert os.environ['ENV_DIR'] == '/opt/envs'
    assert os.environ['ENV_DIR'] == env_root


def test_base_env():
    CommonTests._test_uv_env_file(jupyter_env, jupyter_root)


def test_notebooks_folder():
    assert os.path.exists(notebook_dir)
    assert os.path.exists(f'{notebook_dir}/fornax-demo-notebooks')


@pytest.mark.parametrize("notebook",  list(notebooks.keys()))
def test_check_packages(notebook):
    CommonTests._test_uv_env_file(notebooks[notebook]['env'], env_root)


def test_code_server():
    CommonTests.run_cmd(f'which code-server')


def test_conda_base_env():
    CommonTests._test_conda_env_file(
        'base', f'{env_root}/base/base-lock.yml')


@pytest.mark.parametrize("notebook", list(notebooks.keys()))
def test_imports(notebook):
    """Extract the imports from the notebook and make sure they run"""
    nb_file = notebooks[notebook]['file']
    env = notebooks[notebook]['env']
    nb_path = os.path.dirname(nb_file)
    nb_filename = os.path.basename(nb_file)
    py_filename = nb_filename.replace('md', 'py')
    # isolate the imports
    with change_dir(f'{notebook_dir}/{nb_path}'):
        # we need the folder to be writable
        CommonTests.run_cmd(
            f'jupytext --to py {nb_filename}'
        )

        with open(py_filename) as fp:
            tree = ast.parse(fp.read())
        imports = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                imports.append(ast.get_source_segment(
                    open(py_filename).read(), node))
        with open(f'imports_{py_filename}', 'w') as fp:
            imports = [
                'import os', 'import sys',
                'sys.path.insert(0, os.getcwd() + "/code_src")'
            ] + imports
            if notebook == 'multiband_photometry':
                imports += ['import tractor']
            fp.write('\n'.join([
                re.sub(r'\n|\\', '', line) for line in imports]))

        CommonTests.run_cmd(
            f'{env_root}/{env}/bin/python imports_{py_filename}'
        )

@pytest.mark.parametrize("notebook", list(notebooks.keys()))
def test_notebook_permissions(notebook):
    """Folders are writable; files are read-only"""
    nb_file = notebooks[notebook]['file']
    nb_path = os.path.dirname(nb_file)
    
    assert not os.access(f'{notebook_dir}/{nb_file}', os.W_OK)
    assert os.access(f'{notebook_dir}/{nb_path}', os.W_OK)

def test_notebook_kernels():
    """Kernel defnitions should exist"""
    CommonTests.test_kernels_exist(KERNELS)
