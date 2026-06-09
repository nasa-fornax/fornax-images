ARG BASE_TAG=latest
ARG REPOSITORY=ghcr.io/nasa-fornax/fornax-images

FROM ${REPOSITORY}/fornax-base:${BASE_TAG} AS builder

LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax Core Image"
LABEL org.opencontainers.image.authors="Fornax Project"


USER $NB_USER

# Install system packages with micromamba
# we use micromamba instead of apt, so they are portable
COPY --chown=$NB_UID:$NB_GID base.txt /tmp/
RUN xargs -a /tmp/base.txt micromamba install -y -p $MAMBA_ROOT_PREFIX \
 && micromamba clean -yaf && rm /tmp/base.txt \
 && micromamba env export -p $MAMBA_ROOT_PREFIX > $MAMBA_ROOT_PREFIX/base-lock.yml \
 && cp $MAMBA_ROOT_PREFIX/base-lock.yml $LOCK_DIR/ \
 && fix-permissions $MAMBA_ROOT_PREFIX

## install DEFAULT_ENV ##
COPY --chown=$NB_UID:$NB_GID $DEFAULT_ENV.txt /tmp/requirements-$DEFAULT_ENV.txt
RUN cd /tmp/ && bash /usr/local/bin/setup-pip-env <<< yes \
 # fix the display name of DEFAULT_ENV
 && $ENV_DIR/$DEFAULT_ENV/bin/python -m ipykernel install --name $DEFAULT_ENV \
    --prefix $JUPYTER_DIR --display-name "$DEFAULT_ENV" \
 && rm -rf requirements-$DEFAULT_ENV.txt
## ------------------- ##


# setup julia #
ARG JULIA_VERSION=1.8.0
ENV JULIA_DEPOT_PATH=$ENV_DIR/julia-$JULIA_VERSION \
    JULIA_PKGDIR=$ENV_DIR/julia-$JULIA_VERSION \
    PATH=$ENV_DIR/julia-$JULIA_VERSION/bin:$PATH
COPY --chown=$NB_UID:$NB_GID setup-julia.sh /tmp/
RUN bash /tmp/setup-julia.sh && rm /tmp/setup-julia.sh
# ------------- #
