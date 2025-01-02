# ONBUILD instructions in base-image/Dockerfile are used to
# perform certain actions based on the presence of specific
# files (such as conda-linux-64.lock, start) in this repo.
# Refer to the base-image/Dockerfile for documentation.
ARG BASE_TAG=latest
ARG REPOSITORY=nasa-fornax/fornax-images
ARG REGISTRY=ghcr.io

FROM ${REGISTRY}/${REPOSITORY}/base_image:${BASE_TAG}


LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description "Fornax High Energy Astronomy Image"
LABEL maintainer="Fornax Project"

# set default conda env
ENV CONDA_ENV=notebook


LABEL org.opencontainers.image.ref.name="Fornax High Energy Astrophysics"
LABEL gov.nasa.smce.fornax.jupyterhub.image="${IMAGE_TAG}"
LABEL gov.nasa.smce.fornax.jupyterhub.base_image="${BASE_IMAGE_TAG}"
LABEL gov.nasa.smce.fornax.jupyterhub.repository="${REPOSITORY}"
