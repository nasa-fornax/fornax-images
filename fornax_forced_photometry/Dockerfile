FROM jupyterhub/k8s-singleuser-sample:0.11.1
# Replace `latest` with an image tag from to ensure reproducible builds:
# https://hub.docker.com/r/jupyter/scipy-notebook/tags/
# Inspect the Dockerfile at:
# https://github.com/jupyter/docker-stacks/tree/HEAD/scipy-notebook/Dockerfile

USER root

# Configure environment

ENV SHELL=/bin/bash \
    LC_ALL=C.UTF-8 \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8

# Add a script that we will use to correct permissions after running certain commands

COPY fix-permissions /usr/local/bin/fix-permissions

RUN chmod +x /usr/local/bin/fix-permissions

# Enable prompt color in the skeleton .bashrc before creating the default NB_USER

RUN sed -i 's/^#force_color_prompt=yes/force_color_prompt=yes/' /etc/skel/.bashrc

ENV jl=/usr/local/bin

ENV PROVDIR=${jl}/prov \
    DEBUG=1

COPY selfculler.py \
     runlab.sh \
     ${jl}/

WORKDIR /tmp

# Install Java
RUN apt-get -y update && \
    apt-get install --no-install-recommends -y \
    openjdk-8-jre-headless \
    ca-certificates-java \
    git \
    curl \
    htop \
    vim \
    nano \
    emacs-nox \
    gzip \
    zip \
    unzip \
    bzip2 \
    cmake \
    pkg-config \
    libcairo2-dev \
    libnetpbm10-dev \
    netpbm \
    libjpeg-dev \
    python-numpy \
    python-dev \
    zlib1g-dev \
    libbz2-dev \
    swig \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy start up scripts
COPY scripts/entrypoint.sh /usr/local/bin/
COPY scripts/pre-start-source.sh /usr/local/bin/
COPY condarc /home/$NB_USER/.condarc

ENTRYPOINT [ "/usr/local/bin/entrypoint.sh" ]

# Install mamba
RUN conda install --quiet --yes -c conda-forge mamba

# install additional packages...

RUN mamba install --quiet --yes \
    numpy \
    pip \
    cfitsio \
    fitsio \
    pkg-config \
    matplotlib \
    cairo \
    jpeg \
    astropy \
    scipy \
    seaborn \
    swig \
    astroquery \
    reproject \
    scikit-learn \
    nbgitpuller && \
    conda clean --all -f -y && \
    pip install --no-cache-dir firefly_client && \
    pip install --no-cache-dir jupyter_firefly_extensions && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER

RUN cd /home/jovyan && \
    mkdir code && \
    cd code && \
    git clone https://github.com/dstndstn/astrometry.net.git && \
    cd astrometry.net && \
    make && \
    make py && \
    python setup.py install && \
    export PYTHONPATH=$PWD:$PYTHONPATH && \
    cd .. && \
    git clone https://github.com/dstndstn/tractor.git && \
    cd tractor && \
    make && \
    python setup.py install && \
    export PYTHONPATH=$PWD:$PYTHONPATH && \
    cd /home/jovyan

# Install Jupyter Proxy Server
RUN mamba install --quiet --yes \
    'jupyter-server-proxy' \
    -c conda-forge && \
    jupyter labextension install --no-build \
    @jupyterlab/server-proxy \
    jupyter-matplotlib \
    jupyter_firefly_extensions && \
    jupyter lab build --dev-build=False --minimize=False && \
    jupyter serverextension enable --py jupyter_firefly_extensions && \
    conda clean --all -f -y && \
    fix-permissions $CONDA_DIR && \
    fix-permissions /home/$NB_USER

USER $NB_UID

# set the default command of the image,
# if the parent image will not launch a jupyterhub singleuser server.
# The JupyterHub "Docker stacks" do not need to be overridden.
# Set either here or in `singleuser.cmd` in your values.yaml
CMD ["jupyterhub-singleuser"]

