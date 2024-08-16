#!/bin/bash

env=notebook

# jupyter overrides
mkdir -p $CONDA_DIR/envs/$env/share/jupyter/lab/settings/
mv ~/build/overrides.json $CONDA_DIR/envs/$env/share/jupyter/lab/settings/

# disable the annoucement extension
mamba run -n $env jupyter labextension disable "@jupyterlab/apputils-extension:announcements"