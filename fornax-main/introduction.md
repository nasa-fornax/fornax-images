
<img src="https://nasa-fornax.github.io/fornax-demo-notebooks/_static/fornax_logo.png" alt="Fornax Science Console"
    style="float: right; width: 200px; margin: 10px;" />

# Documentation
The general documentation for using the Fornax Science Console are available in the 
[documentation repository](fornax-documentation/README.md). These can also be browsed
in the [documentation page on github](https://nasa-fornax.github.io/fornax-demo-notebooks/#user-documentation).

# Notebooks
The `notebooks` folder in the home directory contains notebooks that are actively being
developed. They currently include:
- [fornax-demo-notebooks](fornax-demo-notebooks/README.md): These are the main notebooks developed
  by the Fornax team. The rendered version is available on the
  [documentation page](https://nasa-fornax.github.io/fornax-demo-notebooks).
- [IVOA_2024_demo](IVOA_2024_demo/README.md): Notebooks developed in collaboration with the LINCC team,
  demonstrating the use of Hispcat and LSDB for large catalog cross matching.
- Others will be added.

The content of the `notebooks` folder in the home directory will be updated automatically
at the start of every new session. To disable these updates, add an empty file called
`.no-notebook-update.txt` in your home directory.

---
# Latest Changes

## 05/04/2025
- Fix openvscode-server by using jupyter-openvscodeserver-proxy instead of jupyter-vscode-proxy.
- Update packages to the latest possible.

## 03/20/2025
- Add jdaviz (and dependencies) to support JWST notebooks.
- Update python to 3.12 (and iupyterlab==4.3.6, jupyterhub==5.2.1, notebook==7.3.3).
- Update various other packages to the latest.

## 11/26/2024
- The primary conda environment is changed to `notebook`. It is the environment
where the notebooks should be run. With this change, the dask extension should
work naturally.
- Added the openvscode extension.
- Updates to prevent sessions with CPU activity from being stopped. The policy now is:
    - If there is CPU activity, the notebook will not be stopped, even if the browser
    is closed.
    - If there is no activity (e.g. the notebook or browser tab is closed),
    the session terminates after 15 min. 
- The notebooks are updated automatically using `nbgitpuller` and they are
stored in the user's home directory. The update policy for `nbgitpuller`can be found
[here](https://nbgitpuller.readthedocs.io/en/latest/topic/automatic-merging.html#topic-automatic-merging).
The summary is:
    - 1. A file that is changed in the remote repo but not in the local clone will be updated.
    - 2. If different lines are changed by both the remote and local clone, the remote
    changes will be merged similar to case 1.
    - 3. If the same lines are changed by both the remote and local clone, the local
    changes are kept and the remote changes are discarded.
    - 4. If a file is deleted locally but still present in the remote repo, it will be restored.
    - 5. If a new file is added in the locall clone, and the remote repo has a new file with
    the same name, the local copy will be renamed by adding `_<timestamp>`, and the remote copy
    will be used.
If the user has a file (it can be empty) called `.no-notebook-update.txt` in their home
directory, then `nbgitpuller` will not be used and the notebook folder in the home
directory will **not** be updated.
- Switched to using conda yaml files to keep track of the installed software.