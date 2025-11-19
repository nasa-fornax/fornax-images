
<img src="https://raw.githubusercontent.com/nasa-fornax/fornax-documentation/refs/heads/main/_static/fornax_logo.png" alt="Fornax Science Console"
    style="float: right; width: 200px; margin: 10px;" />

# Documentation & Support
The general documentation for using the Fornax Science Console are available in 
the [documentation page](https://docs.fornax.sciencecloud.nasa.gov/).
Help and support is available in the [Fornax discource forum](https://discourse.fornax.sciencecloud.nasa.gov).

# Notebooks
The `fornax-notebooks` folder in the home directory contains notebooks that are actively being
developed. They currently include:
- [fornax-demo-notebooks](fornax-demo-notebooks/README.md): These are the main notebooks developed
  by the Fornax team.
- Others will be added.

The content of the `fornax-notebooks` folder in the home directory can be updated from Fornax menu
at the top: Fornax -> Update Notebooks, or by running the `update-notebooks.sh` script from the
terminal.

---
# Latest Changes

## 25.1120
- Update fornax-labextension to open hub links (hub control and logout) in the page (v0.1.8).
- Make conda-env-install and uv-env-install generic.
- Updates to the deployment infrastructure (kernel files in the images).
- Terminals now call ~/.bashrc (#125).
- Several fixes and updates:
  - Add pip to the jupyter environment for extension installs.
  - Fix tractor install.
  - Fix `%pip` in notebooks (#122).
  - Update lsdb in the ztf environment.
  - Add terminal culling.

## 25.1006
- Add XMM SAS software to the high energy image.
- Add s3fs to python3 and the high energy environments.
- remove notebook-intelligence as it slows startup.
- Updates to support the software AMI.

## 25.0923
- Install notebook-intelligence extension for AI code assistance.
- Add conda/mamba alias that point the user to micromamba (issue #101).
- make folders in the notebooks folder writable; files are read-only. Fix #98
- Move all apt installs to fornax-base to allow portability to fornax-slim #95
- Allow user-installed extensions in code-server to persist #102

## 25.0904
- Fix vscode extension

## 25.0903
- Rebuild to pick the new deployed notebook kernels: `ztf_ps1_crossmatch` and `spectra_collector`.
- Make the fornax-notebooks read-only. Modified notebooks need to be saved elsewhere.
- Bug fixes (issues #87, #86).

## 25.0829
- Add 'Update Notebooks' to Fornax menu (fornax-labextension = 0.1.5).
- Fix Firefly and dask installations.
- Fix calibration database CALDB setup for the heasoft and ciao environments in the high energy image.
- Update kernels for renamed notebook light_curve_generator -> light_curve_collector.
- Build updates to allow for portable software environments (through AMI) and a slim final container image.

## 25.0821
- Update fornax-labextension to get the updated links.
- Add ciao and fermitools to the high energy image.
- Add `/opt/support-data` that points to a sharing location for data used by the software.

## 25.0714
- Fix notebook scrolling jumps (caused by jupyterlab-myst) by setting a default windowing mode in the notebook app.
- Change location of installed software to allow for portability. Lock files are now
  under `LOCK_DIR=$ENV_DIR/lock`
- Add a script `update-notebooks.sh` that the user can run instead of doing the update
  at startup (can slow the startup).

## 25.0630
- Switch to using a separate environment for each notebook. Each notebook has a matching
  environment (or kernel) with a name that starts with `py-`, e.g. `py-multiband_photometry`,
  `py-light_curve_classifier`. These can be selected from the kernel drop down menu when the 
  notebook is launched. To activate one of these environments on the terminal, run:
  `source /opt/envs/py-multiband_photometry/bin/activate` for `py-multiband_photometry` for example.
- Add fornax-labextension, which adds a Fornax top menu, items in the Launcher, and controls the
  display of the `py-*` kernels in the launcher.
- Jupyterlab is run in the conda base environment. The default kernel `python3` contains 
  general astronomy tools (now managed with pip instead of conda).
- Lock files that list the packages in each environment are stored in the folder `$LOCK_DIR`.
  The same files are also available on github for every image release.


## 25.0504
- Fix openvscode-server by using jupyter-openvscodeserver-proxy instead of jupyter-vscode-proxy.
- Update packages to the latest possible.

## 25.0320
- Add jdaviz (and dependencies) to support JWST notebooks.
- Update python to 3.12 (and iupyterlab==4.3.6, jupyterhub==5.2.1, notebook==7.3.3).
- Update various other packages to the latest.

## 24.1126
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