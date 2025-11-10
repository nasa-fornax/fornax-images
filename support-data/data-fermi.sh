#!/usr/bin/bash

# Location of support data
if [ -z $SUPPORT_DATA_DIR ]; then
    echo "ERROR: SUPPORT_DATA_DIR not defined"
    exit 1
fi

FERMI_VERSION=2.4.0
micromamba create -y -p $ENV_DIR/fermi-data python=3.11 fermitools=$FERMI_VERSION \
    -c fermi -c conda-froge

mkdir -p $SUPPORT_DATA_DIR/fermitools-$FERMI_VERSION/
cp -r $ENV_DIR/fermi-data/share/fermitools/data $SUPPORT_DATA_DIR/fermitools-$FERMI_VERSION/
cp -r $ENV_DIR/fermi-data/share/fermitools/refdata $SUPPORT_DATA_DIR/fermitools-$FERMI_VERSION/

# remove conda packages
micromamba env remove -y -p $ENV_DIR/fermi-data