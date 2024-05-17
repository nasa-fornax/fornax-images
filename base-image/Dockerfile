FROM quay.io/jupyter/base-notebook:2024-05-16

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


USER root

# Install OS packages and then clean up
COPY --chown=$NB_USER:$NB_USER scripts /opt/scripts
COPY --chown=$NB_USER:$NB_USER apt.txt* $HOME/build/
# Read apt.txt line by line, and execute apt-get install for each line
RUN cd build && bash /opt/scripts/apt-install.sh


# update start.sh (user as ENTRYPOINT) to a simple one
RUN printf "#!/bin/bash -l\n\nexec \"\$@\"" > /usr/local/bin/start.sh \
 && chmod +x /usr/local/bin/start.sh
CMD ["/bin/bash"]


USER $NB_USER
# setup conda environments
COPY --chown=$NB_USER:$NB_USER conda-*yml $HOME/build/
RUN mamba install conda-lock \
 && cd build && bash /opt/scripts/conda-env-install.sh

# reset user and location
USER ${NB_USER}
WORKDIR ${HOME}

# Make $CONDA_ENV default
RUN printf "\nif ! [ -z \$CONDA_ENV ]; then\n  conda activate \$CONDA_ENV\nfi\n" >> $HOME/.bashrc
ENV PATH=$CONDA_DIR/envs/$CONDA_ENV/bin:$PATH


# Install OS packages and then clean up
ONBUILD USER root
ONBUILD COPY --chown=$NB_USER:$NB_USER apt.txt* $HOME/build/
ONBUILD RUN cd build && bash /opt/scripts/apt-install.sh
ONBUILD USER $NB_USER
# ------------------------------------ #


# setup conda environments
ONBUILD COPY --chown=$NB_USER:$NB_USER conda-*yml $HOME/build/
ONBUILD RUN cd build && bash /opt/scripts/conda-env-install.sh
# ----------------------- #
