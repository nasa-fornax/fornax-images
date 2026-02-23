import pytest
from common import env_root, jupyter_env, jupyter_root, notebook_dir, notebooks  # noqa E402


@pytest.mark.parametrize("notebook",  list(notebooks.keys()))
def test_run_notebooks(notebook):
    """Do a full run of the notebook"""
    nb_file = notebooks[notebook]['file']
    env = notebooks[notebook]['env']
    nb_path = os.path.dirname(nb_file)
    nb_filename = os.path.basename(nb_file)
    py_filename = nb_filename.replace('md', 'py')
    assert os.path.exists(f'{notebook_dir}/{nb_file}')
    with change_dir(f'{notebook_dir}/{nb_path}'):
        CommonTests.run_cmd(
            f'{jupyter_root}/{jupyter_env}/bin/jupytext --to py {nb_filename}'
        )
        CommonTests.run_cmd(
            f'{env_root}/{env}/bin/python {py_filename}'
        )