ARG BASE_TAG=latest
ARG REPOSITORY=nasa-fornax/fornax-images
ARG REGISTRY=ghcr.io

FROM ${REGISTRY}/${REPOSITORY}/jupyter-base:${BASE_TAG}

LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax Base Image"
LABEL org.opencontainers.image.authors="Fornax Project"



ENV DEFAULT_ENV=python3 \
    ENV_DIR=/opt/envs \
    LOCK_DIR=/opt/lock


# cache location: use /tmp/ so we don't fill up $HOME
ENV CACHE_DIR=/tmp/cache
RUN mkdir -p $CACHE_DIR
ENV XDG_CACHE_HOME=$CACHE_DIR \
    XDG_CACHE_DIR=$CACHE_DIR \
    XDG_CACHE_DIR=$CACHE_DIR \
    PIP_CACHE_DIR=$CACHE_DIR/pip \
    UV_CACHE_DIR=$CACHE_DIR/uv
RUN mkdir -p $PIP_CACHE_DIR $UV_CACHE_DIR

# COPY the current content to $HOME/build
RUN mkdir -p $HOME/build/
COPY --chown=$NB_UID:$NB_GID apt.txt $HOME/build/

USER root

# jupyter overrides
COPY --chown=$NB_UID:$NB_GID overrides.json $HOME/build/
RUN mkdir -p $CONDA_DIR/share/jupyter/lab/settings/ \
 && mv ~/build/overrides.json $CONDA_DIR/share/jupyter/lab/settings/ \
 # Disable the announcement extension
 && jupyter labextension disable "@jupyterlab/apputils-extension:announcements"


# Make /opt/ user writeable so it can be used by build-* scripts
RUN fix-permissions /opt/

# Install OS packages and then clean up
COPY --chown=$NB_UID:$NB_GID scripts/*.sh /opt/scripts/
# Read apt.txt line by line, and execute apt-get install for each line
RUN cd build && bash /opt/scripts/apt-install.sh

USER $NB_USER

# add packages to base and notebook
COPY --chown=$NB_UID:$NB_GID base-requirements.txt requirements-$DEFAULT_ENV.txt $HOME/build/
RUN mkdir -p $ENV_DIR \
 && cd build \
 && pip install --no-cache-dir uv \
 && pip install --no-cache-dir -r $HOME/build/base-requirements.txt \
 # && bash /opt/scripts/conda-env-install.sh
 # install requirements for DEFAULT_ENV
 && bash /opt/scripts/uv-env-install.sh \
 # fix the display name of DEFAULT_ENV
 && VIRTUAL_ENV=$ENV_DIR/$DEFAULT_ENV uv run python -m ipykernel install --name $DEFAULT_ENV \
    --prefix $CONDA_DIR --display-name "$DEFAULT_ENV"

# install code-server
ENV CODE_EXECUTABLE=code-server
RUN mamba install code-server \
 # update the lockfile
 && mamba env export > $CONDA_DIR/base-lock.yml \
 && mkdir -p $LOCK_DIR \
 && cp $CONDA_DIR/base-lock.yml $LOCK_DIR \
 && mamba clean -yaf

## ------------------------------------#

# add a script to run before the jupyter session
USER root
RUN mv /opt/conda/bin/uv /opt/conda/bin/uvx /usr/local/bin/
COPY --chmod=0755 pre-notebook.sh /usr/local/bin/before-notebook.d/20-pre-notebook.sh
USER $NB_USER

# Make $CONDA_ENV default; do it at the global level
# because ~/.bashrc is not loaded when user space is mounted
# Also, add it to before-notebook.d main script
USER root
ENV PATH=$CONDA_DIR/envs/$CONDA_ENV/bin:$PATH
RUN cat $HOME/.bashrc >> /etc/bash.bashrc \
 # remove conda hook
 && sed -i '/conda shell.bash hook/d' /etc/bash.bashrc \
 # activate DEFAULT_ENV
 && printf "\nsource $ENV_DIR/$DEFAULT_ENV/bin/activate\n" >> /etc/bash.bashrc \
 && printf "\nsource $ENV_DIR/$DEFAULT_ENV/bin/activate\n" >> /usr/local/bin/before-notebook.d/10-set-default-env.sh \
 && printf "" > $HOME/.bashrc
USER $NB_USER


# For outside mount when using outside fornax
RUN mkdir -p /opt/workspace
VOLUME /opt/workspace

# reset user and location
RUN rm -r $HOME/build /tmp/*
WORKDIR ${HOME}

# Useful environment variables
ENV NOTEBOOK_DIR=/opt/notebooks \
    NOUPDATE=${HOME}/.no-notebook-update.txt \
    ADD_NOTEBOOKS=1
# Run the pre-notebooks script to get a copy in the image
RUN ADD_NOTEBOOKS=1 source /usr/local/bin/before-notebook.d/20-pre-notebook.sh

# ==== Start ONBUILD commands ==== #
# These run in images the inherit fornax-images
# ================================ #

# Install OS packages and then clean up
ONBUILD RUN mkdir -p $HOME/build
ONBUILD COPY --chown=$NB_UID:$NB_GID apt* conda*yml build-* $HOME/build/
ONBUILD USER root
ONBUILD RUN mkdir -p build && cd build && bash /opt/scripts/apt-install.sh
ONBUILD USER $NB_USER
# ------------------------------------ #


# setup conda and uv environments
ONBUILD RUN cd build && bash /opt/scripts/conda-env-install.sh && bash /opt/scripts/uv-env-install.sh
# and ensure the correct display name
# ONBUILD RUN mamba run -n $CONDA_ENV python -m ipykernel install --sys-prefix --display-name "$CONDA_ENV"
# ----------------------- #

# Any other build-* scripts; e.g. build tractor #
ONBUILD RUN cd build \
 ; for script in `ls build-*`; do \
 echo "Found script ${script} ..." \
 && chmod +x $script \
 && ./$script \
 ; done
# --------------------------- #

# landing page; even an empty one
ONBUILD COPY --chown=$NB_UID:$NB_GID --chmod=644 introduction.md* /opt/scripts/
ONBUILD RUN cd /opt/scripts/ \
 && if test -f introduction.md; then \
  pandoc introduction.md -o introduction.html --standalone --metadata title="Welcome to Fornax Science Console!"; \
 fi

ONBUILD RUN rm -r $HOME/build
ONBUILD USER ${NB_USER}
ONBUILD WORKDIR ${HOME}
