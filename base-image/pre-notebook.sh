#!/bin/bash

# if something fails, keep going, we don't want to the stop the server from loading
set +e

# include any code that needs to be run before the start of the jupyter session

# remove the old nb_conda_kernels defined in the user directory
# so they don't show up in the Jupyterlab launcher
rm -rf ~/.local/share/jupyter/kernels/conda-base-py &>/dev/null
rm -rf ~/.local/share/jupyter/kernels/conda-env-science_demo-py &>/dev/null

# remove old condarc in the user's home; continue gracefully
find ~/.condarc -type f ! -newermt "2024-11-26" -delete &>/dev/null || true

# cleanup cache accmulated before the new cache location at /tmp/cache
cd $HOME
for dir in users_conda_envs .astropy/cache .cache; do
    rm $dir &>/dev/null
done

# remove any old pip cache
pip cache purge &>/dev/null

# clean any conda cache
mamba clean -yaf &>/dev/null

# Make sure we have a landing page
if test -z $NOTEBOOK_DIR; then export NOTEBOOK_DIR=$HOME/notebooks; fi
mkdir -p $NOTEBOOK_DIR
if test -f /opt/scripts/introduction.html; then
    mv  /opt/scripts/introduction.html $NOTEBOOK_DIR
fi
if test -f $NOTEBOOK_DIR/introduction.md; then
    rm  $NOTEBOOK_DIR/introduction.md
fi
touch $NOTEBOOK_DIR/introduction.html
