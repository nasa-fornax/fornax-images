#!/usr/bin/bash

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
  - python=3.11
  - ciao
  - sherpa
  - ciao-contrib
  - marx
  - pip
  - pip:
    - pytest
    - astroquery
    - astropy
    - s3fs
EOF

# Use the yml to create the ciao env
bash /usr/local/bin/conda-env-install.sh


# delete the model data and caldb; create simlinks below
rm -rf $ENV_DIR/ciao/spectral/modelData
rm -rf $ENV_DIR/ciao/CALDB | true

# Remove these files
rm -rf $ENV_DIR/ciao/test
rm -rf $ENV_DIR/ciao/docs


# get ciao version
CIAO_VERSION=$(micromamba list ciao -p $ENV_DIR/ciao --json | jq -r '.[0].version')
CALDB_VERSION=4.12.0

# link modelData
ln -sf $SUPPORT_DATA_DIR/ciao-${CIAO_VERSION}/spectral/modelData $ENV_DIR/ciao/spectral/modelData
# link caldb.
ln -sf $SUPPORT_DATA_DIR/ciao-caldb-${CALDB_VERSION}/CALDB $ENV_DIR/ciao/CALDB


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