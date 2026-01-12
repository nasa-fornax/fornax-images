#!/bin/bash

# Add ~/.profile if it does not exist; which sources ~/.bashrc
# JL terminals source ~/.profile not ~/.bashrc
# But some user software may need ~/.bashrc (e.g. rust, julia)

if [ ! -f /home/$NB_USER/.profile ]; then
    cat <<PROFILE > /home/$NB_USER/.profile
if [ -f /home/$NB_USER/.bashrc ]; then
    source /home/$NB_USER/.bashrc
fi
PROFILE
fi

## ----------------------------------------- ##
## Define some runtime environment variables ##
# for custom user environments
export USER_ENV_DIR="/home/$NB_USER/user-envs"
# for vscode
export CODE_EXECUTABLE=code-server
export CODE_EXTENSIONSDIR="/home/$NB_USER/.local/share/code-server/extensions"
# For firefly
export FIREFLY_URL=https://irsa.ipac.caltech.edu/irsaviewer \
# for dask
export DASK_DISTRIBUTED__DASHBOARD__LINK="/jupyter/user/{JUPYTERHUB_USER}/proxy/{port}/status"