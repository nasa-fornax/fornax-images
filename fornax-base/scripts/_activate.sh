#!/usr/bin/bash
# A script to activate the default environment from DEFAULT_ENV

if [ -f \$ENV_DIR/\$DEFAULT_ENV/bin/activate ]; then
  echo activating python in \$ENV_DIR/\$DEFAULT_ENV
  source \$ENV_DIR/\$DEFAULT_ENV/bin/activate
elif [ -d \$ENV_DIR/\$DEFAULT_ENV/conda-meta ]; then
  echo activating python in \$ENV_DIR/\$DEFAULT_ENV
  micromamba activate \$DEFAULT_ENV
else
  echo DEFAULT_ENV=\$DEFAULT_ENV not found
fi