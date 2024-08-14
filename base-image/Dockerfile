FROM quay.io/jupyter/base-notebook:2024-08-12

LABEL org.opencontainers.image.source=https://github.com/fornax-navo/fornax-images
LABEL org.opencontainers.image.ref.name="Fornax Base Image"
LABEL org.opencontainers.image.version=0.1
LABEL maintainer="Fornax Project"

# clear the jupyter stack from base
RUN mamba remove jupyterlab notebook jupyterhub nbclassic ipykernel \
 && mamba clean -afy \
 && find ${CONDA_DIR} -follow -type f -name '*.a' -delete

ENV CONDA_ENV=notebook


# Ask dask to read config from ${CONDA_DIR}/etc rather than
# the default of /etc, since the non-root jovyan user can write
# to ${CONDA_DIR}/etc but not to /etc
ENV DASK_ROOT_CONFIG=${CONDA_DIR}/etc

# COPY the current content to $HOME/build
RUN mkdir -p $HOME/build/
COPY --chown=$NB_USER:$NB_USER apt* conda*yml postBuild* $HOME/build/
COPY --chown=$NB_USER:$NB_USER overrides.json $HOME/build/

USER root

# Install OS packages and then clean up
COPY --chown=$NB_USER:$NB_USER scripts /opt/scripts
# Read apt.txt line by line, and execute apt-get install for each line
RUN cd build && bash /opt/scripts/apt-install.sh



USER $NB_USER
# setup conda environments
RUN mamba install conda-lock \
 && cd build && bash /opt/scripts/conda-env-install.sh

# Change dispaly name of the default kernel
RUN mamba run -n $CONDA_ENV python -m ipykernel install --sys-prefix --display-name "$CONDA_ENV"

# Any other postBuild scripts #
RUN cd $HOME/build \
 ; for script in `ls postBuild*`; do \
 echo "Found script ${script} ..." \
 && chmod +x $script \
 && ./$script \
 ; done
# --------------------------- #

# reset user and location
RUN rm -r $HOME/build $HOME/work /tmp/*
USER ${NB_USER}
WORKDIR ${HOME}

# Make $CONDA_ENV default
RUN printf "\nif ! [ -z \$CONDA_ENV ]; then\n  conda activate \$CONDA_ENV\nfi\n" >> $HOME/.bashrc
ENV PATH=$CONDA_DIR/envs/$CONDA_ENV/bin:$PATH


# Install OS packages and then clean up
ONBUILD RUN mkdir -p $HOME/build
ONBUILD COPY --chown=$NB_USER:$NB_USER apt* conda*yml postBuild* $HOME/build/
ONBUILD USER root
ONBUILD RUN mkdir -p build && cd build && bash /opt/scripts/apt-install.sh
ONBUILD USER $NB_USER
# ------------------------------------ #


# setup conda environments
ONBUILD RUN cd build && bash /opt/scripts/conda-env-install.sh
# ----------------------- #

# Any other postBuild scripts #
ONBUILD RUN cd build \
 ; for script in `ls postBuild*`; do \
 echo "Found script ${script} ..." \
 && chmod +x $script \
 && ./$script \
 ; done
# --------------------------- #

ONBUILD RUN rm -r $HOME/build
ONBUILD USER ${NB_USER}
ONBUILD WORKDIR ${HOME}
