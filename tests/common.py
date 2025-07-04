import sys
import subprocess
import os
from pathlib import Path
import contextlib

uv_root = os.environ.get('ENV_DIR', '/opt/envs')
jupyter_env = 'jupyter'
jupyter_root = '/opt'


class CommonTests:

    @staticmethod
    def run_cmd(command, env=None, **runargs):
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

    @staticmethod
    def _test_python_path(env, root):
        version = f'{sys.version_info.major}.{sys.version_info.minor}'
        assert (
            Path(sys.executable) in
            [Path(f'{root}/{env}/bin/python'),
             Path(f'{root}/{env}/bin/python{sys.version_info.major}'),
             Path(f'{root}/{env}/bin/python{version}')]
        )

    @staticmethod
    def _test_which_python(env, root):
        path = CommonTests.run_cmd('which python')
        assert (
            Path(path.stdout.strip()) ==
            Path(f'{root}/{env}/bin/python')
        )

    @staticmethod
    def _test_uv_env_file(uvenv, root):
        env = {'VIRTUAL_ENV': f'{root}/{uvenv}'}
        txt_file = f'/tmp/tmp_{uvenv}.txt'
        result = CommonTests.run_cmd(
            f'uv pip list --format=freeze > {txt_file}', env=env)
        diff_cmd = (
            f'diff {txt_file} {root}/{uvenv}/requirements-{uvenv}.txt')
        result = CommonTests.run_cmd(diff_cmd)
        assert result.stdout == ''
        assert result.stderr == ''

    @staticmethod
    def _test_conda_env_file(env, ref_yml):
        result = CommonTests.run_cmd(f'micromamba env export -n {env}')
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
        result = CommonTests.run_cmd(diff_cmd)
        assert result.stdout == ''
        assert result.stderr == ''


@contextlib.contextmanager
def change_dir(destination):
    """A context manager to change the current working directory."""
    try:
        current_dir = os.getcwd()
        os.chdir(destination)
        yield
    finally:
        os.chdir(current_dir)
