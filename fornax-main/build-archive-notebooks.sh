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

# fix kernel names for irsa
for nb in `find . -name '*.md'`; do
    $JUPYTER_DIR/bin/jupytext --set-kernel py-irsa-tutorials $nb
done

# SPHEREx is special
cd spherex/spherex_source_discovery
mv conda-spherex_sdt.yml conda-py-spherex_sdt.yml
setup-conda-env <<< yes

nb=spherex/spherex_source_discovery/spherex_source_discovery_tool_demo.md
$JUPYTER_DIR/bin/jupytext --set-kernel py-spherex_sdt $nb
## -------- END IRSA notebooks -------- ##


## -------- START HEASARC notebooks -------- ##
# All notbeooks are using the heasoft environment for now.

## -------- END HEASARC notebooks -------- ##
rm -rf /tmp/*