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


############### Extracting HEASoft version ################
# We need to know the version of HEASoft currently installed in the heasoft environment
#HEA_VERSION=$(micromamba list heasoft -p $ENV_DIR/heasoft --json | jq -r '.packages[0].version')
HEA_VERSION=6.36.*
###########################################################


############## Preparing temporary work area ##############
WORKDIR=/tmp/esass4dr1
mkdir -p $WORKDIR
cd $WORKDIR

rm -rf * > /dev/null 2>&1
###########################################################


############## Defining the environment yaml ##############
# The eSASS conda package has HEASoft as an actual dependency, and we don't want to install it
#  in order to save storage space.
cat <<EOF > temp-conda-solve-$ENV_NAME.yml
name: $ENV_NAME
channels:
  - https://heasarc.gsfc.nasa.gov/FTP/software/conda
  - conda-forge
  - nodefaults
dependencies:
  - python=$PYTHON_VERSION
  - davidt3::esass4dr1
  - heasoft=6.36.*
  - lynx
  - pip
EOF

micromamba create -p "$ENV_NAME" -f temp-conda-solve-$ENV_NAME.yml --dry-run --json > env-solve.json \
  || { cat env-solve.json; exit 1; }
rm temp-conda-solve-$ENV_NAME.yml

CONDA_DEPS=$(jq -r '.actions.LINK[] | select(.name != "heasoft" and .name != "esass4dr1") | "  - \(.name)=\(.version)=\(.build_string)"' env-solve.json)

# Exact esass4dr1 version/build chosen by the dry-run solve
ESASS_SPEC=$(jq -r 'first(.actions.LINK[] | select(.name == "esass4dr1") | "\(.name)=\(.version)=\(.build_string)") // empty' env-solve.json)
if [ -z "$ESASS_SPEC" ]; then
    echo "ERROR: could not find esass4dr1 in env-solve.json"
    exit 1
fi

cat <<EOF > conda-$ENV_NAME.yml
name: $ENV_NAME
channels:
  - https://heasarc.gsfc.nasa.gov/FTP/software/conda
  - conda-forge
  - davidt3
  - nodefaults
dependencies:
$CONDA_DEPS
  - pip:
    - pytest
    - astroquery
    - astropy
    - s3fs
    - boto3
    - xga>=0.6.3
    - daxa
EOF
###########################################################


############## Creating the new environment ###############
# Use conda-esass4dr1.yml to create the esass4dr1 env
bash /usr/local/bin/setup-conda-env <<< yes

micromamba install -n $ENV_NAME --no-deps -c https://heasarc.gsfc.nasa.gov/FTP/software/conda -c conda-forge "davidt3::${ESASS_SPEC}"
###########################################################


# XSPEC modelData - THIS LINK WILL BE BROKEN IN THE IMAGE - but we will direct users to download and install
#  the XSPEC model package instead
#ln -sf $SUPPORT_DATA_DIR/heasoft-${HEA_VERSION}/spectral/modelData $ENV_DIR/$ENV_NAME/heasoft/spectral/modelData

# The path to the eROSITA CalDB on Fornax
caldb_dir=$SUPPORT_DATA_DIR/erosita_caldb4DR1

## Modify the eSASS activation script to set the CALDB environment variable at the
##  very start
#ACTIVATE_FILE="$ENV_DIR/$ENV_NAME/etc/conda/activate.d/post_heasoft_esass_activate.sh"
#echo "export CALDB=$caldb_dir" | cat - "$ACTIVATE_FILE" > temp_file && mv temp_file "$ACTIVATE_FILE"



ln -sf $ENV_DIR/heasoft/etc/conda/activate.d/heainit.sh $ENV_DIR/$ENV_NAME/etc/conda/activate.d/heainit.sh
ln -sf $ENV_DIR/heasoft/heasoft $ENV_DIR/$ENV_NAME/heasoft


sed -i "1i export CALDB=$caldb_dir\nexport CALDBCONFIG=\$CALDB/software/tools/caldb.config\nexport CALDBALIAS=\$CALDB/software/tools/alias_config.fits\nexport SASS_CALVERS=\$CALDB/data/erosita/calvers.indx" "$ENV_DIR/$ENV_NAME/etc/conda/activate.d/post_heasoft_esass_activate.sh"

######
# We also make sure to add the CALDB (and co) unsetting commands to the deactivation
#  script
DEACTIVATE_FILE="$ENV_DIR/$ENV_NAME/etc/conda/deactivate.d/esass_deactivate.sh"
cat << 'EOF' >> "$DEACTIVATE_FILE"
unset CALDB
unset CALDBCONFIG
unset CALDBALIAS
unset SASS_CALVERS

#export LD_LIBRARY_PATH=\$ESASS_PREV_LD_LIBRARY_PATH
EOF
###########################################################

# clean and reset
cd $HOME
rm -rf $WORKDIR