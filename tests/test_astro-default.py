import unittest
import sys
import os
from packaging import version
import contextlib
import pytest

sys.path.insert(0, os.getcwd())
from test_base_image import CommonTests  # noqa: E402

notebook_dir = os.environ.get('NOTEBOOK_DIR', '/home/jovyan/notebooks')

notebooks = {
    'multiband_photometry': {
        'file': ('fornax-demo-notebooks/forced_photometry/'
                 'multiband_photometry.md'),
        'req': 'requirements_multiband_photometry.txt'
    },
    'light_curve_classifier': {
        'file': 'fornax-demo-notebooks/light_curves/light_curve_classifier.md',
        'req': 'requirements_light_curve_classifier.txt'
    },
    'light_curve_generator': {
        'file': 'fornax-demo-notebooks/light_curves/light_curve_generator.md',
        'req': 'requirements_light_curve_generator.txt'
    },
    'scale_up': {
        'file': 'fornax-demo-notebooks/light_curves/scale_up.md',
        'req': 'requirements_scale_up.txt'
    },
    'ML_AGNzoo': {
        'file': 'fornax-demo-notebooks/light_curves/ML_AGNzoo.md',
        'req': 'requirements_ML_AGNzoo.txt'
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


class Test_astro_default(unittest.TestCase, CommonTests):

    def test_conda_env_file(self):
        self._test_conda_env_file('astro-default')

    def test_check_packages(self):
        import tractor
        import astrometry
        import lsdb
        tractor.__version__
        astrometry.__version__
        self.assertLess(version.parse(lsdb.__version__), version.parse('0.4'))

    def test_notebooks_folder(self):
        self.assertTrue(
            os.path.exists(notebook_dir)
        )
        self.assertTrue(
            os.path.exists(f'{notebook_dir}/fornax-documentation')
        )
        self.assertTrue(
            os.path.exists(f'{notebook_dir}/fornax-demo-notebooks')
        )


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
