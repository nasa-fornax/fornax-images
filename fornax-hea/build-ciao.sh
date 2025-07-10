#!/usr/bin/bash

# Location of support data
if [ -z $SUPPORT_DATA_DIR ]; then
    echo "ERROR: SUPPORT_DATA_DIR not defined"
    exit 1
fi

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
  - ciao=4.17
  - sherpa
  - ciao-contrib
  - marx
  - pytest
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
CALDB_VERSION=$(micromamba list caldb_main -p $ENV_DIR/ciao --json | jq -r '.[0].version')

# link modelData
ln -sf $SUPPORT_DATA_DIR/ciao-${CIAO_VERSION}/spectral/modelData $ENV_DIR/ciao/spectral/modelData
# link caldb.
ln -sf $SUPPORT_DATA_DIR/ciao-caldb-${CIAO_VERSION}/CALDB $ENV_DIR/ciao/CALDB

# clean
cd $HOME
rm -rf $WORKDIR