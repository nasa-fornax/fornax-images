import unittest
import subprocess
import sys
import os
from packaging import version

sys.path.insert(0, os.getcwd())
from test_base_image import CommonTests


class Test_astro_default(unittest.TestCase, CommonTests):

    def test_conda_env_file(self):
        self._test_conda_env_file('astro-default')
    
    def test_check_packages(self):
        import tractor
        import astrometry
        import lsdb
        self.assertLess(version.parse(lsdb.__version__), version.parse('0.4'))
    
    def test_notebooks_folder(self):
        self.assertTrue(os.path.exists('/home/jovyan/notebooks'))
        self.assertTrue(os.path.exists('/home/jovyan/notebooks/fornax-documentation'))
        self.assertTrue(os.path.exists('/home/jovyan/notebooks/fornax-demo-notebooks'))
    
    def test_photometry_notebook(self):
        os.chdir('/home/jovyan/notebooks/fornax-demo-notebooks/forced_photometry')
        self.run_cmd('pip install -r requirements_multiband_photometry.txt')
        self.run_cmd('jupytext --to py multiband_photometry.md')
        self.run_cmd('python multiband_photometry.py')
    


if __name__ == "__main__":
    unittest.main()