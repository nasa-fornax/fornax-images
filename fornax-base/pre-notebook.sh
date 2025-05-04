#!/bin/bash

# if something fails, keep going, we don't want to the stop the server from loading
set +e

# Make sure we have a landing page
if test -z $NOTEBOOK_DIR; then export NOTEBOOK_DIR=$HOME/notebooks; fi
mkdir -p $NOTEBOOK_DIR
if test -f /opt/scripts/introduction.html; then
    cp /opt/scripts/introduction.html $NOTEBOOK_DIR
fi
if test -f $NOTEBOOK_DIR/introduction.md; then
    rm $NOTEBOOK_DIR/introduction.md
fi
