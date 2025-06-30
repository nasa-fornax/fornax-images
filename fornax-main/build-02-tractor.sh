#!/bin/bash
# Build astronomy.net and tractor

set -e 
set -o pipefail


pythonenv=py-multiband_photometry
astrometry_commit=1b7d716
tractor_commit=8059ae0

# build in the main conda env, then install in the relevant one
mamba install -y cython
# update the lockfile
mamba env export > /opt/conda/base-lock.yml
mamba clean -yaf

# Install astrometry.net and tractor
cd /tmp
git clone https://github.com/dstndstn/astrometry.net.git
cd astrometry.net
git config --global --add safe.directory $PWD
git checkout $astrometry_commit
make
make py
make extra
make install INSTALL_DIR=${ENV_DIR}/${pythonenv}
mv ${ENV_DIR}/${pythonenv}/lib/python/astrometry \
   ${ENV_DIR}/${pythonenv}/lib/python3.??/site-packages/

cd /tmp
git clone https://github.com/dstndstn/tractor.git
cd tractor
git checkout $tractor_commit
python setup.py build_ext --inplace --with-cython
pip install --no-cache-dir . --target ${ENV_DIR}/${pythonenv}/lib/python3.??/site-packages/
cd $HOME
rm -rf /tmp/astrometry.net /tmp/tractor

# update the freeze file
export VIRTUAL_ENV=$ENV_DIR/$pythonenv
uv pip freeze > $ENV_DIR/$pythonenv/requirements-py-multiband_photometry.txt
