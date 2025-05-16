import unittest
import subprocess
import sys
import os


class CommonTests:

    default_env = 'notebook'
    is_conda_env = False

    def run_cmd(self, command, env=None, **runargs):
        """Run shell command"""
        result = subprocess.run(command, shell=True, check=False, text=True,
                                capture_output=True, env=env, **runargs)
        if result.returncode != 0:
            sep = '\n' + ('+'*20) + '\n'
            raise RuntimeError(
                (f'*** ERROR running: {command}' + sep + result.stdout
                 + sep + result.stderr)
                )
        return result

    def test_python_path(self):
        version = f'{sys.version_info.major}.{sys.version_info.minor}'
        root = '/opt/conda/envs' if self.is_conda_env else '/opt/envs'
        self.assertTrue(
            sys.executable in
            [f'{root}/{self.default_env}/bin/python',
             f'{root}/{self.default_env}/bin/python{sys.version_info.major}',
             f'{root}/{self.default_env}/bin/python{version}']
        )

    def test_python_path2(self):
        path = self.run_cmd('which python')
        root = '/opt/conda/envs' if self.is_conda_env else '/opt/envs'
        self.assertEqual(
            path.stdout.strip(),
            f'{root}/{self.default_env}/bin/python'
        )

    def test_conda_prefix(self):
        if self.is_conda_env:
            self.assertTrue('CONDA_PREFIX' in os.environ)
            self.assertEqual(
                os.environ['CONDA_PREFIX'],
                f'/opt/conda/envs/{self.default_env}'
            )

    def _test_uv_env_file(self, uvenv):
        envdir = f"{os.environ['ENV_DIR']}/{uvenv}"
        env = {'VIRTUAL_ENV': envdir}
        result = self.run_cmd(f'uv pip freeze > tmp_{uvenv}.txt',
                              env=env)
        diff_cmd = (f'diff tmp_{uvenv}.txt {envdir}/requirements-{uvenv}.txt')
        result = self.run_cmd(diff_cmd)
        self.assertEqual(result.stdout, '')
        self.assertEqual(result.stderr, '')


class Test_fornax_base(unittest.TestCase, CommonTests):

    def test_env_file(self):
        self._test_uv_env_file('notebook')

    def test_unique_fornax_base_test(self):
        self.assertEqual(1, 1)


if __name__ == "__main__":
    unittest.main()
