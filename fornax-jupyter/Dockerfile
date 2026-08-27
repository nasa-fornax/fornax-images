# Copyright 2026, University of Maryland, All Rights Reserved

ARG BASE_TAG=latest
ARG REPOSITORY=ghcr.io/nasa-fornax/fornax-images

FROM ${REPOSITORY}/env-assets:${BASE_TAG} AS assets
FROM ${REPOSITORY}/fornax-base:${BASE_TAG} AS build


# Copy our jupyter settings overrides
USER $NB_USER
RUN mkdir -p $JUPYTER_DIR/share/jupyter/lab/settings/
 # Disable the announcement extension
 # && jupyter labextension disable "@jupyterlab/apputils-extension:announcements"
COPY --chown=$NB_UID:$NB_GID overrides.json $JUPYTER_DIR/share/jupyter/lab/settings/
COPY --chown=$NB_UID:$NB_GID page_config.json $JUPYTER_DIR/etc/jupyter/labconfig/
# Copy our jupyter server config file
COPY --chown=$NB_UID:$NB_GID jupyter_server_config.py /tmp/
RUN cat /tmp/jupyter_server_config.py >> /etc/jupyter/jupyter_server_config.py \
 && rm /tmp/jupyter_server_config.py


# add packages to jupyter environment; mainly labextensions & misc-build
COPY --chown=$NB_UID:$NB_GID jupyter-deps.txt scripts/misc-build.sh /tmp/
RUN export VIRTUAL_ENV=$JUPYTER_DIR \
 && uv pip install --no-cache -r /tmp/jupyter-deps.txt \
 && rm -rf jupyter-deps.txt \
 && uv cache clean \
 # update lock file and make a copy in LOCK_DIR
 && uv pip list --format=freeze > $JUPYTER_DIR/requirements-jupyter.txt \
 && cp $JUPYTER_DIR/requirements-jupyter.txt $LOCK_DIR/requirements-jupyter.txt \
 && bash /tmp/misc-build.sh \
 && fix-permissions $JUPYTER_DIR /tmp/cache \
 && find $JUPYTER_DIR \( -name "yarn.lock" -o -name "package-lock.json" \) -delete \
 && rm /tmp/jupyter-deps.txt /tmp/misc-build.sh

# Add the notebooks
COPY --from=assets $NOTEBOOK_DIR $NOTEBOOK_DIR

# landing page; even an empty one
COPY --chown=$NB_UID:$NB_GID --chmod=644 introduction.md $NOTEBOOK_DIR/introduction.mdv
COPY --chown=$NB_UID:$NB_GID --chmod=644 changes.md $NOTEBOOK_DIR/changes.mdv

# # Update the intro page with notebooks by parsing the manifests
COPY --chown=$NB_UID:$NB_GID scripts/parse_nb_manifest.py /tmp/
RUN \
  if [ -f /tmp/parse_nb_manifest.py ]; then \
    echo "Parsing manifests of archive notebooks"; \
    cd $NOTEBOOK_DIR; \
    $JUPYTER_DIR/bin/python /tmp/parse_nb_manifest.py; \
  fi \
 && rm /tmp/parse_nb_manifest.py

# copy kernel files from other images.
# ./kernels is created by the the build script
# COPY --chown=$NB_UID:$NB_GID kernels /opt/jupyter/share/jupyter/kernels
COPY --chown=$NB_UID:$NB_GID --from=assets /kernels /opt/jupyter/share/jupyter/kernels

# copy other setup scripts
COPY scripts/misc-setup.sh /usr/local/bin/before-notebook.d/

# add a build version
ARG BUILD_VERSION=0
RUN IFS=: read -r name ver <<< "$BUILD_VERSION" && echo "$ver" >> /opt/build-$name

# Add ldap-related config; related to libnss-ldap
USER root
RUN \
   sed -i 's/passwd:         files/passwd:         files ldap/g' /etc/nsswitch.conf \
&& sed -i 's/group:          files/group:          files ldap/g' /etc/nsswitch.conf \
&& cat <<'EOF' > /etc/ldap.conf
base dc=fornax,dc=core              
uri ldap://glauth.fornax.core:30389 
ldap_version 3                      
binddn cn=svcacct,dc=fornax,dc=core
bindpw T3mp3rman3nt 
pam_password clear
EOF

