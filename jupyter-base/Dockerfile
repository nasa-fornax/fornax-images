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
ENV JUPYTER_DIR=/opt/jupyter \
    SHELL=/bin/bash \
    NB_USER="${NB_USER}" \
    NB_UID=${NB_UID} \
    NB_GID=${NB_GID} \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    LANGUAGE=C.UTF-8

ENV PATH="${JUPYTER_DIR}/bin:${PATH}" \
    HOME="/home/${NB_USER}"

# Copy scripts from the jupyter stack script
ARG JUPYTER_STACK_URL=https://raw.githubusercontent.com/jupyter/docker-stacks/refs/heads/main/images
RUN cd /usr/local/bin/ \
 && curl -fsSLO $JUPYTER_STACK_URL/docker-stacks-foundation/fix-permissions \
 && curl -fsSLO $JUPYTER_STACK_URL/docker-stacks-foundation/run-hooks.sh \
 && curl -fsSLO $JUPYTER_STACK_URL/docker-stacks-foundation/start.sh \
 && chmod a+rx fix-permissions start.sh \
 && mkdir -p start-notebook.d before-notebook.d

# Configure container entrypoint
ENTRYPOINT ["tini", "-g", "--", "start.sh"]

# Enable prompt color
RUN sed -i 's/^#force_color_prompt=yes/force_color_prompt=yes/' /etc/skel/.bashrc \
 && echo 'eval "$(micromamba shell hook --shell bash)"' >> /etc/skel/.bashrc \
 && echo 'eval "$(micromamba shell hook --shell bash)"' > /usr/local/bin/before-notebook.d/10activate-conda-env.sh 

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
 && fix-permissions /opt/

# Install uv & micromamba
ENV MAMBA_ROOT_PREFIX=/opt/
RUN cd /tmp/ \
 && curl -LsSf https://astral.sh/uv/install.sh | sh \
 && mv $HOME/.local/bin/uv* /usr/local/bin/ \
 && rm -rf $HOME/.local/bin \
 && sed -i '/\.local\/bin/d' $HOME/.bashrc \
 # micromamba
 && curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj bin/micromamba \
 && mv bin/micromamba /usr/local/bin/ \
 && rm -rf bin



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
 && chmod +x start-notebook.py start-singleuser.py \
 # make sure we start the correct jupyter
 && sed -i "s|\"jupyter|\"$JUPYTER_DIR/bin/jupyter|g" start-notebook.py \
 && sed -i "s|\"jupyter|\"$JUPYTER_DIR/bin/jupyter|g" start-singleuser.py \
 && mkdir -p /etc/jupyter/ \
 && mv docker_healthcheck.py jupyter_server_config.py /etc/jupyter/

HEALTHCHECK --interval=3s --timeout=1s --start-period=3s --retries=3 \
    CMD /etc/jupyter/docker_healthcheck.py || exit 1

USER ${NB_UID}

## ----- end of base-notebook ----- ##
## -------------------------------- ##

## -- install jupyter -- ##
ENV PYTHON_VERSION=3.12 \
    ENV_DIR=/opt/envs
ENV UV_PYTHON_INSTALL_DIR=${ENV_DIR}/.uv
RUN uv python install $PYTHON_VERSION \
 && uv venv $JUPYTER_DIR \
 && export VIRTUAL_ENV=$JUPYTER_DIR \
 && uv pip install "jupyterlab==4.*" "jupyterhub==5.*" \
 && uv clean \
 && jupyter lab clean \
 && uv pip list --format=freeze > $JUPYTER_DIR/requirements-jupyter.txt \
 && find $JUPYTER_DIR -follow -type f \( -name '*.a' -o -name '*.pyc' -o -name '*.js.map' \) -delete

USER root
RUN fix-permissions /etc/jupyter/ /home/${NB_USER} /opt/ \
 && cat $HOME/.bashrc >> /etc/bash.bashrc \
 && rm -r $HOME/.*

USER $NB_USER
WORKDIR $HOME
