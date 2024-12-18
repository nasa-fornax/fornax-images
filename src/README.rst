New Fornax Images Repo (alpha)
==============================

This repo houses Dockerfiles and supporting files for the "base_image", and
"tractor" images within subdirectories of this repo.  (It also houses heasoft,
but that is currently disabled until we can package it in such a way that it
doesn't need to compile every time).

It also includes three GitHub workflows:

- A workflow which will build images related to the branch being checked into
  (e.g. "main").

- A workflow that runs on release that tags the latest "main" image with the
  release tag and a symbolic rolling tag "stable".

- A workflow that runs the tests of the building and tagging machinery.

For each image built, it is pushed to the GitHub container registry associated
with this repostory.

Notable Changes and Questions
=============================

- We use GitHub Container Registry instead of Amazon's.

- Instead of image names like ``fornax_images:base-image-XYZ``, and
  ``fornax_images:heasoft-XYZ``, we produce images like ``base_image:XYZ`` and
  ``tractor:XYZ`` as it is easy enough to do when we use the GitHub container
  registry, and it's more "normal".

- All of the logic to build and push (or not build or push) exists within
  ``src/buildimages.py``, which is executed by the GitHub workflow actions
  defined within ``.github/workflows/images.yml``.

- The event that fires off the worfklow that produces the images is currently a
  a push or pull request event.  It happens on every push for every branch.

- The event that creates "imagename:v0.1.1" tags is a release event.  It tags
  all "main" images as released using the release tag name supplied plus a
  symbolic "stable" tag.

- ``src/buildimages.py`` can be run standalone from any machine that is logged
  in to a GitHub account with an API token that permitted to create "packages"
  using ``docker login`` .  In this mode, all images will be built and pushed
  the same as if a release was made, although a GitHub release will not
  actually be made.

- There are several other Dockerfiles in the older GitLab fornax-images repo.
  They seemed at a quick glance unrelated to the others because they didn't use
  the base image.  Can we confirm?

- The limitations of a free GitHub account with respect to action runners
  appears to be these:

  - Only one runner may be available at any time.

  - The active runner is executed on a run-of-the-mill machine.

  - The runner cannot be self-hosted.

Findings
========

- With or without an enterprise subscripion, you can fork a repository into
  another repository in the same organization (e.g. nasa/fornax-images to
  nasa/fornax-images2).  It requires the appropriate permissions granted to the
  forking user from the organization manager.
  https://github.blog/changelog/2022-06-27-improved-innersource-collaboration-and-enterprise-fork-policies/.

- When you fork a repo with workflows in it, initially the workflows are
  disabled.  You can enable the workflows by visiting the Actions tab within
  the fork and clicking the button to reenable them.  Then the forked repo
  actions work just like the original repo actions, and can contain their own
  registries, etc.

  
