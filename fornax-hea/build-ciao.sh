#!/usr/bin/bash

# exit on failure; error on undefiend vars; print commands
set -eux
set -o pipefail

# Location of support data
if [ -z $SUPPORT_DATA_DIR ]; then
    echo "ERROR: SUPPORT_DATA_DIR not defined"
    exit 1
fi

# First remove the existing, inevitably broken because it is pointing to a non-mounted Fornax resource, directory -
#  there is some directory-checking logic here because another of the build scripts may have already done this
[ -L $SUPPORT_DATA_DIR ] && ! [ -e $SUPPORT_DATA_DIR ] && rm $SUPPORT_DATA_DIR
# Then make a new support data directory
mkdir -p $SUPPORT_DATA_DIR

# install ciao; do it in a script instead of yml file so
# get more control over the spectral data files
WORKDIR=/tmp/ciao
mkdir -p $WORKDIR
cd $WORKDIR

rm -rf * > /dev/null 2>&1

cat <<EOF > conda-ciao.yml
name: ciao
channels:
  - https://cxc.cfa.harvard.edu/conda/ciao
  - conda-forge
dependencies:
  - ciao=4.17.0
  - sherpa
  - ciao-contrib=4.17.0
  - marx
  - pip
  - pip:
    - pytest
    - astroquery
    - astropy
    - s3fs
    - boto3
EOF

# Use the yml to create the ciao env
bash /usr/local/bin/setup-conda-env <<< yes

# Get the CIAO and Chandra-CALDB versions into environment variables
CIAO_VERSION=$(micromamba list ciao -p $ENV_DIR/ciao --json | jq -r '.[0].version')
CALDB_VERSION=4.12.0

# These images form the basis of the environent on the Fornax cloud compute system, but
#  can also be used locally. We already provide these 'supporting files' in a storage
#  mount on Fornax, but we want to include them in the full image as there is no
#  way of downloading the CIAO spectral model files separately.
# First step is to make a directory to put them in, in the $SUPPORT_DATA_DIR
#  directory that we made sure existed at the top of this script
mkdir -p $SUPPORT_DATA_DIR/ciao-${CIAO_VERSION}/spectral/
#mkdir -p $SUPPORT_DATA_DIR/ciao-caldb-${CALDB_VERSION}/

# We then move the spectral model files there (they live in the same place on
#  Fornax), and add a symlink back to their original location. That symlink will
#  also function properly on Fornax itself
mv $ENV_DIR/ciao/spectral/modelData $SUPPORT_DATA_DIR/ciao-${CIAO_VERSION}/spectral/
ln -sf $SUPPORT_DATA_DIR/ciao-${CIAO_VERSION}/spectral/modelData $ENV_DIR/ciao/spectral/modelData

# Move
#mv $ENV_DIR/ciao/CALDB $SUPPORT_DATA_DIR/ciao-caldb-${CALDB_VERSION}/CALDB | true
#ln -sf $SUPPORT_DATA_DIR/ciao-caldb-${CALDB_VERSION}/CALDB $ENV_DIR/ciao/CALDB

# Remove these files - we don't need to include them in the image at all
rm -rf $ENV_DIR/ciao/test
rm -rf $ENV_DIR/ciao/docs


# Writing scripts to ensure the CALDB and HEASoft PFILES paths are properly set up when the CIAO environment is loaded
####### CALDB #######
# Start with the CALDB activation and deactivation scripts - necessary because we're not using the CIAO CALDB conda
#  package, we already have CALDB living somewhere else, and as such the conda activate.d script that calls the
#  CALDB init script does not exist
cat << EOF > $ENV_DIR/ciao/etc/conda/activate.d/caldb_main_activate.sh
export CALDB=$ENV_DIR/ciao/CALDB
export CALDBCONFIG="\$CALDB/software/tools/caldb.config"
export CALDBALIAS="\$CALDB/software/tools/alias_config.fits"
EOF
#####################

###### PFILES #######
# HEASoft software (like the 'nh' tool) cannot find base parameter files to copy by looking in the CIAO
#  'params' directory, causing errors when those tools are to be used. We add the HEASoft environment
#  base-pfile-storage-directory to the PFILES environment variable path, which solves this issue
cat << EOF > $ENV_DIR/ciao/etc/conda/activate.d/ciao-pfiles_activate.sh
#!/bin/bash
# Intended to solve parameter file copying issues for HEASoft tools when using the CIAO conda environment
export PFILES="$PFILES:$ENV_DIR/heasoft/heasoft/syspfiles"
EOF
#####################

# clean
cd $HOME
rm -rf $WORKDIR
