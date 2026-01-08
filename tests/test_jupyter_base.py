import unittest
import sys
import os
import pwd
import subprocess
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
            # start it and ensure it uses the correct jupyter
            # add --help so we don't do a full run.
            proc = subprocess.run(
                [file, '--help'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            out = proc.stdout + proc.stderr
            assert f'{jupyter_root}/{jupyter_env}/bin/jupyter' in out
    
    def test_user_id_name(self):
        """Check the username/id/gid etc"""
        uid = os.getuid()
        gid = os.getgid()
        username = pwd.getpwuid(uid).pw_name
        assert uid == 1000
        assert gid == 100
        assert username == 'jovyan'
        assert os.environ['NB_UID'] == f'{uid}'
        assert os.environ['NB_GID'] == f'{gid}'
        assert os.environ['NB_USER'] == username



if __name__ == "__main__":
    unittest.main()
