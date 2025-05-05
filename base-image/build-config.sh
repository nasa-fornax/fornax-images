#!/bin/bash

env=notebook

# jupyter overrides
mkdir -p $CONDA_DIR/envs/$env/share/jupyter/lab/settings/
mv ~/build/overrides.json $CONDA_DIR/envs/$env/share/jupyter/lab/settings/


# disable the announcement extension
mamba run -n $env jupyter labextension disable "@jupyterlab/apputils-extension:announcements"

# install openvscode-server
cd /tmp/
wget -q https://github.com/gitpod-io/openvscode-server/releases/download/openvscode-server-v1.98.2/openvscode-server-v1.98.2-linux-x64.tar.gz
tar -zxvf openvscode-server-v1.98.2-linux-x64.tar.gz
mv openvscode-server-v1.98.2-linux-x64 /opt/openvscode-server
