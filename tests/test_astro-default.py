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
    


if __name__ == "__main__":
    unittest.main()