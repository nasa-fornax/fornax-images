#!/usr/bin/bash

# Location of support data
if [ -z $SUPPORT_DATA_DIR ]; then
    echo "ERROR: SUPPORT_DATA_DIR not defined"
    exit 1
fi

# As the Fornax-Hea image that results from these installation scripts is no longer loaded directly into Fornax, and
#  is instead split up so that the large software packages are served in Amazon Machine Images (AMI), we can
#  must take some steps to ensure that this image is usable on platforms other than Fornax.
# First remove the existing, inevitably broken because it is pointing to a non-mounted Fornax resource, directory -
#  there is some directory-checking logic here because another of the build scripts may have already done this
[ -L $SUPPORT_DATA_DIR ] && ! [ -e $SUPPORT_DATA_DIR ] && rm $SUPPORT_DATA_DIR
# Then make a new support data directory
mkdir -p $SUPPORT_DATA_DIR

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
EOF

# Use the yml to create the ciao env
bash /usr/local/bin/conda-env-install.sh

# Get fermitools version
FERMITOOLS_VERSION=$(micromamba list fermitools -p $ENV_DIR/fermi --json | jq -r '.[0].version')

# Move the reference data required by Fermitools to the support data directory - this is necessary so that the
#  everything-included Fornax-Hea image setup matches that of deployed Fornax-AMI setup, which holds
#  the reference data in an existing support data directory
mkdir -p $SUPPORT_DATA_DIR/fermitools-${FERMITOOLS_VERSION}
mv $ENV_DIR/fermi/share/fermitools/refdata $SUPPORT_DATA_DIR/fermitools-${FERMITOOLS_VERSION}/refdata

# Link the refdata files back to the fermitools directory
ln -sf $SUPPORT_DATA_DIR/fermitools-${FERMITOOLS_VERSION}/refdata $ENV_DIR/fermi/share/fermitools/refdata

# clean
cd $HOME
rm -rf $WORKDIR