import sys
import subprocess
import os
from pathlib import Path

conda_dir = os.environ.get('CONDA_DIR', '/opt/conda')
env_dir = os.environ.get('ENV_DIR', '/opt/envs')


class CommonTests:

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

    def _get_env_root(self, env, is_conda):
        """return root path to the environment"""
        root = f'{conda_dir}/envs' if is_conda else env_dir
        if is_conda and (env in [None, '']):
            root = conda_dir
        return root

    def _test_python_path(self, env, is_conda=False):
        version = f'{sys.version_info.major}.{sys.version_info.minor}'
        root = self._get_env_root(env, is_conda)
        self.assertTrue(
            Path(sys.executable) in
            [Path(f'{root}/{env}/bin/python'),
             Path(f'{root}/{env}/bin/python{sys.version_info.major}'),
             Path(f'{root}/{env}/bin/python{version}')]
        )

    def _test_which_python(self, env, is_conda=False):
        path = self.run_cmd('which python')
        root = self._get_env_root(env, is_conda)
        self.assertEqual(
            Path(path.stdout.strip()),
            Path(f'{root}/{env}/bin/python')
        )

    def _test_conda_prefix(self, env):
        self.assertTrue('CONDA_PREFIX' in os.environ)
        self.assertEqual(
            os.environ['CONDA_PREFIX'],
            f'{conda_dir}/envs/{env}'
        )

    def _test_uv_env_file(self, uvenv):
        env = {'VIRTUAL_ENV': f'{env_dir}/{uvenv}'}
        txt_file = f'/tmp/tmp_{uvenv}.txt'
        result = self.run_cmd(f'uv pip freeze > {txt_file}',
                              env=env)
        diff_cmd = (
            f'diff {txt_file} {env_dir}/{uvenv}/requirements-{uvenv}.txt')
        result = self.run_cmd(diff_cmd)
        self.assertEqual(result.stdout, '')
        self.assertEqual(result.stderr, '')

    def _test_conda_env_file(self, env, ref_yml):
        result = self.run_cmd(f'mamba env export -n {env}')
        lines = []
        include = False
        for line in result.stdout.split('\n'):
            if "name:" in line:
                include = True
            if include:
                lines.append(line)
        with open(f"/tmp/tmp-{env}-lock.yml", "w") as fp:
            fp.write("\n".join(lines))
        diff_cmd = (
            f'diff /tmp/tmp-{env}-lock.yml {ref_yml}'
        )
        result = self.run_cmd(diff_cmd)
        self.assertEqual(result.stdout, '')
        self.assertEqual(result.stderr, '')
