![GitHub Release](https://img.shields.io/github/v/release/nasa-fornax/fornax-images?label=Latest%20Release)

![Static Badge](https://img.shields.io/badge/develop-blue)
![GitHub last commit (branch)](https://img.shields.io/github/last-commit/nasa-fornax/fornax-images/develop?label=Last%20commit)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/nasa-fornax/fornax-images/image-build.yml?branch=develop&style=flat&label=build)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/nasa-fornax/fornax-images/run-tests.yml?branch=develop&style=flat&label=tests)

---

# fornax-images
This repo contains the Docker images for the Fornax Platform deployments.
It produces the jupyterhub computing environments.

The following is a general description of the images:

- Each image is in its own directory (e.g. `fornax-base` and `fornax-main`).

- `jupyter-base` is a custom jupyterlab image that matches the 
  [base-notebook](https://github.com/jupyter/docker-stacks/tree/main/images/base-notebook)
  in the jupyter stack.

- `fornax-base` is a base image for other images in fornax. Other images should use 
  it as a starting point.
  
- Jupyterlab is installed in an environment called `jupyter` in $ENV_DIR/jupyter.
  Basic astronomy and analysis packages are installed in a environment called `python3`,
  which is the default environment for running analysis.
  
- Each demo notebook has its own environment. These environments
  are created during the build using the `requirements.txt` files associated with
  individual notebooks (managed with `uv`).
  Notebook environment have names: `py-{notebook-name}`.

- `pre-notebook.sh` is a script that runs before a jupyter server is started.

- `overrides.json` contains any jupyter settings that need to be set by default.
  
- The `scripts/build.py` script is used when building the images. The script has many options.
  Run `python scripts/build.py -h` for detailed help. Example runs include:
  - To build an image locally: `python scripts/build.py image-name`. Where `image-name`
  is `fornax-base`, `fornax-main` etc. The image will be tagged as 
  `ghcr.io/nasa-fornax/fornax-images/{image-name}:{branch-name}`
  - Adding `--push` pushes the images the the github container registry.
  - Adding `--ecr-endpoint $ENDPOINT --trigger-ecr` notify `$ENDPOINT` that
  a new image has been built. This is used as part of the build CI.

- Building an image that starts from`fornx-base` will trigger the `ONBUILD` sections
defined in `fornax-base/Dockerfile`, which include:
  - If `apt.txt` exits, it will be parsed for the list of the system software to be installed with `apt-get`.
  - If `build-*` files exist, the scripts are run during the build.
  - If `conda-{env}.yml` exists, it is used to create a conda environment called `{env}`.
  - If `requirements-{env}.txt` exists, it is used to create a virtual python
    environment `{env}` (using `uv venv`). Experience showed that having packages managed with `pip`
    rather than `conda`, reduces the chance of conflicts. Conda-managed environments can create
    the undesired situations (e.g. #20) where conda install a version of a package and pip install another one.
  - The `introduction.md` file is shared between the main fornax images. During the build, its copied
    to the image folder and converted to an html file (with `pandoc`) that is included in the image.
    the `pre-notebook` script copies is from `$JUPYTER_DIR/introduction.html` to `$NOTEBOOK_DIR` when
    the notebook server starts.

# The images
- `jupyter-base`: is a custom jupyterlab image that matches the 
  [base-notebook](https://github.com/jupyter/docker-stacks/tree/main/images/base-notebook)
  in the jupyter stack. It is build here to allow for customization, including
  the possibility of using conda alternatives, such as pixi (in the future).

- `fornax-base`:  is the base image that all other fornax images start from. 
  It contains jupyter and the basic science tools needed for deployment in the fornax project.

- `fornax-main`: Main Fornax image that was used for the demo notebooks. It contains several 
  notebook kernels. The `notebook` environment contains general astronomy and science tools.
  Additionally, each demo notebook has its own environment (or kernel).

- `fornax-hea`: Fornax image containign high energy software. For now, it has heasoft as installed
  as a conda package.

