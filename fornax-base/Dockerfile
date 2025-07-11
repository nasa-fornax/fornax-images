ARG BASE_TAG=latest
ARG REPOSITORY=nasa-fornax/fornax-images
ARG REGISTRY=ghcr.io

FROM ${REGISTRY}/${REPOSITORY}/jupyter-base:${BASE_TAG}

LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax Base Image"
LABEL org.opencontainers.image.authors="Fornax Project"



ENV DEFAULT_ENV=python3 \
    LOCK_DIR=$ENV_DIR/lock


# cache location: use /tmp/ so we don't fill up $HOME
ENV CACHE_DIR=/tmp/cache
RUN mkdir -p $CACHE_DIR
ENV XDG_CACHE_HOME=$CACHE_DIR \
    XDG_CACHE_DIR=$CACHE_DIR \
    XDG_CACHE_DIR=$CACHE_DIR \
    PIP_CACHE_DIR=$CACHE_DIR/pip \
    UV_CACHE_DIR=$CACHE_DIR/uv
RUN mkdir -p $PIP_CACHE_DIR $UV_CACHE_DIR


USER root

# jupyter setting overrides
RUN mkdir -p $JUPYTER_DIR/share/jupyter/lab/settings/ \
 # Disable the announcement extension
 && jupyter labextension disable "@jupyterlab/apputils-extension:announcements"
COPY --chown=$NB_UID:$NB_GID overrides.json $JUPYTER_DIR/share/jupyter/lab/settings/


# Make /opt/ user writeable so it can be used by build-* scripts
RUN fix-permissions /opt/

# Install OS packages and then clean up
COPY --chown=$NB_UID:$NB_GID scripts/*.sh /usr/local/bin/
# Read apt.txt line by line, and execute apt-get install for each line
COPY --chown=$NB_UID:$NB_GID apt.txt .
RUN bash /usr/local/bin/apt-install.sh && rm apt.txt

USER $NB_USER

# add packages to jupyter environment
COPY --chown=$NB_UID:$NB_GID jupyter-requirements.txt /tmp/
RUN uv pip install --no-cache-dir -r /tmp/jupyter-requirements.txt

# install fornax-labextension in jupyter environment
RUN cd /tmp/ \
 && whlurl=`curl -s "https://api.github.com/repos/nasa-fornax/fornax-labextension/releases/latest" \
    | jq -r '.assets[] | select(.name | endswith(".whl")) | .browser_download_url'` \
 && whlfile=`basename $whlurl` \
 && curl -sSLO $whlurl \
 && uv pip install --no-cache-dir ./$whlfile \
 && rm $whlfile

# update env file
RUN uv pip list --format=freeze > $JUPYTER_DIR/requirements-jupyter.txt \
 && mkdir -p $LOCK_DIR \
 && cp $JUPYTER_DIR/requirements-jupyter.txt $LOCK_DIR/requirements-jupyter.txt

# install code-server binary
ENV CODE_EXECUTABLE=code-server
USER root
RUN curl -fsSL https://code-server.dev/install.sh | sh
USER $NB_USER

## ------------------------------------#

# install DEFAULT_ENV
COPY --chown=$NB_UID:$NB_GID requirements-$DEFAULT_ENV.txt /tmp/
RUN cd /tmp/ && bash /usr/local/bin/uv-env-install.sh \
 # fix the display name of DEFAULT_ENV
 && $ENV_DIR/$DEFAULT_ENV/bin/python -m ipykernel install --name $DEFAULT_ENV \
    --prefix $JUPYTER_DIR --display-name "$DEFAULT_ENV"

# add a script to run before the jupyter session
USER root
COPY --chmod=0777 update-notebooks.sh /usr/local/bin/update-notebooks.sh
USER $NB_USER

# Make $DEFAULT_ENV default; do it at the global level
# because ~/.bashrc is not loaded when user space is mounted
# Also, add it to before-notebook.d main script
USER root
RUN echo "if [ -f \$ENV_DIR/\$DEFAULT_ENV/bin/activate ]; then" > /tmp/activate.sh \
 && echo "  source \$ENV_DIR/\$DEFAULT_ENV/bin/activate" >> /tmp/activate.sh \
 && echo "elif [ -d \$ENV_DIR/\$DEFAULT_ENV/conda-meta ]; then" >> /tmp/activate.sh \
 && echo "  micromamba activate \$DEFAULT_ENV" >> /tmp/activate.sh \
 && echo "else" >> /tmp/activate.sh \
 && echo "  echo DEFAULT_ENV=\$DEFAULT_ENV not found" >> /tmp/activate.sh \
 && echo "fi" >> /tmp/activate.sh \
 && echo "" >> /tmp/activate.sh \
 && cat /tmp/activate.sh >> /etc/bash.bashrc \
 && cat /tmp/activate.sh  >> /usr/local/bin/before-notebook.d/10activate-conda-env.sh \
 && rm -r /tmp/*

# reset user and location
WORKDIR ${HOME}
USER $NB_USER


# For outside mount when using outside fornax
RUN mkdir -p /opt/workspace
VOLUME /opt/workspace


# Useful environment variables
ENV NOTEBOOK_DIR=/opt/notebooks
# Run the pre-notebooks script to get a copy in the image
RUN bash /usr/local/bin/update-notebooks.sh

# SUPPORT_DATA_MOUNT can be passed from JH. The location of the mount point for support data
# SUPPORT_DATA_DIR: is what scripts should use. It is fixed here.
ARG SUPPORT_DATA_MOUNT=/shared-storage/support-data
ENV SUPPORT_DATA_DIR=/opt/support-data
RUN ln -s $SUPPORT_DATA_MOUNT $SUPPORT_DATA_DIR

# ==== Start ONBUILD commands ==== #
# These run in images the inherit fornax-images
# ================================ #

# Install OS packages and then clean up
ONBUILD RUN mkdir -p $HOME/build
ONBUILD COPY --chown=$NB_UID:$NB_GID apt* build-* requirements-* conda-* $HOME/build/
ONBUILD USER root
ONBUILD RUN mkdir -p build && cd build && bash /usr/local/bin/apt-install.sh
ONBUILD USER $NB_USER
# ------------------------------------ #


# setup uv environments
ONBUILD RUN cd build && bash /usr/local/bin/uv-env-install.sh \
 && bash /usr/local/bin/conda-env-install.sh
# ----------------------- #

# Any other build-* scripts; e.g. build tractor, heasoft etc #
ONBUILD RUN cd build \
 ; for script in `ls build-*`; do \
 echo "Found script ${script} ..." \
 && chmod +x $script \
 && ./$script \
 ; done
# --------------------------- #

# landing page; even an empty one
ONBUILD COPY --chown=$NB_UID:$NB_GID --chmod=644 introduction.md* $JUPYTER_DIR
ONBUILD RUN cd $JUPYTER_DIR \
 && if test -f introduction.md; then \
  pandoc introduction.md -o introduction.html --standalone --metadata title="Welcome to Fornax Science Console!"; \
 fi

ONBUILD RUN rm -r $HOME/build
ONBUILD USER ${NB_USER}
ONBUILD WORKDIR ${HOME}