# Add OOM watcher and s3archive helper script into the build in a single layer
COPY scripts/oom_watch.py /usr/local/bin/oom_watch
COPY scripts/s3archive.py /usr/local/bin/s3archive
RUN chmod +x /usr/local/bin/oom_watch /usr/local/bin/s3archive \
 && printf '#!/bin/bash\n/usr/local/bin/oom_watch --delay > /tmp/oom-watch.log 2>&1 & disown' > /usr/local/bin/before-notebook.d/start-oom-watch.sh

## ------------------------------------------------------- ##
## -------- Start from scratch for a minmial image ------- ##
FROM scratch

LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax Primary Jupyter Image"
LABEL org.opencontainers.image.authors="Fornax Project"

# Copy everything *except* the folder you want to remove
COPY --from=build /opt/jupyter /opt/jupyter
COPY --from=build /opt/build-fornax-jupyter /opt/
COPY --from=build /opt/notebooks /opt/notebooks
COPY --from=build /tmp /tmp
COPY --from=build /usr /usr
COPY --from=build /bin /bin
COPY --from=build /etc /etc
COPY --from=build /lib /lib
COPY --from=build /lib64 /lib64
COPY --from=build /home /home
COPY --from=build /root /root
COPY --from=build /run /run
COPY --from=build /sbin /sbin
COPY --from=build /var /var
RUN mkdir -p /tmp/ && chmod 777 /tmp/

## ---- from jupyter-base ---- ##
ARG NB_USER="jovyan"
ARG NB_UID="1000"
ARG NB_GID="100"
ARG PYTHON_VERSION=3.12
ARG JUPYTER_PORT=8888
ARG JUPYTER_DIR=/opt/jupyter
ARG ENV_DIR=/opt/envs

# Set docker shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Define environment variables
ENV JUPYTER_DIR=$JUPYTER_DIR \
    ENV_DIR=$ENV_DIR \
    SHELL=/bin/bash \
    NB_USER=${NB_USER} \
    NB_UID=${NB_UID} \
    NB_GID=${NB_GID} \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    LANGUAGE=C.UTF-8 \
    PYTHON_VERSION=${PYTHON_VERSION} \
    PATH=${JUPYTER_DIR}/bin:${PATH} \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    DEBIAN_FRONTEND=noninteractive \
    HOME=/home/${NB_USER}

# Configure container entrypoint, port, cmd and healthcheck
ENTRYPOINT ["tini", "-g", "--", "start.sh"]
EXPOSE $JUPYTER_PORT
CMD ["start-notebook.py"]
HEALTHCHECK --interval=3s --timeout=1s --start-period=3s --retries=3 \
    CMD /etc/jupyter/docker_healthcheck.py || exit 1

## ---- from fornax-base ---- ##
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
    # Location of the support data
    SUPPORT_DATA_DIR=/opt/support-data \
    # path
    PATH=$MAMBA_ROOT_PREFIX/bin:$PATH


# JUPYTER variables
ARG JUPYTER_CUSTOM_DIR=/scratch/.jupyter
ENV JUPYTER_RUNTIME_DIR=$JUPYTER_CUSTOM_DIR \
    JUPYTER_DATA_DIR=$JUPYTER_CUSTOM_DIR \
    JUPYTER_CONFIG_DIR=$JUPYTER_CUSTOM_DIR \
    IPYTHONDIR=$JUPYTER_CUSTOM_DIR
# Use scratch for jupyter folders #194 
# The folder is empty in the image but is mounted in deployment
USER root
RUN mkdir /scratch && chown $NB_UID:$NB_GID -R /scratch
USER $NB_UID
RUN fix-permissions /scratch

# Support data location; SUPPORT_DATA_DIR -> SUPPORT_DATA_MOUNT
# SUPPORT_DATA_MOUNT is empty here; it is mounted in the deployment
USER root
RUN SUPPORT_DATA_MOUNT=/shared-storage/support-data \
 && mkdir -p $SUPPORT_DATA_MOUNT \
 && ln -s $SUPPORT_DATA_MOUNT $SUPPORT_DATA_DIR \
 && fix-permissions $SUPPORT_DATA_MOUNT
USER $NB_USER

## ----- from other images ----- ##
# From the images
ARG JULIA_VERSION=1.8.0
ENV JULIA_DEPOT_PATH=$ENV_DIR/julia-$JULIA_VERSION \
    JULIA_PKGDIR=$ENV_DIR/julia-$JULIA_VERSION \
    PATH=$ENV_DIR/julia-$JULIA_VERSION/bin:$PATH

ENV DEFAULT_ENV=python3
USER ${NB_UID}
WORKDIR $HOME