#!/usr/bin/bash

# Location of support data
if [ -z $SUPPORT_DATA_DIR ]; then
    echo "ERROR: SUPPORT_DATA_DIR not defined"
    exit 1
fi

# As the Fornax-Hea image that results from these installation scripts is no longer loaded directly into Fornax, and
#  is instead split up so that the large software packages are served in Amazon Machine Images (AMI), we can
#  must take some steps to ensure that this image is usable on platforms other than Fornax.
# This includes making a real, root-level, shared-storage/support-data directory (which on Fornax proper is mounted
#  from an AWS storage solution), so that the high-energy software installations can be shipped with the necessary
#  support data in the same place it will be on Fornax itself
mkdir -p /shared-storage/support-data

# install heasoft; do it in a script instead of yml file so
# get more control over the spectral data files
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
  - python=3.12
  - heasoft=6.35.*
  - pip
  - pip:
    - pytest
    - astroquery
    - astropy
    - s3fs
    - boto3
EOF

# Use conda-heasoft.yml to create the heasoft env
bash /usr/local/bin/conda-env-install.sh

# Extract the heasoft version
HEA_VERSION=$(micromamba list heasoft -p $ENV_DIR/heasoft --json | jq -r '.[0].version')

# Tweak Xspec settings for a no-X11 environment
# add xspec and xstar model data from the data location in $headata
printf "setplot splashpage off\ncpd /GIF\n" >> $ENV_DIR/heasoft/heasoft/spectral/scripts/global_customize.tcl

# remove refdata that comes in the package. We'll use the one in SUPPORT_DATA_DIR instead.
#rm -rf $ENV_DIR/heasoft/heasoft/refdata

# Move the reference data required by HEASoft to the support data directory - this is necessary so that the
#  everything-included Fornax-Hea image setup matches that of deployed Fornax-AMI setup, which holds
#  the reference data in an existing support data directory
mv $ENV_DIR/heasoft/heasoft/refdata $SUPPORT_DATA_DIR/heasoft-${HEA_VERSION}/refdata
# Link refdata, including heasoft, xstar etc.
ln -sf $SUPPORT_DATA_DIR/heasoft-${HEA_VERSION}/refdata $ENV_DIR/heasoft/heasoft/refdata

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
