#!/usr/bin/bash

# Location of support data
if [ -z $SUPPORT_DATA_DIR ]; then
    echo "ERROR: SUPPORT_DATA_DIR not defined"
    exit 1
fi

# install ciao; do it in a script instead of yml file so
# get more control over the spectral data files
WORKDIR=/tmp/fermi
mkdir -p $WORKDIR
cd $WORKDIR

rm -rf * > /dev/null 2>&1

cat <<EOF > conda-fermi.yml
name: fermi
channels:
  - fermi
  - conda-forge
dependencies:
  - python=3.11
  - fermitools=2.4
  - fermipy
  - pip
  - pip:
    - pytest
    - astroquery
    - astropy
    - s3fs
EOF

# Use the yml to create the ciao env
bash /usr/local/bin/conda-env-install.sh


# delete data; create simlinks below
rm -rf $ENV_DIR/fermi/share/fermitools/refdata

# Remove these files
# none


# get fermitools version
FERMITOOLS_VERSION=$(micromamba list fermitools -p $ENV_DIR/fermi --json | jq -r '.[0].version')

# link data files
ln -sf $SUPPORT_DATA_DIR/fermitools-${FERMITOOLS_VERSION}/refdata $ENV_DIR/fermi/share/fermitools/refdata

# clean
cd $HOME
rm -rf $WORKDIR