# Jupyter foundation.
# This is a merged version of jupyter's docker-stacks-foundation and base-notebook
# It is a separate image to give us flexibility to use non-conda environment management.

# Starting image
ARG ROOT_IMAGE=ubuntu:24.04
FROM $ROOT_IMAGE

# Add some labels
LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax jupyter foundation image"
LABEL org.opencontainers.image.authors="Fornax Project"

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

# Install OS dependencies. Keep this to a minimum.
# We add system python to be used later by uv.
USER root
COPY apt.txt /tmp/
RUN apt-get update --yes && apt-get upgrade --yes \
 # install requested packages
 && xargs -a /tmp/apt.txt apt-get install -y --no-install-recommends \
 # add python
 && apt-get install -y --no-install-recommends python$PYTHON_VERSION\
 # clean to remove any cache files
 && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/apt.txt \
 && rm /etc/localtime && ln -sf /usr/share/zoneinfo/America/New_York /etc/localtime \
 && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
 && echo "C.UTF-8 UTF-8" >> /etc/locale.gen \
 && locale-gen

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
    HOME=/home/${NB_USER}

# Copy scripts from the jupyter stack repo
COPY --chmod=0555 scripts/start* scripts/fix-permissions scripts/run-hooks.sh /usr/local/bin/
COPY --chown=$NB_UID:$NB_GID scripts/docker_healthcheck.py scripts/jupyter_server_config.py /etc/jupyter/
RUN cd /usr/local/bin/ \
 && fix-permissions /etc/jupyter/ /opt/ \
 && mkdir -p start-notebook.d before-notebook.d

# Configure container entrypoint, port, cmd and healthcheck
ENTRYPOINT ["tini", "-g", "--", "start.sh"]
EXPOSE $JUPYTER_PORT
CMD ["start-notebook.py"]
HEALTHCHECK --interval=3s --timeout=1s --start-period=3s --retries=3 \
    CMD /etc/jupyter/docker_healthcheck.py || exit 1

# Enable prompt color and micromamba shell hook
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
 && useradd --no-log-init --create-home --shell /bin/bash --uid "${NB_UID}" --gid "${NB_GID}" --no-user-group $NB_USER \
 && chmod g+w /etc/passwd \
 && cat $HOME/.bashrc >> /etc/bash.bashrc \
 # remove /home/ubuntu
 && if test -d /home/ubuntu; then rm -f /home/ubuntu;fi

# Install uv & micromamba
RUN cd /tmp/ \
 && curl -LsSf https://astral.sh/uv/install.sh | sh \
 && mv $HOME/.local/bin/uv* /usr/local/bin/ \
 && rm -rf $HOME/.local/bin \
 && sed -i '/\.local\/bin/d' $HOME/.bashrc \
 # micromamba
 && curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj bin/micromamba \
 && mv bin/micromamba /usr/local/bin/ \
 # add alias for conda and mamba to point the user to micromamba
 && cd /usr/local/bin/\
 && echo -e '#!/usr/bin/bash\necho "** Please use micromamba instead of conda/mamba **"' | tee conda mamba \
 && chmod +x mamba conda \
 && rm -rf bin \
 && cd $HOME && rm -rf .* *


## -- install jupyter -- ##
USER ${NB_UID}
RUN uv venv $JUPYTER_DIR --no-managed-python -p /usr/bin/python$PYTHON_VERSION \
 && export VIRTUAL_ENV=$JUPYTER_DIR \
 && uv pip install "jupyterlab==4.*" "jupyterhub==5.*" pytest \
 && uv clean \
 && jupyter lab clean \
 && uv pip list --format=freeze > $JUPYTER_DIR/requirements-jupyter.txt \
 && find $JUPYTER_DIR -follow -type f \( -name '*.a' -o -name '*.pyc' -o -name '*.js.map' \) -delete \
 && cd $HOME && rm -rf .* * \
 && fix-permissions $JUPYTER_DIR


WORKDIR $HOME
