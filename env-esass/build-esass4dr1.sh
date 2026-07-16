#!/usr/bin/bash

# exit on failure; error on undefined vars; print commands
set -eux
set -o pipefail

# Location of support data
if [ -z $SUPPORT_DATA_DIR ]; then
    echo "ERROR: SUPPORT_DATA_DIR not defined"
    exit 1
fi

############### Setting up useful variables ###############
# Define the name of the environment to be set up
export ENV_NAME=esass4dr1
###########################################################


# get current dir
script_dir=/usr/local/bin


WORKDIR=/tmp/esass4dr1
mkdir -p $WORKDIR
cd $WORKDIR

rm -rf * > /dev/null 2>&1

cat <<EOF > conda-$ENV_NAME.yml
name: $ENV_NAME
channels:
  - https://heasarc.gsfc.nasa.gov/FTP/software/conda
  - conda-forge
  - davidt3
  - nodefaults
dependencies:
  - python=$PYTHON_VERSION
  - esass4dr1
  - heasoft=6.36.*
  - lynx
  - pip
  - pip:
    - pytest
    - astroquery
    - astropy
    - s3fs
    - boto3
    - xga>=0.6.3
    - daxa
EOF

# Use conda-esass4dr1.yml to create the esass4dr1 env
bash /usr/local/bin/setup-conda-env <<< yes

# Extract the HEASoft package version
HEA_VERSION=$(micromamba list heasoft -p $ENV_DIR/$ENV_NAME --json | jq -r '.[0].version')

# (re)move data files;
bash $script_dir/map-data.sh $ENV_DIR/$ENV_NAME/heasoft/refdata heasoft-$HEA_VERSION
bash $script_dir/map-data.sh $ENV_DIR/$ENV_NAME/heasoft/spectral/modelData heasoft-$HEA_VERSION/spectral

# Tweak Xspec settings for a no-X11 environment
# add xspec model data from the data location
printf "setplot splashpage off\ncpd /nu" >> $ENV_DIR/$ENV_NAME/heasoft/spectral/scripts/global_customize.tcl

# set lynx as default for opening help files
sed -i 's/HTML_COMMAND:[[:space:]]*firefox/HTML_COMMAND:  lynx/g' $ENV_DIR/$ENV_NAME/heasoft/spectral/manager/Xspec.init

# XSPEC modelData - THIS LINK WILL BE BROKEN IN THE IMAGE - but we will direct users to download and install
#  the XSPEC model package instead
ln -sf $SUPPORT_DATA_DIR/heasoft-${HEA_VERSION}/spectral/modelData $ENV_DIR/$ENV_NAME/heasoft/spectral/modelData

# The path to the eROSITA CalDB on Fornax
caldb_dir=$SUPPORT_DATA_DIR/erosita_caldb4DR1

# Modify the eSASS activation script to set the CALDB environment variable at the
#  very start
ACTIVATE_FILE="$ENV_DIR/$ENV_NAME/etc/conda/activate.d/post_heasoft_esass_activate.sh"
echo "export CALDB=$caldb_dir" | cat - "$ACTIVATE_FILE" > temp_file && mv temp_file "$ACTIVATE_FILE"

# We also make sure to add the CALDB (and co) unsetting commands to the deactivation
#  script
DEACTIVATE_FILE="$ENV_DIR/$ENV_NAME/etc/conda/deactivate.d/esass_deactivate.sh"
cat << 'EOF' >> "$DEACTIVATE_FILE"
unset CALDB
unset CALDBCONFIG
unset CALDBALIAS
unset SASS_CALVERS
EOF

# clean and reset
cd $HOME
rm -rf $WORKDIR