#!/bin/bash
# Copy archive-specific notebooks
set -eu

# if NOTEBOOK_DIR is not defined; return or exit
if test -z $NOTEBOOK_DIR; then
    # since this script is sourced, we return
    echo "NOTEBOOK_DIR not defined; returning ..."
    return 0
fi

## -------- START IRSA notebooks -------- ##

# setup the kernel
cd $NOTEBOOK_DIR/irsa-tutorials
# remove packages already in the jupyter env
sed -i -e '/jupytext/d' -e '/jupyterlab-myst/d' -e '/firefly-extensions/d' requirements-irsa-tutorials.txt
mv requirements-irsa-tutorials.txt requirements-py-irsa-tutorials.txt
# setup the environment
setup-pip-env <<< yes
## -------- END IRSA notebooks -------- ##


## -------- START HEASARC notebooks -------- ##
# All notbeooks are using the heasoft environment for now.

## -------- END HEASARC notebooks -------- ##
rm -rf /tmp/*