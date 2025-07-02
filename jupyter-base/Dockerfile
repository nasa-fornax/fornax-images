# Jupyter foundation.
# This is a merged version of jupyter's docker-stacks-foundation and base-notebook
# It is a separate image to give us flexibility to use non-conda environment management.

ARG ROOT_IMAGE=ubuntu:24.04
FROM $ROOT_IMAGE

LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax jupyter foundation image"
LABEL org.opencontainers.image.authors="Fornax Project"

ARG NB_USER="jovyan"
ARG NB_UID="1000"
ARG NB_GID="100"
ARG PIXI_HOME="/opt/pixi"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install OS dependencies.
USER root
COPY apt.txt /tmp/
RUN apt-get update --yes \
 # `apt-get upgrade` is run to patch known vulnerabilities in system packages
 && apt-get upgrade --yes \
 && xargs -a /tmp/apt.txt apt-get install -y --no-install-recommends \
 && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/apt.txt \
 && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
 && echo "C.UTF-8 UTF-8" >> /etc/locale.gen \
 && locale-gen

# Configure environment
ENV PIXI_HOME=${PIXI_HOME} \
    SHELL=/bin/bash \
    NB_USER=${NB_USER} \
    NB_UID=${NB_UID} \
    NB_GID=${NB_GID} \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    LANGUAGE=C.UTF-8

ENV PATH="${PIXI_HOME}/bin:${PATH}" \
    HOME="/home/${NB_USER}"

# Copy scripts from the jupyter stack script
ARG JUPYTER_STACK_URL=https://raw.githubusercontent.com/jupyter/docker-stacks/refs/heads/main/images
RUN cd /usr/local/bin/ \
 && curl -fsSLO $JUPYTER_STACK_URL/docker-stacks-foundation/fix-permissions \
 && curl -fsSLO $JUPYTER_STACK_URL/docker-stacks-foundation/run-hooks.sh \
 && curl -fsSLO $JUPYTER_STACK_URL/docker-stacks-foundation/start.sh \
 && curl -fsSLO $JUPYTER_STACK_URL/docker-stacks-foundation/10activate-conda-env.sh \
 && chmod a+rx fix-permissions start.sh \
 && mkdir -p start-notebook.d before-notebook.d \
 && mv 10activate-conda-env.sh start-notebook.d

# Configure container entrypoint
ENTRYPOINT ["tini", "-g", "--", "start.sh"]

# Enable prompt color
RUN sed -i 's/^#force_color_prompt=yes/force_color_prompt=yes/' /etc/skel/.bashrc

# Delete existing user with UID="${NB_UID}" if it exists
RUN if grep -q "${NB_UID}" /etc/passwd; then \
        userdel --remove $(id -un "${NB_UID}"); \
    fi

# Create "${NB_USER}"
RUN echo "auth requisite pam_deny.so" >> /etc/pam.d/su \
 && sed -i.bak -e 's/^%admin/#%admin/' /etc/sudoers \
 && sed -i.bak -e 's/^%sudo/#%sudo/' /etc/sudoers \
 && useradd --no-log-init --create-home --shell /bin/bash --uid "${NB_UID}" --no-user-group "${NB_USER}" \
 && chmod g+w /etc/passwd \
 && mkdir -p $PIXI_HOME \
 && fix-permissions "${PIXI_HOME}" \
 && fix-permissions "/home/${NB_USER}"

USER ${NB_UID}
ARG PYTHON_VERSION=3.12

# Install pixi
ENV PATH="${PIXI_HOME}/bin:${PATH}" \
    JUPYTER_ENV=jupyter
RUN curl -fsSL https://pixi.sh/install.sh | bash \
 && pixi global install --environment $JUPYTER_ENV --expose jupyter --expose python --expose uv --expose jupyterhub-singleuser \
    "python=${PYTHON_VERSION}" uv \
    "jupyterlab==4.3.6" \
    "jupyterhub==5.2.1" \
    "notebook==7.3.3" \
 && pixi clean cache -y

## ----- end of docker-stacks-foundation ----- ##
## ------------------------------------------- ##

## --- content from base-notebook -- ##

ARG JUPYTER_PORT=8888
EXPOSE $JUPYTER_PORT

# Configure container startup
CMD ["start-notebook.py"]

# Bring in files from jupyter/base-notebook
USER root
RUN cd /usr/local/bin/ \
 && curl -fsSLO $JUPYTER_STACK_URL/base-notebook/start-notebook.py \
 && curl -fsSLO $JUPYTER_STACK_URL/base-notebook/start-singleuser.py \
 && curl -fsSLO $JUPYTER_STACK_URL/base-notebook/docker_healthcheck.py \
 && curl -fsSLO $JUPYTER_STACK_URL/base-notebook/jupyter_server_config.py \
 # ensure the start scripts use the correct jupyter
 && sed -i "s|\"jupyter|\"$PIXI_HOME/bin/jupyter|g" start-notebook.py \
 && sed -i "s|\"jupyter|\"$PIXI_HOME/bin/jupyter|g" start-singleuser.py \
 && chmod +x start-notebook.py start-singleuser.py \
 && mkdir -p /etc/jupyter/ \
 && mv docker_healthcheck.py jupyter_server_config.py /etc/jupyter/

HEALTHCHECK --interval=3s --timeout=1s --start-period=3s --retries=3 \
    CMD /etc/jupyter/docker_healthcheck.py || exit 1
RUN fix-permissions /etc/jupyter/ /home/${NB_USER} /opt/

# set DASK_ROOT_CONFIG a directory writable by the user
ENV DASK_ROOT_CONFIG=${CONDA_DIR}/etc

## ----- end of base-notebook ----- ##
## -------------------------------- ##

## -- install jupyter -- ##
USER $NB_USER
RUN jupyter server --generate-config \
 && pixi clean cache -y \
 && jupyter lab clean \
 && rm -rf "/home/${NB_USER}/.cache/yarn" \
 && fix-permissions "${PIXI_HOME}" \
 && fix-permissions "/home/${NB_USER}"

 USER $NB_USER
WORKDIR $HOME
