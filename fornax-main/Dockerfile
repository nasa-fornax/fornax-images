ARG BASE_TAG=latest
ARG REPOSITORY=ghcr.io/nasa-fornax/fornax-images

FROM ${REPOSITORY}/env-core:${BASE_TAG} AS env_core
FROM ${REPOSITORY}/fornax-nb:${BASE_TAG} AS fornax_nb
FROM ${REPOSITORY}/archive-nb:${BASE_TAG} AS archive_nb
FROM ${REPOSITORY}/fornax-jupyter:${BASE_TAG}


LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax Main Image"
LABEL org.opencontainers.image.authors="Fornax Project"

# Copy from env-core #
RUN --mount=type=bind,from=env_core,source=/opt/,target=/tmp/opt \
    cp -r /tmp/opt/envs/Renv /opt/envs/Renv \
 && cp -r /tmp/opt/envs/julia-* /opt/envs/ \
 && cp -r /tmp/opt/envs/python3 /opt/envs/ \
 && cp -r /tmp/opt/envs/base /opt/envs/ \
 && cp -r /tmp/opt/envs/lock/requirements-python3.txt /opt/envs/lock/ \
 && cp -r /tmp/opt/envs/lock/build-env-core /opt/envs/lock/ \
 && cp -r /tmp/opt/envs/lock/julia /opt/envs/lock/ \
 && cp -r /tmp/opt/jupyter/share/jupyter/kernels/* /opt/jupyter/share/jupyter/kernels/

ARG JULIA_VERSION=1.8.0
ENV JULIA_DEPOT_PATH=$ENV_DIR/julia-$JULIA_VERSION \
    JULIA_PKGDIR=$ENV_DIR/julia-$JULIA_VERSION \
    PATH=$ENV_DIR/julia-$JULIA_VERSION/bin:$PATH

ENV DEFAULT_ENV=python3
# ------------------- #

# Copy from fornax-nb #
RUN --mount=type=bind,from=fornax_nb,source=/opt/,target=/tmp/opt \
    cp -r /tmp/opt/envs/py-* /opt/envs/ \
 && cp -r /tmp/opt/notebooks/* /opt/notebooks/ \
 && cp -r /tmp/opt/envs/lock/requirements-py-* /opt/envs/lock/ \
 && cp -r /tmp/opt/envs/lock/build-fornax-nb /opt/envs/lock/ \
 && cp -r /tmp//opt/jupyter/share/jupyter/kernels/py-* /opt/jupyter/share/jupyter/kernels/
# ------------------- #

# Copy from archive-nb #
RUN --mount=type=bind,from=archive_nb,source=/opt/,target=/tmp/opt \
    cp -r /tmp/opt/envs/py-* /opt/envs/ \
 && cp -r /tmp/opt/notebooks/* /opt/notebooks/ \
 && cp -r /tmp/opt/envs/lock/requirements-py-* /opt/envs/lock/ \
 && cp -r /tmp/opt/envs/lock/py-spherex_sdt-lock.yml /opt/envs/lock/ \
 && cp -r /tmp/opt/envs/lock/build-archive-nb /opt/envs/lock/
# ------------------- #