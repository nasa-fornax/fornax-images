#!/usr/bin/bash
# Copyright 2026, University of Maryland, All Rights Reserved


# exit on failure; error on undefiend vars; print commands
set -eux
set -o pipefail

# Location of support data
if [ -z $SUPPORT_DATA_DIR ]; then
    echo "ERROR: SUPPORT_DATA_DIR not defined"
    exit 1
fi

# get current dir
script_dir=/usr/local/bin

# install Fermitools
WORKDIR=/tmp/fermi
mkdir -p $WORKDIR
cd $WORKDIR

rm -rf * > /dev/null 2>&1

# TODO IF UPDATING, CHECK WHETHER 'gammapy' HAS A RELEASE VERSION HIGHER THAN 2.1, IF
#  YES THEN YOU CAN PROBABLY REMOVE THE REGION<0.12 RESTRICTION.
# TODO Python=3.11 is driven by fermitools, once it has non-dev conda releases
#  built for versions later than 3.11 this should be replaced by 'python=$PYTHON_VERSION'
cat <<EOF > conda-fermi.yml
name: fermi
channels:
  - fermi
  - conda-forge
dependencies:
  - python=3.12
  - regions<0.12
  - fermitools=2.5.2
  - fermipy
  - pip
  - pip:
    - pytest
EOF

# Use the yml to create the ciao env
bash /usr/local/bin/setup-conda-env  <<< yes

# Get fermitools version
FERMITOOLS_VERSION=$(micromamba list fermitools -p $ENV_DIR/fermi --json | jq -r '.[0].version')

# (re)move data files;
bash $script_dir/map-data.sh $ENV_DIR/fermi/share/fermitools/refdata fermitools-${FERMITOOLS_VERSION}

# clean
cd $HOME
rm -rf $WORKDIR
