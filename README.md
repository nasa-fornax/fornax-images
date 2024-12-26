# fornax-images
This repo contains the Docker images for the Fornax Platform deployments.
It produces reproducible computing environments. Some of the parts are
adapted from the [Pangeo](https://github.com/pangeo-data/pangeo-docker-images) project.

Reproducibility is achived by keeping track of the software environments using conda yaml files.
The following is a general description of the images:

- Each image is in its own directory (e.g. `base_image` and `astro-defaul`).

- `base_image` is a base image that contains basic JupyterHub and Lab setup, and many astronomy packages.
Other images should use it as a starting point (i.e. using `FROM ...`).

- Jupyterlab is installed in a conda environment called `notebook`, and it is the
default environment when running the images. It is also the environment that contains `dask`.

- The `scripts/build.py` script should be used when building the image locally. It takes as parameter
the name of the folder that contains Dockerfile, which is also the name of the image.
For example: `python scripts/build.py base_image` builds the base image, and
`python scripts/build.py astro-default` builds the default image, etc.

- The Dockerfile of each image (other than `base_image`) should start from the base image.

- Starting from `base_image` will trigger the `ONBUILD` sections defined in the
`base_image/Dockerfile`, which include:
  - If `apt.txt` exits, it will be parsed for the list of the system software to be installed with `apt-get`.
  - If `build-*` files exist, the scripts are run during the build.
  - If `conda-{env}.yml` exists, it defines a conda environment called `{env}`, which typically what gets modified by hand.
  - Additionally, if `conda-{env}-lock.yml` exists, it locks
the versions of the installed libraries. To create this `-lock` file, or updated it, pass `--update-lock` to the
build script `scripts/build.py`. This will first create or update the conda environment from the `conda-{env}.yml` file, then generate a new `conda-{env}-lock.yml` from the installed packages.
  - If `introduction.md` file exists, it is copied to `/opt/scritps`, then copied to the user's `~/notebooks` (by the pre-notebook script) and serve as a landing page (through `JUPYTERHUB_DEFAULT_URL` defined in the jupyterhub depolyment code).

The recommonded workflow is therefore like this:

- Define the libraries requirement in `conda-{env}.yml`.

- Build the image with `python scripts/build.py {image-name} --update-lock`.

- This will generate `conda-{env}-lock.yml`, which should be kept under
version control. The next time the image is built with `python scripts/build.py {image-name}`, the lock
file will be used inside the Dockerfile to reproduce the exact build.

# The images
- `base_image`: is the base image that all other images should start from. It contains jupyter and the basic tools needed for deployment in the fornax project.

- `astro-default`: Main Astro image that was used for the demo notebooks. It contains tractor and other general useful tools.

- `heasoft`: high energy image containing heasoft.

