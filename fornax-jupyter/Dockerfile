ARG BASE_TAG=latest
ARG REPOSITORY=ghcr.io/nasa-fornax/fornax-images

FROM ${REPOSITORY}/fornax-base:${BASE_TAG} AS builder

LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax Jupyter Image"
LABEL org.opencontainers.image.authors="Fornax Project"


# Copy our jupyter settings overrides
USER root
RUN mkdir -p $JUPYTER_DIR/share/jupyter/lab/settings/ \
 # Disable the announcement extension
 && jupyter labextension disable "@jupyterlab/apputils-extension:announcements" \
 && fix-permissions $JUPYTER_DIR
COPY --chown=$NB_UID:$NB_GID overrides.json $JUPYTER_DIR/share/jupyter/lab/settings/
# Copy our jupyter server config file
COPY jupyter_server_config.py /tmp/
RUN cat /tmp/jupyter_server_config.py >> /etc/jupyter/jupyter_server_config.py
USER $NB_USER


# add packages to jupyter environment; mainly labextensions
COPY --chown=$NB_UID:$NB_GID jupyter-deps.txt /tmp/
RUN export VIRTUAL_ENV=$JUPYTER_DIR \
 && uv pip install --no-cache -r /tmp/jupyter-deps.txt \
 && rm -rf jupyter-deps.txt \
 && uv cache clean \
 # update lock file and make a copy in LOCK_DIR
 && uv pip list --format=freeze > $JUPYTER_DIR/requirements-jupyter.txt \
 && cp $JUPYTER_DIR/requirements-jupyter.txt $LOCK_DIR/requirements-jupyter.txt \
 && fix-permissions $JUPYTER_DIR