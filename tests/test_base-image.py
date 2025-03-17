import unittest
import subprocess
import sys
import os


class CommonTests:

    default_env = 'notebook'

    def run_cmd(self, command, **runargs):
        """Run shell command"""
        result = subprocess.run(command, shell=True, check=False, text=True,
                                capture_output=True, **runargs)
        if result.returncode != 0:
            sep = '\n' + ('+'*20) + '\n'
            raise RuntimeError(
                (f'*** ERROR running: {command}' + sep + result.stdout
                 + sep + result.stderr)
                )
        return result

    def test_python_path(self):
        version = f'{sys.version_info.major}.{sys.version_info.minor}'
        print(self.default_env)
        self.assertTrue(
            sys.executable in
            [f'/opt/conda/envs/{self.default_env}/bin/python',
             f'/opt/conda/envs/{self.default_env}/bin/python{version}']
        )

    def test_python_path2(self):
        path = self.run_cmd('which python')
        self.assertEqual(
            path.stdout.strip(),
            f'/opt/conda/envs/{self.default_env}/bin/python'
        )

    def test_conda_prefix(self):
        self.assertTrue('CONDA_PREFIX' in os.environ)
        self.assertEqual(
            os.environ['CONDA_PREFIX'], f'/opt/conda/envs/{self.default_env}'
        )

    def _test_conda_env_file(self, image):
        result = self.run_cmd(f'mamba env export -n {self.default_env}')
        lines = []
        include = False
        for line in result.stdout.split('\n'):
            if "name:" in line:
                include = True
            if include:
                lines.append(line)
        with open(f"tmp-{self.default_env}-lock.yml", "w") as fp:
            fp.write("\n".join(lines))
        diff_cmd = (
            f'diff tmp-{self.default_env}-lock.yml {os.path.dirname(__file__)}'
            f'/../{image}/conda-{self.default_env}-lock.yml'
        )
        result = self.run_cmd(diff_cmd)
        self.assertEqual(result.stdout, '')
        self.assertEqual(result.stderr, '')


class Test_base_image(unittest.TestCase, CommonTests):

    def test_conda_env_file(self):
        self._test_conda_env_file('base-image')

    def test_unique_base_image_test(self):
        self.assertEqual(1, 1)


if __name__ == "__main__":
    unittest.main()
