
ARG BASE_TAG=latest
ARG REPOSITORY=nasa-fornax/fornax-images
ARG REGISTRY=ghcr.io

FROM ${REGISTRY}/${REPOSITORY}/fornax-base:${BASE_TAG} AS base
FROM scratch


# Copy everything *except* the folder you want to remove
COPY --from=base /opt/jupyter /opt/jupyter
COPY --from=base /opt/notebooks /opt/notebooks
COPY --from=base /usr /usr
COPY --from=base /bin /bin
COPY --from=base /etc /etc
COPY --from=base /lib /lib
COPY --from=base /lib64 /lib64
COPY --from=base /home /home
COPY --from=base /root /root
COPY --from=base /run /run
COPY --from=base /sbin /sbin
COPY --from=base /var /var
RUN mkdir -p /tmp/ && chmod 777 /tmp/

## ---- from jupyter-base ---- ##

# Define global variables
ARG NB_USER="jovyan"
ARG NB_UID="1000"
ARG NB_GID="100"
ARG PYTHON_VERSION=3.12
ARG JUPYTER_PORT=8888
ARG JUPYTER_DIR=/opt/jupyter
ARG ENV_DIR=/opt/envs

# Set docker shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

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
    HOME=/home/${NB_USER}

# Configure container entrypoint, port, cmd and healthcheck
ENTRYPOINT ["tini", "-g", "--", "start.sh"]
EXPOSE $JUPYTER_PORT
CMD ["start-notebook.py"]
HEALTHCHECK --interval=3s --timeout=1s --start-period=3s --retries=3 \
    CMD /etc/jupyter/docker_healthcheck.py || exit 1


## ---- from fornax-base ---- ##
ARG SUPPORT_DATA_MOUNT=/shared-storage/support-data
ARG MAMBA_ROOT_PREFIX=$ENV_DIR/base

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
    # support data; JH can pass ARG SUPPORT_DATA_MOUNT; SUPPORT_DATA_DIR points to it
    # scripts that rely on support data should use SUPPORT_DATA_DIR
    SUPPORT_DATA_DIR=/opt/support-data \
    # path
    PATH=$MAMBA_ROOT_PREFIX/bin:$PATH

# For outside mount when using outside fornax
RUN mkdir -p /opt/workspace
VOLUME /opt/workspace

# Support data location; SUPPORT_DATA_DIR -> SUPPORT_DATA_MOUNT
# SUPPORT_DATA_MOUNT can be set by JH
RUN ln -s $SUPPORT_DATA_MOUNT $SUPPORT_DATA_DIR

# copy kernel files from other images.
# ./kernels is created by the the build script
COPY --chown=$NB_UID:$NB_GID kernels /opt/jupyter/share/jupyter/kernels


## ----- From other images ----- ##
ARG JULIA_VERSION=1.8.0
ENV JULIA_DEPOT_PATH=$ENV_DIR/julia-$JULIA_VERSION \
    JULIA_PKGDIR=$ENV_DIR/julia-$JULIA_VERSION \
    PATH=$ENV_DIR/julia-$JULIA_VERSION/bin:$PATH

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

USER ${NB_UID}
WORKDIR $HOME