#!/bin/bash

# if something fails, keep going, we don't want to the stop the server from loading
set +e

# include any code that needs to be run before the start of the jupyter session

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
    cp /opt/scripts/introduction.html $NOTEBOOK_DIR
fi
if test -f $NOTEBOOK_DIR/introduction.md; then
    rm $NOTEBOOK_DIR/introduction.md
fi
