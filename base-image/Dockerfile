ARG BASE_TAG=2024-08-12

FROM quay.io/jupyter/base-notebook:${BASE_TAG} as base
FROM quay.io/jupyter/docker-stacks-foundation:${BASE_TAG}


LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax Base Astronomy Image"
LABEL org.opencontainers.image.authors="Fornax Project"


# Bring some commands from jupyter/base-notebook
# Skip the install of jupyterhub/lab etc
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV JUPYTER_PORT=8888
EXPOSE $JUPYTER_PORT
CMD ["start-notebook.py"]
# Copy files from the image directly
COPY --from=base /usr/local/bin/start-* /usr/local/bin/
COPY --from=base /etc/jupyter/*py /etc/jupyter/
USER root
HEALTHCHECK --interval=3s --timeout=1s --start-period=3s --retries=3 \
    CMD /etc/jupyter/docker_healthcheck.py || exit 1
RUN fix-permissions /etc/jupyter/ /home/${NB_USER} /opt/
USER $NB_USER
WORKDIR $HOME
# End of imports from jupyter/base-notebook #
# ----------------------------------------- #

ENV CONDA_ENV=notebook

# Ask dask to read config from ${CONDA_DIR}/etc rather than
# the default of /etc, since the non-root jovyan user can write
# to ${CONDA_DIR}/etc but not to /etc
ENV DASK_ROOT_CONFIG=${CONDA_DIR}/etc

# COPY the current content to $HOME/build
RUN mkdir -p $HOME/build/
COPY --chown=$NB_UID:$NB_GID apt* conda*yml build-* $HOME/build/
COPY --chown=$NB_UID:$NB_GID overrides.json $HOME/build/

USER root

# Make /opt/ user writeable so it can be used by build-* scripts
RUN fix-permissions /opt/

# Install OS packages and then clean up
COPY --chown=$NB_UID:$NB_GID scripts/*.sh /opt/scripts/
# Read apt.txt line by line, and execute apt-get install for each line
RUN cd build && bash /opt/scripts/apt-install.sh

USER $NB_USER
# setup conda environments
RUN cd build && bash /opt/scripts/conda-env-install.sh \
 # Change display name of the default kernel
 && mamba run -n $CONDA_ENV python -m ipykernel install --sys-prefix --display-name "$CONDA_ENV"

# Any other build-* scripts #
RUN cd $HOME/build \
 ; for script in `ls build-*`; do \
 echo "Found script ${script} ..." \
 && chmod +x $script \
 && ./$script \
 ; done
# --------------------------- #

# cache location: use /tmp/ so we don't fill up $HOME
ENV CACHE_DIR=/tmp/cache
RUN mkdir -p $CACHE_DIR
ENV XDG_CACHE_HOME=$CACHE_DIR
ENV XDG_CACHE_DIR=$CACHE_DIR
ENV XDG_CACHE_DIR=$CACHE_DIR

# Set default config for pip and conda
# change default pip cache from ~/.cache/pip
ENV PIP_CACHE_DIR=$CACHE_DIR/pip
RUN mkdir -p $PIP_CACHE_DIR

COPY --chown=$NB_UID:$NB_GID condarc ${CONDA_DIR}/.condarc
# ------------------------------------#

# add a script for to run before the jupyter session
USER root
COPY --chmod=0755 pre-notebook.sh /usr/local/bin/before-notebook.d/20-pre-notebook.sh
USER $NB_USER

# Make $CONDA_ENV default; do it at the global level
# because ~/.bashrc is not loaded when user space is mounted
# Also, add it to before-notebook.d main script
USER root
ENV PATH=$CONDA_DIR/envs/$CONDA_ENV/bin:$PATH
RUN cat $HOME/.bashrc >> /etc/bash.bashrc \
 && printf "\nconda activate \$CONDA_ENV\n" >> /etc/bash.bashrc \
 && printf "\nconda activate \$CONDA_ENV\n" >> /usr/local/bin/before-notebook.d/10activate-conda-env.sh \
 && printf "" > $HOME/.bashrc
USER $NB_USER

# For vscode
ENV CODE_EXECUTABLE=openvscode-server

# For outside mount when using outside fornax
RUN mkdir -p /opt/workspace
VOLUME /opt/workspace

# reset user and location
RUN rm -r $HOME/build $HOME/work /tmp/*
WORKDIR ${HOME}

# Useful environment variables
ENV NOTEBOOK_DIR=${HOME}/notebooks \
    NOUPDATE=${HOME}/.no-notebook-update.txt
 
# Install OS packages and then clean up
ONBUILD RUN mkdir -p $HOME/build
ONBUILD COPY --chown=$NB_UID:$NB_GID apt* conda*yml build-* $HOME/build/
ONBUILD USER root
ONBUILD RUN mkdir -p build && cd build && bash /opt/scripts/apt-install.sh
ONBUILD USER $NB_USER
# ------------------------------------ #


# setup conda environments
ONBUILD RUN cd build && bash /opt/scripts/conda-env-install.sh
# and ensure the correct display name
ONBUILD RUN mamba run -n $CONDA_ENV python -m ipykernel install --sys-prefix --display-name "$CONDA_ENV"
# ----------------------- #

# Any other build-* scripts #
ONBUILD RUN cd build \
 ; for script in `ls build-*`; do \
 echo "Found script ${script} ..." \
 && chmod +x $script \
 && ./$script \
 ; done
# --------------------------- #

# landing page
ONBUILD COPY --chown=$NB_UID:$NB_GID --chmod=644 introduction.md* /opt/scripts/

ONBUILD RUN rm -r $HOME/build
ONBUILD USER ${NB_USER}
ONBUILD WORKDIR ${HOME}
