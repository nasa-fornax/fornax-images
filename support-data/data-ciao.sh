#!/usr/bin/bash

# Location of support data
if [ -z $SUPPORT_DATA_DIR ]; then
    echo "ERROR: SUPPORT_DATA_DIR not defined"
    exit 1
fi

CIAO_VERSION=4.17
CIAO_CALDB=4.12.0
micromamba create -y -p $ENV_DIR/ciao-data python=3.11 caldb_main=$CIAO_CALDB sherpa ciao-contrib ciao=$CIAO_VERSION \
    -c https://cxc.cfa.harvard.edu/conda/ciao -c conda-forge

mkdir -p $SUPPORT_DATA_DIR/ciao-$CIAO_VERSION/spectral
cp -r $ENV_DIR/ciao-data/spectral/modelData $SUPPORT_DATA_DIR/ciao-$CIAO_VERSION/spectral

cp -r $ENV_DIR/ciao-data/CALDB $SUPPORT_DATA_DIR/ciao-caldb-$CIAO_CALDB

# remove conda packages
micromamba env remove -y -p $ENV_DIR/ciao-data