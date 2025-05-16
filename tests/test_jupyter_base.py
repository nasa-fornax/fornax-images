import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests, conda_dir  # noqa E402


class Test_jupyter_base(unittest.TestCase, CommonTests):

    def test_python_path(self):
        self._test_python_path('', is_conda=True)

    def test_which_python(self):
        self._test_which_python('', is_conda=True)

    def test_base_env(self):
        self._test_conda_env_file('base', f'{conda_dir}/base-lock.yml')

    def test_stack_files(self):
        """Check for file from jupyter stack"""
        for file in [
            '/usr/local/bin/start-notebook.py',
            '/usr/local/bin/start-singleuser.py',
            '/etc/jupyter/docker_healthcheck.py',
        ]:
            assert os.path.exists(file)


if __name__ == "__main__":
    unittest.main()
