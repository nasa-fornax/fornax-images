# ONBUILD instructions in base-image/Dockerfile are used to
# perform certain actions based on the presence of specific
# files (such as conda-linux-64.lock, start) in this repo.
# Refer to the base-image/Dockerfile for documentation.
ARG BASE_TAG=latest
ARG REPOSITORY=nasa-fornax/fornax-images
ARG REGISTRY=ghcr.io

FROM ${REGISTRY}/${REPOSITORY}/fornax-main:develop

# LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
# LABEL org.opencontainers.image.description="Fornax Main Astronomy Image"
# LABEL org.opencontainers.image.authors="Fornax Project"


# # For firefly
# ENV FIREFLY_URL=https://irsa.ipac.caltech.edu/irsaviewer

# TEMP: remove /opt/
USER root
RUN rm -rf /opt/ \
 && rm -rf /usr/local/bin/before-notebook.d/* \
 && sed -i '/activate/d' /etc/bash.bashrc \
 && mkdir -p /opt2/ \
 && fix-permissions /opt2

USER ${NB_USER}
ENV PATH=/opt2/py3/bin:$PATH
RUN cd /opt2/ \
 && uv venv py3 \
 && VIRTUAL_ENV=/opt2/py3 uv pip install jupyterlab jupyterhub
