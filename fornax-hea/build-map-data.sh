#!/usr/bin/bash
# This is a script used by other build scripts to map data to SUPPORT_DATA_DIR
# The data will be stored in $SUPPORT_DATA_DIR instead of $ENV_DIR and symlinks
# are added in ENV_DIR; so the software dir is not bloated and at the same time, 
# the data is available for standalone image use. In the deployment, SUPPORT_DATA_DIR
# is overriden and $ENV_DIR is access from the AMI.
# Example usage:
# ./build-map-data.sh $ENV_DIR/heasoft/heasoft/refdata heasoft-$HEA_VERSION

set -e

src=$1
dest=$2
if [[ -z $src || -z $dest ]]; then
    printf "USAGE: \n $0 src dest\n"
    exit 1
fi
dirname=$(basename $src)
echo " Mapping: | $src -> $dest"
mkdir -p $SUPPORT_DATA_DIR/$dest
# It is possible $src does not exist, but we still need the symlink
if [ -d $src ]; then
    mv $src $SUPPORT_DATA_DIR/$dest
fi
ln -sf $SUPPORT_DATA_DIR/$dest/$dirname $src
