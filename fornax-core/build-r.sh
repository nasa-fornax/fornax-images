#!/bin/bash
# Add R kernel
set -eux
set -o pipefail

cd /tmp/

envfile=conda-Renv.yml
envname=Renv

cat <<EOF > $envfile
name: heasoft
channels:
  - conda-forge
  - nodefaults
dependencies:
  - r
  - r-irkernel
EOF

micromamba create -y -p $ENV_DIR/Renv -f $envfile

# add the environment as a jupyter kernel
micromamba run -p $ENV_DIR/Renv R -e "IRkernel::installspec(prefix = Sys.getenv('JUPYTER_DIR'))"
fix-permissions $ENV_DIR/Renv
micromamba clean -yaf
rm -rf /tmp/*
