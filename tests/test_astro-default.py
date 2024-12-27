import unittest
import subprocess
import sys
import os

sys.path.insert(0, os.getcwd())
from test_base_image import CommonTests


class Test_astro_default(unittest.TestCase, CommonTests):

    def test_conda_env_file(self):
        self._test_conda_env_file('astro-default')
    


if __name__ == "__main__":
    unittest.main()