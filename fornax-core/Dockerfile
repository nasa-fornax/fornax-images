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
RUN PY_EXACT_VERSION=`python -c "import sys; print(sys.version.split()[0])"` \
 && micromamba create -y -p $MAMBA_ROOT_PREFIX python=$PY_EXACT_VERSION \
 && xargs -a /tmp/base.txt micromamba install -y -p $MAMBA_ROOT_PREFIX \
 && micromamba clean -yaf && rm /tmp/base.txt \
 && micromamba env export -p $MAMBA_ROOT_PREFIX > $MAMBA_ROOT_PREFIX/base-lock.yml \
 && cp $MAMBA_ROOT_PREFIX/base-lock.yml $LOCK_DIR/ \
 && fix-permissions $MAMBA_ROOT_PREFIX \
 # we want our micromamba envs 1) in $ENV_DIR so they are portable,
 # but the same time 2) we want to be able to activate them with
 # micromamba activate env_name.
 # 1, requires them under $ENV_DIR
 # 2, requires them under MAMBA_ROOT_PREFIX/envs
 # the solution is make MAMBA_ROOT_PREFIX/envs a symlin to $ENV_DIR
 && cd $MAMBA_ROOT_PREFIX && rm -rf envs && ln -s $ENV_DIR

## install DEFAULT_ENV ##
COPY --chown=$NB_UID:$NB_GID $DEFAULT_ENV.txt /tmp/requirements-$DEFAULT_ENV.txt
RUN cd /tmp/ && bash /usr/local/bin/setup-pip-env <<< yes \
 # fix the display name of DEFAULT_ENV
 && $ENV_DIR/$DEFAULT_ENV/bin/python -m ipykernel install --name $DEFAULT_ENV \
    --prefix $JUPYTER_DIR --display-name "$DEFAULT_ENV"
## ------------------- ##
