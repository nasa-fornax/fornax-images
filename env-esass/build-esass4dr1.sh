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
# UNFORTUNATELY THIS APPROACH ISN'T REALLY POSSIBLE, AS THE HEASOFT ENVIRONMENT IS COPIED TO
#  THIS IMAGE ONLY AFTER THIS SCRIPT IS RUN.
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
#  in order to save storage space. As such, we first do a dry run of the install, so the environment
#  can be resolved, then edited to stop the installation of HEASoft.
cat <<EOF > temp-conda-solve-$ENV_NAME.yml
name: $ENV_NAME
channels:
  - https://heasarc.gsfc.nasa.gov/FTP/software/conda
  - conda-forge
  - nodefaults
dependencies:
  - python=$PYTHON_VERSION
  - davidt3::esass4dr1
  - heasoft=$HEA_VERSION
  - lynx
  - pip
EOF

# We now use the temporary environment yml file above to perform a dry-run of the install, outputting the
#  list of conda packages to install, their versions, and exact build IDs, as well as the source of the
#  package, to a file.
micromamba create -p "$ENV_NAME" -f temp-conda-solve-$ENV_NAME.yml --dry-run --json > env-solve.json \
  || { cat env-solve.json; exit 1; }

# We extract every package to be installed, with the exception of HEASoft and eSASS, which are disregarded
CONDA_DEPS=$(jq -r '.actions.LINK[] | select(.name != "heasoft" and .name != "esass4dr1") | "  - \(.name)=\(.version)=\(.build_string)"' env-solve.json)

# As we intend to install eSASS into the environment later, with a flag disabling the installation of dependencies, we do still need
#  to extract the exact version and build ID of the eSASS package.
ESASS_SPEC=$(jq -r 'first(.actions.LINK[] | select(.name == "esass4dr1") | "\(.name)=\(.version)=\(.build_string)") // empty' env-solve.json)
if [ -z "$ESASS_SPEC" ]; then
    echo "ERROR: could not find esass4dr1 in env-solve.json"
    exit 1
fi

# Now we construct the real environment yaml file, which will contain everything we need to install
#  (including the dependencies installed through pip this time).
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

# Install the eSASS package (with version and build ID identified by the dry run installation earlier) into
#  the environment. We include the '--no-deps' flag to ensure that no dependencies are installed at the
#  same time (as it would try to install HEASoft, and avoiding that is the reason we have to
#  jump through all these hoops in this script in the first place).
micromamba install -n $ENV_NAME --no-deps -c https://heasarc.gsfc.nasa.gov/FTP/software/conda -c conda-forge "davidt3::${ESASS_SPEC}"
###########################################################


############ Preparing (de)activation scripts #############
ln -sf $ENV_DIR/heasoft/etc/conda/activate.d/heainit.sh $ENV_DIR/$ENV_NAME/etc/conda/activate.d/heainit.sh
ln -sf $ENV_DIR/heasoft/heasoft $ENV_DIR/$ENV_NAME/heasoft

# The path to the eROSITA CalDB directory on Fornax
caldb_dir=$SUPPORT_DATA_DIR/erosita_caldb4DR1

# Modify the eSASS activation script to set the CALDB environment variable at the
#  very start
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

EOF
###########################################################

# clean and reset
cd $HOME
rm -rf $WORKDIR