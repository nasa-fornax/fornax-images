# ONBUILD instructions in base-image/Dockerfile are used to
# perform certain actions based on the presence of specific
# files (such as conda-linux-64.lock, start) in this repo.
# Refer to the base-image/Dockerfile for documentation.
ARG BASE_IMAGE_TAG=latest
ARG IMAGE_TAG=latest
ARG REPOSITORY=fornax-core/images
FROM ghcr.io/${REPOSITORY}/base_image:${BASE_IMAGE_TAG}

LABEL org.opencontainers.image.ref.name="Fornax Default Astrophysics"
LABEL gov.nasa.smce.fornax.jupyterhub.base_image="${BASE_IMAGE_TAG}"
LABEL gov.nasa.smce.fornax.jupyterhub.image="${IMAGE_TAG}"
LABEL gov.nasa.smce.fornax.jupyterhub.repository="${REPOSITORY}"
# add notebook updater script to run when jupyter starts
USER root
COPY --chmod=0755 update-notebooks.sh /usr/local/bin/before-notebook.d
USER $NB_USER

# For firefly
ENV FIREFLY_URL=https://irsa.ipac.caltech.edu/irsaviewer
