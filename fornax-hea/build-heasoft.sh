#!/usr/bin/bash

# exit on failure; error on undefiend vars; print commands
set -eux
set -o pipefail

# Location of support data
if [ -z $SUPPORT_DATA_DIR ]; then
    echo "ERROR: SUPPORT_DATA_DIR not defined"
    exit 1
fi

# get current dir
script_dir=$(pwd)

# install heasoft; do it in a script instead of yml file so
# we get more control over the spectral data files
WORKDIR=/tmp/heasoft
mkdir -p $WORKDIR
cd $WORKDIR

rm -rf * > /dev/null 2>&1

cat <<EOF > conda-heasoft.yml
name: heasoft
channels:
  - https://heasarc.gsfc.nasa.gov/FTP/software/conda
  - conda-forge
  - nodefaults
dependencies:
  - python=$PYTHON_VERSION
  - heasoft=6.36.*
  - pip
  - pip:
    - pytest
    - astroquery
    - astropy
    - s3fs
    - boto3
EOF

# Use conda-heasoft.yml to create the heasoft env
bash /usr/local/bin/setup-conda-env <<< yes

# Extract the heasoft version
HEA_VERSION=$(micromamba list heasoft -p $ENV_DIR/heasoft --json | jq -r '.[0].version')

# (re)move data files;
bash $script_dir/build-map-data.sh $ENV_DIR/heasoft/heasoft/refdata heasoft-$HEA_VERSION
bash $script_dir/build-map-data.sh $ENV_DIR/heasoft/heasoft/spectral/modelData heasoft-$HEA_VERSION/spectral

# Tweak Xspec settings for a no-X11 environment
# add xspec model data from the data location
printf "setplot splashpage off\ncpd /GIF\n" >> $ENV_DIR/heasoft/heasoft/spectral/scripts/global_customize.tcl

# XSPEC modelData - THIS LINK WILL BE BROKEN IN THE IMAGE - but we will direct users to download and install
#  the XSPEC model package instead
ln -sf $SUPPORT_DATA_DIR/heasoft-${HEA_VERSION}/spectral/modelData $ENV_DIR/heasoft/heasoft/spectral/modelData


# Add CALDB; use remote caldb for now
caldb_dir=$ENV_DIR/heasoft/caldb
mkdir -p $caldb_dir
cd $caldb_dir
wget -qL https://heasarc.gsfc.nasa.gov/FTP/caldb/software/tools/caldb.config
wget -qL https://heasarc.gsfc.nasa.gov/FTP/caldb/software/tools/alias_config.fits

cat << EOF > $ENV_DIR/heasoft/etc/conda/activate.d/caldb_activate.sh
export CALDBCONFIG=$caldb_dir/caldb.config
export CALDBALIAS=$caldb_dir/alias_config.fits
export CALDB=https://heasarc.gsfc.nasa.gov/FTP/caldb
EOF

# clean and reset
cd $HOME
rm -rf $WORKDIR