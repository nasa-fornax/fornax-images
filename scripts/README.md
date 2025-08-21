# Fornax Images Repo

This repo houses Dockerfiles for building the Fornax Science Environment images.
Each image is hosted in its directory. fornax-base is the base image that all
others start from.

It also includes the following GitHub workflows:

- `image-build.yml`: build images whose code has changed in a push commit. The images
 will be tagged with branch name (e.g. `fornax-base:fix-issue-1` or `fornax-main:fix-issue-34`).
 The images will be built and pushed to the container registry of the repo.

 This happens for every GitHub branch, not just "main".

  NB: when `fornax-base` changes, its dependencies will **not** be rebuilt against the new
  `fornax-base` unless files change in that image itself.

- `release.yml`: runs on a release, and it tags the image from which the release is
 coming from (typically main) with a release tag and symbolic tag named 'stable'.

- `check-build-code.yml`: A workflow that runs the tests of the building scripts and
  tagging machinery when anything in "scripts" changes.

- `run-tests.yml`: Running some tests using the notebooks. Checking the environments,
  checking that the required packages are installed, and that all imports work. No full run.

For each image built, it is pushed to the GitHub container registry associated
with this repository.
When an new image is built, AWS endpoint is called to notify the aws ECR of an image change.
The next pull from the ECR pulls newly-built image from github.

See the "Packages" link on the right hand side of the main repository page for
a list of images in the container registry.

See the "Actions" tab of the repository to see the results of each workflow.

# Notable Changes

## 08-2025
- Disable --trigger-ecr in actions as pull-though cache is not working correctly

## 06-2025
- Lock files are copied to a single location `$LOCK_DIR`.
- Lock files are also released with every image release and available as github release assets.
- fornax-labextension is installed from a release on github rather from git (faster).
- re-organize build/release code in build.py so they are independent.
- refactor the release ci to handle lock files
- Some notebook requirement files need numpy<2.3; pinned temporary until things are fixed upstream.
- the introduction.md file is now a single file that is used in all images.

## 05-2025
- Add a starting jupyter base image: `jupyter-base` instead of the one from jupyter stack.
- Rename images to: `fornax-base`, `formax-main` and `fornax-hea`.
- `formax-main` uses separate environments for each notebeook. Also, the `notebook`
  environment is manged with `uv (pip)` rather than `conda` to resolve conflicts (#20).
- Lock files are stored in the images. In `$CONDA_DIR/env?/` for conda and `$ENV_DIR/{env}`
  for non-conda environments.

## Pre-04-2025
- We use GitHub Container Registry instead of Amazon's.

- Instead of image names like `fornax_images:base-image-XYZ`, and
  `fornax_images:heasoft-XYZ`, we produce images like `base-image:XYZ` and
  `astro-default:XYZ` as it is easy enough to do when we use the GitHub container
  registry, and it's more "normal".

- All of the logic to build and push (or not build or push) exists within
  `scripts/build.py`, which is executed by the GitHub workflow actions
  defined within `.github/workflows/image-build.yml`.

- The event that fires off the workflow that produces the images is currently a
  a push or pull request event.  It happens on every push for every branch.

- The event that creates "imagename:v0.1.1" tags is a GitHub release event.  It
  tags all "main" images as released using the release tag name supplied plus a
  symbolic "stable" tag.

- `src/build.py` can be run standalone from any machine with docker.  It can only
  push images if it is logged in to a GitHub account with an API token that
  permitted to create "packages" using `docker login` .

- The limitations of a free GitHub account with respect to action runners
  appears to be these:

  - Only one runner may be available at any time.

  - The active runner is executed on a run-of-the-mill machine.

  - The runner cannot be self-hosted.
