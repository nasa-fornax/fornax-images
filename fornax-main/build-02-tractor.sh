#!/bin/bash
# Build astronomy.net and tractor
# Assumes build-01-notebook-req.sh has been run

set -e 
set -o pipefail


pythonenv=py-multiband_photometry
astrometry_commit=1b7d716
tractor_commit=8059ae0


source $ENV_DIR/$pythonenv/bin/activate
TARGET_DIR=`ls -d $ENV_DIR/$pythonenv/lib/python3.??/site-packages/`


# We need some packages
micromamba install -y -p $ENV_DIR/base \
   make gcc cairo expat netpbm libpng zlib swig cfitsio binutils pkg-config
uv pip install cython setuptools
export PKG_CONFIG_PATH=/opt/envs/base

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
mv $ENV_DIR/$pythonenv/lib/python/astrometry $TARGET_DIR

cd /tmp
git clone https://github.com/dstndstn/tractor.git
cd tractor
git checkout $tractor_commit
python setup.py build_ext --inplace --with-cython
uv pip install --no-cache . --no-build-isolation  --target ${TARGET_DIR}
cd $HOME
rm -rf /tmp/astrometry.net /tmp/tractor

# clean up
uv pip uninstall cython setuptools
micromamba uninstall -y -p $ENV_DIR/base \
   make gcc binutils pkg-config expat swig netpbm libpng
# since we updated the base micromamba env, we need a new lock file
micromamba env export -p $ENV_DIR/base > $ENV_DIR/base/base-lock.yml
cp $ENV_DIR/base/base-lock.yml $LOCK_DIR/

# update the freeze file
uv pip list --format=freeze > $VIRTUAL_ENV/requirements-py-multiband_photometry.txt

micromamba clean -yaf
uv cache clean