# ONBUILD instructions in base-image/Dockerfile are used to
# perform certain actions based on the presence of specific
# files (such as conda-linux-64.lock, start) in this repo.
# Refer to the base-image/Dockerfile for documentation.
ARG BASE_TAG=latest
ARG REPOSITORY=nasa-fornax/fornax-images
ARG REGISTRY=ghcr.io

FROM ${REGISTRY}/${REPOSITORY}/fornax-base:${BASE_TAG}


LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax High Energy Astronomy Image"
LABEL org.opencontainers.image.authors="Fornax Project"

# set default conda env
ENV DEFAULT_ENV=heasoft

#
# As the Fornax-Hea image that results from these installation scripts is no longer loaded directly into Fornax, and
#  is instead split up so that the large software packages are served in Amazon Machine Images (AMI), we can
#  must take some steps to ensure that this image is usable on platforms other than Fornax.
# This includes making a real, root-level, shared-storage/support-data directory (which on Fornax proper is mounted
#  from an AWS storage solution), so that the high-energy software installations can be shipped with the necessary
#  support data in the same place it will be on Fornax itself
USER root
RUN mkdir -p /shared-storage/support-data

# Return to the notebook user
USER $NB_USER