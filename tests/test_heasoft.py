import unittest
import sys
import os
import contextlib
import pytest

sys.path.insert(0, os.getcwd())
CommonTests = __import__('test_base-image').CommonTests

notebook_dir = os.environ.get('NOTEBOOK_DIR', '/home/jovyan/notebooks')

notebooks = {
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


class Test_heasoft(unittest.TestCase, CommonTests):

    def test_conda_env_file(self):
        self._test_conda_env_file('astro-default')

    def test_check_packages(self):
        import heasoftpy
        import xspec
        heasoftpy.__version__
        xspec.__version__

    # def test_notebooks_folder(self):
    #     self.assertTrue(
    #         os.path.exists(notebook_dir)
    #     )
    #     self.assertTrue(
    #         os.path.exists(f'{notebook_dir}/fornax-documentation')
    #     )
    #     self.assertTrue(
    #         os.path.exists(f'{notebook_dir}/fornax-demo-notebooks')
    #     )


@pytest.mark.parametrize("notebook",  list(notebooks.keys()))
def test_notebooks(notebook):
    common = CommonTests()
    nb_file = notebooks[notebook]['file']
    nb_req = notebooks[notebook]['req']
    nb_path = os.path.dirname(nb_file)
    nb_filename = os.path.basename(nb_file)
    py_filename = nb_filename.replace('md', 'py')
    assert os.path.exists(f'{notebook_dir}/{nb_file}')
    with change_dir(f'{notebook_dir}/{nb_path}'):
        common.run_cmd(f'pip install -r {nb_req}')
        common.run_cmd(f'jupytext --to py {nb_filename}')
        common.run_cmd(f'python {py_filename}')


if __name__ == "__main__":
    unittest.main()
