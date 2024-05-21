# fornax-images
This repo contains the Docker images for the Fornax Platform deployments.
It produces reproducible computing environments. Some of the parts are
adapted from the [Pangeo](https://github.com/pangeo-data/pangeo-docker-images) project.

Reproducibility is achived by keeping track of the software environments using conda-lock.
The following is a general description of the images:

- Each image is in its own directory (e.g. `base-image` and `tractor`).
- `base-image` is a base image that contains basic JupyterHub and Lab setup.
Other images should use it as a starting point.
- Jupyterlab is installed in a conda environment called `notebook`, and it is the
default environment when running the images.
- The `build.py` script should be used when building the image. It takes as parameter
the name of the folder that contains Dockerfile, which is also the name of the image.
For example: `python build.py base-image` build the base image, and
`python build.py tractor` builds the tractor image.
- The Dockerfile of each image (other than `base-image`) should start from the base image:
`FROM fornax/base-image:latest`. That will trigger the `ONBUILD` sections defined in the
`base-image/Dockerfile`, which include:
  - If `apt.txt` exits, it will parsed for the list of the system software to be installed with `apt-get`.
  - If `postBuild*` files exist, the scripts are run during the build.
  - If `conda-{env}.yml` exists, it defines a conda environment called `{env}`.
  - Additionally, if `conda-{env}-lock.yml` exists, it defines a `conda-lock` file that locks
the versions of the installed libraries. To create it, or updated it, pass `--update-lock` to the
build script `build.py`. This will first generate a conda environment file from what is installed in the
conda environment, then use `conda-lock` to lock the versions, and then generate human-readable `packages.txt`
that contains a list of installed libraries and their versions.

The recommonded workflow is therefore like this:
- Define the libraries requirement from some conda environment `{env}` in `conda-{env}.yml`.
- Build the image with `python build.py {image-name} --update-lock`.
- This will generate: `conda-{env}-lock.yml` and `packages.txt`. Both these should be kept under
verson control. The next time the image is built with `python build.py {image-name}`, the lock
file will be used inside Dockerfile to reproduce the exact build.

# The image
- `base_image`: is the base image that all other images should start from. It contains jupyter and the basic tools needed for deployment in the fornax project.

- `tractor`: Main Astro image that was used for the demo. It contains tractor and other general useful tools.

- `heasoft`: high energy image containing heasoft.

