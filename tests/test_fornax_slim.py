import sys
import os
import re

sys.path.insert(0, os.path.dirname(__file__))
from common import CommonTests, change_dir  # noqa E402
from common import env_root, jupyter_env, jupyter_root, notebook_dir  # noqa E402



def test_python_path():
    CommonTests._test_python_path(jupyter_env, jupyter_root)


def test_which_python():
    CommonTests._test_which_python(jupyter_env, jupyter_root)


def test_env_file():
    CommonTests._test_uv_env_file(jupyter_env, jupyter_root)


def test_env_vars():
    for var in [
        'DEFAULT_ENV', 'JUPYTER_DIR', 'MAMBA_ROOT_PREFIX', 'NOTEBOOK_DIR',
        'SUPPORT_DATA_DIR', 'ENV_DIR', 'FIREFLY_URL',
        'NB_USER', 'NB_UID', 'NB_GID',
        'PYTHON_VERSION', 'CACHE_DIR',
    ]:
        assert var in os.environ
    assert os.environ['CODE_EXECUTABLE'] == 'code-server'


def test_env_dir_not_exist():
    assert not os.path.exists(os.environ['ENV_DIR'])


def test_notebooks_folder():
    assert os.path.exists(notebook_dir)
    assert os.path.exists(f'{notebook_dir}/fornax-demo-notebooks')

def test_env_vars():
    """ensure all variables defined in fornax-base and subsequent images
    are propagated to fornax-slim
    """
    images = ['jupyter-base', 'fornax-base', 'fornax-main', 'fornax-hea']
    wdir = os.path.dirname(__file__)
    envs = []
    for image in images:
        _envs = _extract_env_vars(f'{wdir}/../{image}/Dockerfile')
        envs += _envs
    
    slim_envs = _extract_env_vars(f'{wdir}/../fornax-slim/Dockerfile')
    assert(set(envs) == set(slim_envs))



def _extract_env_vars(dockerfile):
    """Extract all ENV variables from a Dockerfile"""
    env_vars = []
    with open(dockerfile, 'r') as fp:
        lines = fp.readlines()
    
    # Join lines that end with backslash
    combined_lines = []
    current = ''
    for line in lines:
        sline = line.strip()
        if not sline or sline.startswith('#'):
            continue
        if sline[-1] == '\\':
            current += sline[:-1] + ' '
        else:
            current += sline
            combined_lines.append(current)
            current = ''
    # now look for the ENV
    pattern = re.compile(r'^\s*ENV\s+(.*)')
    for line in combined_lines:
        match = pattern.match(line)
        if match:
            parts = match.group(1)
            for var in re.findall(r'(\S+?)(?:=)', parts):
                env_vars.append(var)
    return env_vars
