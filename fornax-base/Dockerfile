ARG BASE_TAG=latest
ARG REPOSITORY=ghcr.io/nasa-fornax/fornax-images

FROM ${REPOSITORY}/jupyter-base:${BASE_TAG}

LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax Base Image"
LABEL org.opencontainers.image.authors="Fornax Project"

ARG MAMBA_ROOT_PREFIX=$ENV_DIR/base


# Environment variables
ENV CACHE_DIR=/tmp/cache
ENV DEFAULT_ENV=jupyter \
    MAMBA_ROOT_PREFIX=$MAMBA_ROOT_PREFIX \
    LOCK_DIR=$ENV_DIR/lock \
    XDG_CACHE_HOME=$CACHE_DIR \
    XDG_CACHE_DIR=$CACHE_DIR \
    XDG_CACHE_DIR=$CACHE_DIR \
    TECTONIC_CACHE_DIR=$CACHE_DIR \
    PIP_CACHE_DIR=$CACHE_DIR/pip \
    UV_CACHE_DIR=$CACHE_DIR/uv \
    UV_LINK_MODE=copy \
    NOTEBOOK_DIR=/opt/notebooks \
    # folder that start.sh need to fix permissions for
    CHOWN_EXTRA=/opt/notebooks \
    CHOWN_EXTRA_OPTS="-R" \
    # Location of the support data
    SUPPORT_DATA_DIR=/opt/support-data \
    # path
    PATH=$MAMBA_ROOT_PREFIX/bin:$PATH

USER root

# Create folder and set premissions
RUN \
 for folder in $ENV_DIR $LOCK_DIR $NOTEBOOK_DIR; do \
   mkdir -p $folder; \
   fix-permissions $folder; \
 done

# Copy our scripts
COPY --chmod=0555 --chown=$NB_UID:$NB_GID scripts/* /usr/local/bin/

# Support data location; SUPPORT_DATA_DIR -> SUPPORT_DATA_MOUNT
# SUPPORT_DATA_MOUNT is used here to allow the images to be used
# outside the platform; in the platform, this is replaced by JH deployment
RUN SUPPORT_DATA_MOUNT=/shared-storage/support-data \
 && mkdir -p $SUPPORT_DATA_MOUNT \
 && ln -s $SUPPORT_DATA_MOUNT $SUPPORT_DATA_DIR \
 && fix-permissions $SUPPORT_DATA_MOUNT

# Make $DEFAULT_ENV default; do it at the global level
# because ~/.bashrc is not loaded when user space is mounted
# Also, add it to before-notebook.d main script
RUN cat /usr/local/bin/_activate.sh >> /etc/bash.bashrc \
 && cat /usr/local/bin/_activate.sh  >> /usr/local/bin/before-notebook.d/10activate-env.sh \
 && echo "bash /usr/local/bin/link-notebooks.sh" > /usr/local/bin/before-notebook.d/20link-notebooks.sh \
 && rm -r /usr/local/bin/_activate.sh /tmp/*

# Do any apt system packages
COPY apt.txt* /tmp/
RUN cd /tmp/ && \
  if test -f apt.txt; then \
    xargs bash /usr/local/bin/apt-install.sh; \
    rm apt.txt; \
  fi 

# reset user and location
WORKDIR ${HOME}
USER $NB_USER

# Add a base conda environment; include what we need in the scripts
RUN PY_EXACT_VERSION=`python -c "import sys; print(sys.version.split()[0])"` \
 && micromamba create -y -p $MAMBA_ROOT_PREFIX python=$PY_EXACT_VERSION \
 && micromamba install -y -p $MAMBA_ROOT_PREFIX jq git \
 && micromamba clean -yaf \
# we want our micromamba envs 1) in $ENV_DIR so they are portable,
# but the same time 2) we want to be able to activate them with
# micromamba activate env_name.
# 1, requires them under $ENV_DIR
# 2, requires them under MAMBA_ROOT_PREFIX/envs
# the solution is make MAMBA_ROOT_PREFIX/envs a symlin to $ENV_DIR
 && cd $MAMBA_ROOT_PREFIX && rm -rf envs && ln -s $ENV_DIR


# For outside mount when using outside fornax
RUN mkdir -p /opt/workspace
VOLUME /opt/workspace

ARG BUILD_VERSION=0
RUN IFS=: read -r name ver <<< "$BUILD_VERSION" && echo "$ver" >> $LOCK_DIR/build-$name

# ==== Start ONBUILD commands ==== #
# These commands run in images the inherit fornax-images
# ================================ #

# add version number
ONBUILD ARG BUILD_VERSION=0
ONBUILD RUN IFS=: read -r name ver <<< "$BUILD_VERSION" && echo "$ver" >> $LOCK_DIR/build-$name

# Install any uv/conda environments and call build-* scripts
ONBUILD RUN mkdir -p $HOME/build
ONBUILD COPY --chown=$NB_UID:$NB_GID build-* requirements-* conda-* $HOME/build/

ONBUILD USER $NB_USER


# setup uv and conda environments #
ONBUILD RUN cd build && bash /usr/local/bin/setup-pip-env <<< yes \
 && bash /usr/local/bin/setup-conda-env <<< yes
# ------------------------------- #

# Any other build-* scripts; e.g. build tractor, heasoft etc #
ONBUILD RUN cd build \
 ; for script in `ls build-*`; do \
 echo "Found script ${script} ..." \
 && chmod +x $script \
 && ./$script \
 ; done
# --------------------------- #


ONBUILD RUN rm -r $HOME/build
ONBUILD USER ${NB_USER}
ONBUILD WORKDIR ${HOME}
