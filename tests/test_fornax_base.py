import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests, conda_dir, env_dir  # noqa E402


class Test_fornax_base(unittest.TestCase, CommonTests):

    def test_python_path(self):
        self._test_python_path('notebook', is_conda=False)

    def test_which_python(self):
        self._test_which_python('notebook', is_conda=False)

    def test_env_file(self):
        self._test_uv_env_file('notebook')

    def test_env_vars(self):
        assert os.environ['DEFAULT_ENV'] == 'notebook'
        assert os.environ['ENV_DIR'] == '/opt/envs'
        assert os.environ['ENV_DIR'] == env_dir

    def test_base_env(self):
        self._test_conda_env_file('base', f'{conda_dir}/base-lock.yml')
