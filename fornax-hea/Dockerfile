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
USER root
RUN \
 # remove default uv activation
 sed -i '/bin\/activate/d' /etc/bash.bashrc \
 # activate DEFAULT_ENV
 && printf "\neval \"\$(conda shell.bash hook)\"\n\nconda activate $DEFAULT_ENV\n" >> /etc/bash.bashrc
USER $NB_USER
