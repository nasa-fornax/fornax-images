ARG BASE_TAG=latest
ARG REPOSITORY=nasa-fornax/fornax-images
ARG REGISTRY=ghcr.io

FROM ${REGISTRY}/${REPOSITORY}/jupyter-base:${BASE_TAG}

LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax Base Image"
LABEL org.opencontainers.image.authors="Fornax Project"

ARG SUPPORT_DATA_MOUNT=/shared-storage/support-data
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
    # for vscode
    CODE_EXECUTABLE=code-server \
    CODE_EXTENSIONSDIR=$HOME/.local/share/code-server/extensions \
    NOTEBOOK_DIR=/opt/notebooks \
    # support data; JH can pass ARG SUPPORT_DATA_MOUNT; SUPPORT_DATA_DIR points to it
    # scripts that rely on support data should use SUPPORT_DATA_DIR
    SUPPORT_DATA_DIR=/opt/support-data \
    # path
    PATH=$MAMBA_ROOT_PREFIX/bin:$PATH \
    # For firefly
    FIREFLY_URL=https://irsa.ipac.caltech.edu/irsaviewer \
    # for dask
    DASK_DISTRIBUTED__DASHBOARD__LINK="/jupyter/user/{JUPYTERHUB_USER}/proxy/{port}/status"


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
COPY --chmod=0777 --chown=$NB_UID:$NB_GID scripts/*.sh update-notebooks.sh link-notebooks.sh /usr/local/bin/
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
&& timeout 20s jupyterhub-singleuser || true

# Install system packages with micromamba
# we use microconda instead of apt, so they are portable
COPY --chown=$NB_UID:$NB_GID base.txt /tmp/
RUN PY_EXACT_VERSION=`python -c "import sys; print(sys.version.split()[0])"` \
 && micromamba create -y -p $MAMBA_ROOT_PREFIX python=$PY_EXACT_VERSION \
 && xargs -a /tmp/base.txt micromamba install -y -p $MAMBA_ROOT_PREFIX \
 && micromamba clean -yaf && rm /tmp/base.txt \
 && micromamba env export -p $MAMBA_ROOT_PREFIX > $MAMBA_ROOT_PREFIX/base-lock.yml \
 && cp $MAMBA_ROOT_PREFIX/base-lock.yml $LOCK_DIR/ \
 # we want our micromamba envs 1) in $ENV_DIR so they are portable,
 # but the same time 2) we want to be able to activate them with
 # micromamba activate env_name.
 # 1, requires them under $ENV_DIR
 # 2, requires them under MAMBA_ROOT_PREFIX/envs
 # the solution is make MAMBA_ROOT_PREFIX/envs a symlin to $ENV_DIR
 && cd $MAMBA_ROOT_PREFIX && rm -rf envs && ln -s $ENV_DIR

## install DEFAULT_ENV ##
COPY --chown=$NB_UID:$NB_GID requirements-$DEFAULT_ENV.txt /tmp/
RUN cd /tmp/ && bash /usr/local/bin/uv-env-install.sh \
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
COPY add-dot-profile.sh /usr/local/bin/before-notebook.d/
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
# Add ldap-related config; related to libnss-ldap
RUN \
# && sed -i 's/passwd:         files/passwd:         files ldap/g' /etc/nsswitch.conf \
# && sed -i 's/group:          files/group:          files ldap/g' /etc/nsswitch.conf \
cat <<'EOF' > /etc/ldap.conf
base dc=fornax,dc=core              
uri ldap://glauth.fornax.core:30389 
ldap_version 3                      
binddn cn=svcacct,dc=fornax,dc=core
bindpw T3mp3rman3nt 
pam_password clear
EOF

# reset user and location
WORKDIR ${HOME}
USER $NB_USER


# For outside mount when using outside fornax
RUN mkdir -p /opt/workspace
VOLUME /opt/workspace

# landing page; even an empty one
COPY --chown=$NB_UID:$NB_GID --chmod=644 introduction.md* $JUPYTER_DIR
RUN cd $JUPYTER_DIR \
    && if test -f introduction.md; then \
      pandoc introduction.md -o introduction.html --standalone --metadata title="Welcome to Fornax Science Console!"; \
    fi

# Add the notebooks to the image
RUN update-notebooks.sh && link-notebooks.sh


# Support data location; SUPPORT_DATA_DIR -> SUPPORT_DATA_MOUNT
# SUPPORT_DATA_MOUNT can be set by JH
RUN ln -s $SUPPORT_DATA_MOUNT $SUPPORT_DATA_DIR

ARG BUILD_VERSION=0
USER root
RUN IFS=: read -r name ver <<< "$BUILD_VERSION" && echo "$ver" >> $LOCK_DIR/build-$name
USER $NB_USER

# ==== Start ONBUILD commands ==== #
# These commands run in images the inherit fornax-images
# ================================ #

# add version number
ONBUILD ARG BUILD_VERSION=0
ONBUILD USER root
ONBUILD RUN IFS=: read -r name ver <<< "$BUILD_VERSION" && echo "$ver" >> $LOCK_DIR/build-$name
ONBUILD USER $NB_USER

# Install any uv/conda environments and call build-* scripts
ONBUILD RUN mkdir -p $HOME/build
ONBUILD COPY --chown=$NB_UID:$NB_GID build-* requirements-* conda-* $HOME/build/
ONBUILD USER $NB_USER

# # setup uv environments
ONBUILD RUN cd build && bash /usr/local/bin/uv-env-install.sh \
 && bash /usr/local/bin/conda-env-install.sh
# # ----------------------- #

# Any other build-* scripts; e.g. build tractor, heasoft etc #
ONBUILD RUN cd build \
 ; for script in `ls build-*`; do \
 echo "Found script ${script} ..." \
 && chmod +x $script \
 && ./$script \
 ; done
# --------------------------- #

# Update the notebooks
ONBUILD RUN update-notebooks.sh


ONBUILD RUN rm -r $HOME/build
ONBUILD USER ${NB_USER}
ONBUILD WORKDIR ${HOME}
