import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests  # noqa E402
from common import jupyter_env, jupyter_root  # noqa E402


class Test_jupyter_base(unittest.TestCase):

    def test_python_path(self):
        CommonTests._test_python_path(jupyter_env, jupyter_root)

    def test_which_python(self):
        CommonTests._test_which_python(jupyter_env, jupyter_root)

    def test_jupyter_env(self):
        CommonTests._test_uv_env_file(jupyter_env, jupyter_root)

    def test_stack_files(self):
        """Check for file from jupyter stack"""
        for file in [
            '/usr/local/bin/start-notebook.py',
            '/usr/local/bin/start-singleuser.py',
            '/etc/jupyter/docker_healthcheck.py',
        ]:
            assert os.path.exists(file)

    def test_stack_files_jupyter(self):
        """Check that the start files use the correct jupyter"""
        for file in [
            '/usr/local/bin/start-notebook.py',
            '/usr/local/bin/start-singleuser.py',
        ]:
            with open(file) as fp:
                lines = fp.readlines()
                assert any(
                    [f'"{jupyter_root}/{jupyter_env}/bin/jupyter'
                        in line for line in lines]
                )


if __name__ == "__main__":
    unittest.main()
