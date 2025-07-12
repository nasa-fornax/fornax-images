#!/bin/bash
# Build astronomy.net and tractor
# Assumes build-01-notebook-req.sh has been run

set -e 
set -o pipefail


pythonenv=py-multiband_photometry
astrometry_commit=1b7d716
tractor_commit=8059ae0

export VIRTUAL_ENV=$ENV_DIR/$pythonenv

# We need cython
source $VIRTUAL_ENV/bin/activate
uv pip install cython setuptools numpy
TARGET_DIR=`ls -d ${VIRTUAL_ENV}/lib/python3.??/site-packages`

# Install astrometry.net and tractor
cd /tmp
git clone https://github.com/dstndstn/astrometry.net.git
cd astrometry.net
git config --global --add safe.directory $PWD
git checkout $astrometry_commit
make
make py
make extra
make install INSTALL_DIR=${VIRTUAL_ENV}
mv ${VIRTUAL_ENV}/lib/python/astrometry $TARGET_DIR

cd /tmp
git clone https://github.com/dstndstn/tractor.git
cd tractor
git checkout $tractor_commit
python setup.py build_ext --inplace --with-cython
uv pip install --no-cache-dir . --no-build-isolation  --target $TARGET_DIR
cd $HOME
rm -rf /tmp/astrometry.net /tmp/tractor

# update the freeze file
uv pip list --format=freeze > $VIRTUAL_ENV/requirements-py-multiband_photometry.txt
uv cache clean