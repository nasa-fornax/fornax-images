
ARG BASE_TAG=latest
ARG REPOSITORY=nasa-fornax/fornax-images
ARG REGISTRY=ghcr.io

FROM ${REGISTRY}/${REPOSITORY}/fornax-main:${BASE_TAG} as base

FROM scratch

# Copy everything *except* the folder you want to remove
COPY --from=base / /

#RUN rm -rf /opt/envs /usr/local/bin/before-notebook.d/10activate-conda-env.sh
# RUN mv /opt/envs /opt/software \
#  && find "/opt/jupyter/share/jupyter" -name "kernel.json" -exec sed -i 's|/opt/envs/|/opt/software/|g' {} +
RUN rm -rf /opt/envs

ENV ENV_DIR=/opt/envs

ARG NB_USER="jovyan"
ARG NB_UID="1000"
ARG NB_GID="100"

ENV JUPYTER_DIR=/opt/jupyter \
    SHELL=/bin/bash \
    NB_USER="${NB_USER}" \
    NB_UID=${NB_UID} \
    NB_GID=${NB_GID} \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    LANGUAGE=C.UTF-8

ENV PATH="${JUPYTER_DIR}/bin:${PATH}" \
    HOME="/home/${NB_USER}" \
    MAMBA_ROOT_PREFIX=/opt/

ENTRYPOINT ["tini", "-g", "--", "start.sh"]

ARG JUPYTER_PORT=8888
EXPOSE $JUPYTER_PORT

# Configure container startup
CMD ["start-notebook.py"]

HEALTHCHECK --interval=3s --timeout=1s --start-period=3s --retries=3 \
    CMD /etc/jupyter/docker_healthcheck.py || exit 1

ENV PYTHON_VERSION=3.12
ENV UV_PYTHON_INSTALL_DIR=${ENV_DIR}/.uv

ENV DEFAULT_ENV=python3 \
    LOCK_DIR=/opt/lock
ENV CACHE_DIR=/tmp/cache
ENV XDG_CACHE_HOME=$CACHE_DIR \
    XDG_CACHE_DIR=$CACHE_DIR \
    XDG_CACHE_DIR=$CACHE_DIR \
    PIP_CACHE_DIR=$CACHE_DIR/pip \
    UV_CACHE_DIR=$CACHE_DIR/uv
ENV CODE_EXECUTABLE=code-server

VOLUME /opt/workspace

ENV NOTEBOOK_DIR=/opt/notebooks \
    NOUPDATE=${HOME}/.no-notebook-update.txt \
    ADD_NOTEBOOKS=1

USER $NB_USER
WORKDIR $HOME