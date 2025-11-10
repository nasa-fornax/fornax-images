#!/usr/bin/bash

# Location of support data
if [ -z $SUPPORT_DATA_DIR ]; then
    echo "ERROR: SUPPORT_DATA_DIR not defined"
    exit 1
fi

mkdir -p $SUPPORT_DATA_DIR/xmm_ccf
cd $SUPPORT_DATA_DIR/xmm_ccf
wget -nH --no-remove-listing -N -np -r --cut-dirs=4 -e robots=off -l 1 -R "index.html*" \
    https://heasarc.gsfc.nasa.gov/FTP/xmm/data/CCF/