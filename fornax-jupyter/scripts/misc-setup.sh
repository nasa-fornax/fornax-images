#!/bin/bash
# Copyright 2026, University of Maryland, All Rights Reserved


# Add ~/.profile if it does not exist; which sources ~/.bashrc
# JL terminals source ~/.profile not ~/.bashrc
# But some user software may need ~/.bashrc (e.g. rust, julia)

# if something fails, keep going
set +ex
if [ ! -f /home/$NB_USER/.profile ]; then
    cat <<PROFILE > /home/$NB_USER/.profile
if [ -f /home/$NB_USER/.bashrc ]; then
    source /home/$NB_USER/.bashrc
fi
PROFILE
    chown $NB_UID:$NB_GID /home/$NB_USER/.profile
fi
# reset exit-on-error
set -e

## ----------------------------------------- ##
## Define some runtime environment variables ##
# for custom user environments
export USER_ENV_DIR="/home/$NB_USER/user-envs"
# where uv installs custom python binaries
export UV_PYTHON_INSTALL_DIR="/home/$NB_USER/user-envs/python"
# allow micromamba to find $USER_ENV_DIR
export CONDA_ENVS_PATH=$USER_ENV_DIR
# for vscode
export CODE_EXECUTABLE=code-server
export CODE_EXTENSIONSDIR="/home/$NB_USER/.local/share/code-server/extensions"
# For firefly
export FIREFLY_URL=https://irsacloud.ipac.caltech.edu/firefly \
# for dask
export DASK_DISTRIBUTED__DASHBOARD__LINK="/jupyter/user/{JUPYTERHUB_USER}/proxy/{port}/status"
# Tell dask-labextension to use GatewayCluster
# export DASK_LABEXTENSION__FACTORY__MODULE="dask_gateway"
# export DASK_LABEXTENSION__FACTORY__CLASS="GatewayCluster"

# image version
export FORNAX_SOFTWARE_VERSION=$(sed -n '/^##/ { s/^##[[:space:]]*//; p; q; }' $NOTEBOOK_DIR/changes.mdv)

## Clean the home dir if needed
# CLEAN_HOME=0
if [[ "$CLEAN_HOME" == "1" ]]; then
    echo "Cleaning home folder in /home/$NB_USER"
    stamp=`date +%s%3N`
    if [ -d "/home/$NB_USER/.jupyter" ]; then
        echo "renaming /home/$NB_USER/.jupyter to ~/.jupyter-$stamp"
        mv /home/$NB_USER/.jupyter /home/$NB_USER/.jupyter-$stamp
    fi
fi
## ----------------------------------------- ##

## ------------------------------------ ##
## Create a symlink to /scratch in $HOME
if [[ ! -e /home/$NB_USER/scratch && ! -L /home/$NB_USER/scratch && -d /scratch ]]; then
    ln -s /scratch /home/$NB_USER/
fi
## ------------------------------------ ##