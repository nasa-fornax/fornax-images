# ONBUILD instructions in base-image/Dockerfile are used to
# perform certain actions based on the presence of specific
# files (such as conda-linux-64.lock, start) in this repo.
# Refer to the base-image/Dockerfile for documentation.
ARG BASE_TAG=latest
ARG REPOSITORY=nasa-fornax/fornax-images
ARG REGISTRY=ghcr.io

FROM ${REGISTRY}/${REPOSITORY}/base_image:${BASE_TAG}

LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description "Fornax Main Astronomy Image"
LABEL org.opencontainers.image.authors="Fornax Project"

# add notebook updater script to run when jupyter starts
USER root
COPY --chmod=0755 update-notebooks.sh /usr/local/bin/before-notebook.d
USER $NB_USER

# For firefly
ENV FIREFLY_URL=https://irsa.ipac.caltech.edu/irsaviewer
