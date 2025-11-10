#!/usr/bin/bash

# Location of support data
if [ -z $SUPPORT_DATA_DIR ]; then
    echo "ERROR: SUPPORT_DATA_DIR not defined"
    exit 1
fi

HEASOFT_VERSION=6.36
micromamba create -p $ENV_DIR/hea-data -y heasoft=$HEASOFT_VERSION xspec-data \
    -c https://heasarc.gsfc.nasa.gov/FTP/software/conda/ -c conda-forge


# Copy data files
mkdir -p $SUPPORT_DATA_DIR/heasoft-$HEASOFT_VERSION
cp -r $ENV_DIR/hea-data/heasoft/refdata $SUPPORT_DATA_DIR/heasoft-$HEASOFT_VERSION
cp -r $ENV_DIR/hea-data/heasoft/spectral/modelData $SUPPORT_DATA_DIR/heasoft-$HEASOFT_VERSION/spectral

# remove conda packages
micromamba env remove -y -p $ENV_DIR/hea-data