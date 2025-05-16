import sys
import os
import ast
import re
import contextlib
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests, conda_dir, env_dir  # noqa E402


notebook_dir = os.environ.get('NOTEBOOK_DIR', '/home/jovyan/notebooks')

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
    'light_curve_generator': {
        'file': 'fornax-demo-notebooks/light_curves/light_curve_generator.md',
        'env': 'py-light_curve_generator'
    },
    'scale_up': {
        'file': 'fornax-demo-notebooks/light_curves/scale_up.md',
        'env': 'py-scale_up'
    },
    'ml_agnzoo': {
        'file': 'fornax-demo-notebooks/light_curves/ML_AGNzoo.md',
        'env': 'py-ml_agnzoo'
    }
}


@contextlib.contextmanager
def change_dir(destination):
    """A context manager to change the current working directory."""
    try:
        current_dir = os.getcwd()
        os.chdir(destination)
        yield
    finally:
        os.chdir(current_dir)


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


def test_notebooks_folder():
    assert os.path.exists(notebook_dir)
    assert os.path.exists(f'{notebook_dir}/fornax-documentation')
    assert os.path.exists(f'{notebook_dir}/fornax-demo-notebooks')


@pytest.mark.parametrize("notebook",  list(notebooks.keys()))
def test_check_packages(notebook):
    CommonTests._test_uv_env_file(notebooks[notebook]['env'])


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
            f'{env_dir}/{env}/bin/python imports_{py_filename}'
        )
