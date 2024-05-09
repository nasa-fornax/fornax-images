# fornax-images
This repo contains the Docker images for the Fornax Platform deployments.
It captures reproducible computing environments, and it follows the
structure used by [Pangeo](https://github.com/pangeo-data/pangeo-docker-images).

Each image is in its own directory.
`base-image` is a base image that contains basic JupyterHub and Lab setup.
Other images should use it as a starting point.

# Content
- `base_image`: is the base image that all other images should start from. It contains jupyter and the basic tools needed for deployment in the fornax project.

- `tractor`: Main Astro image that was used for the demo. It contains tractor and other general useful tools.

- `heasoft`: high energy image containing heasoft.

# Adding New Images
TODO
