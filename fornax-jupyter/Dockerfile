ARG BASE_TAG=latest
ARG REPOSITORY=ghcr.io/nasa-fornax/fornax-images

FROM ${REPOSITORY}/fornax-nb:${BASE_TAG} AS fornax_nb
FROM ${REPOSITORY}/archive-nb:${BASE_TAG} AS archive_nb
FROM ${REPOSITORY}/fornax-base:${BASE_TAG}

LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax Primary Jupyter Image"
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
RUN cat /tmp/jupyter_server_config.py >> /etc/jupyter/jupyter_server_config.py \
 && rm /tmp/jupyter_server_config.py
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
 && (timeout 20s start-notebook.py || true) \
 && fix-permissions $JUPYTER_DIR /tmp/cache \
 && rm /tmp/jupyter-deps.txt

# From the images
ARG JULIA_VERSION=1.8.0
ENV JULIA_DEPOT_PATH=$ENV_DIR/julia-$JULIA_VERSION \
    JULIA_PKGDIR=$ENV_DIR/julia-$JULIA_VERSION \
    PATH=$ENV_DIR/julia-$JULIA_VERSION/bin:$PATH

# Add the notebooks
COPY --from=fornax_nb $NOTEBOOK_DIR $NOTEBOOK_DIR
COPY --from=archive_nb $NOTEBOOK_DIR $NOTEBOOK_DIR

# landing page; even an empty one
COPY --chown=$NB_UID:$NB_GID --chmod=644 introduction.md $NOTEBOOK_DIR/introduction.mdv
COPY --chown=$NB_UID:$NB_GID --chmod=644 changes.md $NOTEBOOK_DIR/changes.mdv

# # Update the intro page with notebooks by parsing the manifests
COPY --chown=$NB_UID:$NB_GID parse_nb_manifest.py /tmp/
RUN \
  if [ -f /tmp/parse_nb_manifest.py ]; then \
    echo "Parsing manifests of archive notebooks"; \
    cd $NOTEBOOK_DIR; \
    $JUPYTER_DIR/bin/python /tmp/parse_nb_manifest.py; \
  fi \
 && rm /tmp/parse_nb_manifest.py

# copy kernel files from other images.
# ./kernels is created by the the build script
COPY --chown=$NB_UID:$NB_GID kernels /opt/jupyter/share/jupyter/kernels

# copy other setup scripts
COPY misc-setup.sh /usr/local/bin/before-notebook.d/

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

# Add OOM watcher script
COPY oom_watch.py /usr/local/bin/oom_watch
RUN chmod +x /usr/local/bin/oom_watch \
 && printf '#!/bin/bash\nnohup /usr/local/bin/oom_watch > /tmp/oom_watch.log 2>&1 &' > /usr/local/bin/before-notebook.d/start-oom-watchdog.sh

ENV DEFAULT_ENV=python3
USER ${NB_UID}
WORKDIR $HOME