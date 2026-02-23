ARG BASE_TAG=latest
ARG REPOSITORY=nasa-fornax/fornax-images
ARG REGISTRY=ghcr.io

FROM ${REGISTRY}/${REPOSITORY}/jupyter-base:${BASE_TAG}

LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax Base Image"
LABEL org.opencontainers.image.authors="Fornax Project"

ARG MAMBA_ROOT_PREFIX=$ENV_DIR/base


# Environment variables
ENV CACHE_DIR=/tmp/cache
ENV DEFAULT_ENV=python3 \
    MAMBA_ROOT_PREFIX=$MAMBA_ROOT_PREFIX \
    LOCK_DIR=$ENV_DIR/lock \
    XDG_CACHE_HOME=$CACHE_DIR \
    XDG_CACHE_DIR=$CACHE_DIR \
    XDG_CACHE_DIR=$CACHE_DIR \
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

# Copy our scripts
COPY --chmod=0555 --chown=$NB_UID:$NB_GID scripts/* update-notebooks.sh link-notebooks.sh /usr/local/bin/
COPY --chown=$NB_UID:$NB_GID parse_nb_manifest.py $JUPYTER_DIR/bin/

# Support data location; SUPPORT_DATA_DIR -> SUPPORT_DATA_MOUNT
# SUPPORT_DATA_MOUNT is used here to allow the images to be used
# outside the platform; in the platform, this is replaced by JH deployment
RUN SUPPORT_DATA_MOUNT=/shared-storage/support-data \
 && mkdir -p $SUPPORT_DATA_MOUNT \
 && ln -s $SUPPORT_DATA_MOUNT $SUPPORT_DATA_DIR \
 && fix-permissions $SUPPORT_DATA_MOUNT

USER $NB_USER


# add packages to jupyter environment; mainly labextensions
COPY --chown=$NB_UID:$NB_GID jupyter-requirements.txt /tmp/
RUN export VIRTUAL_ENV=$JUPYTER_DIR \
 && uv pip install --no-cache -r /tmp/jupyter-requirements.txt \
 # get the latest fornax-labextension
 && curl -s "https://api.github.com/repos/nasa-fornax/fornax-labextension/releases/latest" -o /tmp/latest.json \
 && whlurl=`python -c "import json; d = json.loads(open('/tmp/latest.json').read()); print(d['assets'][0]['browser_download_url'])"` \
 && whlfile=`basename $whlurl` \
 && curl -sSLO $whlurl \
 && uv pip install --no-cache ./$whlfile \
 && rm -rf $whlfile jupyter-requirements.txt latest.json \
 && uv cache clean \
 # update lock file and make a copy in LOCK_DIR
 && uv pip list --format=freeze > $JUPYTER_DIR/requirements-jupyter.txt \
 && mkdir -p $LOCK_DIR \
 && cp $JUPYTER_DIR/requirements-jupyter.txt $LOCK_DIR/requirements-jupyter.txt \
# run jupyterhub-singleuser once to cache the extension and speedup the start
&& timeout 20s jupyterhub-singleuser || true \
&& fix-permissions $JUPYTER_DIR

# Install system packages with micromamba
# we use microconda instead of apt, so they are portable
COPY --chown=$NB_UID:$NB_GID base.txt /tmp/
RUN PY_EXACT_VERSION=`python -c "import sys; print(sys.version.split()[0])"` \
 && mkdir -p $ENV_DIR && fix-permissions $ENV_DIR \
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
COPY --chown=$NB_UID:$NB_GID requirements-$DEFAULT_ENV.txt /tmp/
RUN cd /tmp/ && bash /usr/local/bin/setup-pip-env <<< yes \
 # fix the display name of DEFAULT_ENV
 && $ENV_DIR/$DEFAULT_ENV/bin/python -m ipykernel install --name $DEFAULT_ENV \
    --prefix $JUPYTER_DIR --display-name "$DEFAULT_ENV"
## ------------------- ##


# Make $DEFAULT_ENV default; do it at the global level
# because ~/.bashrc is not loaded when user space is mounted
# Also, add it to before-notebook.d main script
USER root
RUN cat <<ACTIVATE > /tmp/activate.sh
#!/usr/bin/bash
if [ -f \$ENV_DIR/\$DEFAULT_ENV/bin/activate ]; then
  echo activating python in \$ENV_DIR/\$DEFAULT_ENV
  source \$ENV_DIR/\$DEFAULT_ENV/bin/activate
elif [ -d \$ENV_DIR/\$DEFAULT_ENV/conda-meta ]; then
  echo activating python in \$ENV_DIR/\$DEFAULT_ENV
  micromamba activate \$DEFAULT_ENV
else
  echo DEFAULT_ENV=\$DEFAULT_ENV not found
fi
ACTIVATE
COPY misc-setup.sh /usr/local/bin/before-notebook.d/
RUN cat /tmp/activate.sh >> /etc/bash.bashrc \
 && cat /tmp/activate.sh  >> /usr/local/bin/before-notebook.d/10activate-env.sh \
 && echo "bash /usr/local/bin/link-notebooks.sh" > /usr/local/bin/before-notebook.d/20link-notebooks.sh \
 && rm -r /tmp/* $HOME/.*

# Add any system packages. We want them all to be here fornax-base
# so they can be transfered to fornax-slim
COPY apt.txt* /tmp/
RUN cd /tmp/ && \
    if test -f apt.txt; then \
      xargs bash /usr/local/bin/apt-install.sh; \
      rm apt.txt; \
    fi

# reset user and location
WORKDIR ${HOME}
USER $NB_USER


# For outside mount when using outside fornax
RUN mkdir -p /opt/workspace
VOLUME /opt/workspace

# landing page; even an empty one
COPY --chown=$NB_UID:$NB_GID --chmod=644 introduction.md* changes.md* $JUPYTER_DIR

# Add the notebooks to the image
RUN update-notebooks.sh && link-notebooks.sh


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

# # setup uv environments
ONBUILD RUN cd build && bash /usr/local/bin/setup-pip-env <<< yes \
 && bash /usr/local/bin/setup-conda-env <<< yes
# # ----------------------- #

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
