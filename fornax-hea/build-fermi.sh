#!/usr/bin/bash

# Location of support data
if [ -z $SUPPORT_DATA_DIR ]; then
    echo "ERROR: SUPPORT_DATA_DIR not defined"
    exit 1
fi

# As the Fornax-Hea image that results from these installation scripts is no longer loaded directly into Fornax, and
#  is instead split up so that the large software packages are served in Amazon Machine Images (AMI), we can
#  must take some steps to ensure that this image is usable on platforms other than Fornax.
# This includes making a real, root-level, shared-storage/support-data directory (which on Fornax proper is mounted
#  from an AWS storage solution), so that the high-energy software installations can be shipped with the necessary
#  support data in the same place it will be on Fornax itself
mkdir -p /shared-storage/support-data

# install Fermitools
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
bash /usr/local/bin/conda-env-install.sh

# Get fermitools version
FERMITOOLS_VERSION=$(micromamba list fermitools -p $ENV_DIR/fermi --json | jq -r '.[0].version')

# Move the reference data required by Fermitools to the support data directory - this is necessary so that the
#  everything-included Fornax-Hea image setup matches that of deployed Fornax-AMI setup, which holds
#  the reference data in an existing support data directory
mv $ENV_DIR/fermi/share/fermitools/refdata $SUPPORT_DATA_DIR/fermitools-${FERMITOOLS_VERSION}/refdata

# Link the refdata files back to the fermitools directory
ln -sf $SUPPORT_DATA_DIR/fermitools-${FERMITOOLS_VERSION}/refdata $ENV_DIR/fermi/share/fermitools/refdata

# clean
cd $HOME
rm -rf $WORKDIR
