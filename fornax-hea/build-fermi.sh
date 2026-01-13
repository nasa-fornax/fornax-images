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

# install Fermitools
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
    - boto3
EOF

# Use the yml to create the ciao env
bash /usr/local/bin/setup-conda-env  <<< yes

# Get fermitools version
FERMITOOLS_VERSION=$(micromamba list fermitools -p $ENV_DIR/fermi --json | jq -r '.[0].version')

# (re)move data files;
bash $script_dir/build-map-data.sh $ENV_DIR/fermi/share/fermitools/refdata fermitools-${FERMITOOLS_VERSION}

# clean
cd $HOME
rm -rf $WORKDIR
