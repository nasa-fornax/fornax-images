import unittest
import subprocess
import sys
import os


class CommonTests:

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
        self.assertTrue(
            sys.executable in
            ['/opt/conda/envs/notebook/bin/python',
             f'/opt/conda/envs/notebook/bin/python{version}']
        )

    def test_python_path2(self):
        path = self.run_cmd('which python')
        self.assertEqual(
            path.stdout.strip(), '/opt/conda/envs/notebook/bin/python'
        )

    def test_conda_prefix(self):
        self.assertTrue('CONDA_PREFIX' in os.environ)
        self.assertEqual(
            os.environ['CONDA_PREFIX'], '/opt/conda/envs/notebook'
        )

    def _test_conda_env_file(self, image):
        result = self.run_cmd('mamba env export -n notebook')
        lines = []
        include = False
        for line in result.stdout.split('\n'):
            if "name:" in line:
                include = True
            if include:
                lines.append(line)
        with open("tmp-notebook-lock.yml", "w") as fp:
            fp.write("\n".join(lines))
        diff_cmd = (
            f'diff tmp-notebook-lock.yml {os.path.dirname(__file__)}'
            f'/../{image}/conda-notebook-lock.yml'
        )
        result = self.run_cmd(diff_cmd)
        self.assertEqual(result.stdout, '')
        self.assertEqual(result.stderr, '')


class Test_base_image(unittest.TestCase, CommonTests):

    def test_conda_env_file(self):
        self._test_conda_env_file('base_image')

    def test_unique_base_image_test(self):
        self.assertEqual(1, 1)


if __name__ == "__main__":
    unittest.main()
