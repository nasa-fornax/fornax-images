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
cd /tmp/
git clone --branch deploy_to_fornax --depth 1 https://github.com/Caltech-IPAC/irsa-tutorials/
mv irsa-tutorials/irsa-tutorials $NOTEBOOK_DIR

# setup the kernel
cd $NOTEBOOK_DIR/irsa-tutorials
# remove packages already in the jupyter env
sed -i -e '/jupytext/d' -e '/jupyterlab-myst/d' -e '/firefly-extensions/d' requirements-irsa-tutorials.txt
mv requirements-irsa-tutorials.txt requirements-py-irsa-tutorials.txt
# setup the environment
setup-pip-env <<< yes

# fix kernel names
for nb in `find . -name '*.md'`; do
    $JUPYTER_DIR/bin/jupytext --set-kernel py-irsa-tutorials $nb
done

# clean
rm -rf /tmp/irsa-tutorials
## -------- END IRSA notebooks -------- ##


## -------- START HEASARC notebooks -------- ##
cd /tmp/
git clone --branch production-notebooks --depth 1 https://github.com/heasarc/heasarc-tutorials
mv heasarc-tutorials/ $NOTEBOOK_DIR

cd $NOTEBOOK_DIR/heasarc-tutorials/
rm README.md
find . -type f -name '*.ipynb' -delete

# All notbeooks are using the heasoft environment for now.

## -------- END HEASARC notebooks -------- ##