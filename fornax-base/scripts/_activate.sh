#!/usr/bin/bash
# A script to activate the default environment from DEFAULT_ENV


if [ "$DEFAULT_ENV" == "jupyter" ]; then
  env_dir=$JUPYTER_DIR
else
  env_dir=$ENV_DIR/$DEFAULT_ENV
fi

if [ -f $env_dir/bin/activate ]; then
  echo activating python in $env_dir
  source $env_dir/bin/activate
elif [ -d $env_dir/conda-meta ]; then
  echo activating python in $env_dir
  micromamba activate $DEFAULT_ENV
else
  echo DEFAULT_ENV=$DEFAULT_ENV not found in $env_dir
fi