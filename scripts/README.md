# Fornax Images Repo (beta)

This repo houses Dockerfiles for building the Fornax Science Environment images.
Each image is hosted in its directory. base-image is the base image that all
others start from.

It also includes three GitHub workflows:

- `image-build.yml`: build images whose code has changed in a push commit. The images
 will be tagged with branch name (e.g. `base-image:fix-issue-1` or `astro-default:fix-issue-34`).
 The images will be built and pushed to the container registry of the repo.

 This happens for every GitHub branch, not just "main".

  NB: when `base-image` changes, its dependencies will **not** be rebuilt against the new
  `base-image` unless files change in that image itself.

- `release.yml`: runs on a release, and it tags the image from which the release is
 coming from (typically main) with a release tag and symbolic tag named 'stable'.

- A workflow that runs the tests of the building scripts and tagging machinery when
  anything in "scripts" changes.

For each image built, it is pushed to the GitHub container registry associated
with this repository.

See the "Packages" link on the right hand side of the main repository page for
a list of images in the container registry.

See the "Actions" tab of the repository to see the results of each workflow.

NB: The code in this directory has only been tested with Python3.11 and better.

# Notable Changes After Moving to GH

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

- `src/build.py` can be run standalone from any machine.  It can only
  push images if it is logged in to a GitHub account with an API token that
  permitted to create "packages" using `docker login` .

- The limitations of a free GitHub account with respect to action runners
  appears to be these:

  - Only one runner may be available at any time.

  - The active runner is executed on a run-of-the-mill machine.

  - The runner cannot be self-hosted.
