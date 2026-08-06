#!/bin/bash
# Build astronomy.net and tractor
# Assumes build-01-notebook-req.sh has been run

# exit on failure; error on undefiend vars; print commands
set -eux
set -o pipefail


pythonenv=py-multiband_photometry
astrometry_version=0.97
tractor_commit=3fd2e80


source $ENV_DIR/$pythonenv/bin/activate
TARGET_DIR=`ls -d $ENV_DIR/$pythonenv/lib/python3.??/site-packages/`


# We need some packages; backup the environment;
cp -r $ENV_DIR/base $ENV_DIR/base.off
micromamba install -y -p $ENV_DIR/base \
   make gcc cairo expat netpbm libpng zlib swig cfitsio binutils pkg-config
uv pip install cython setuptools
export PKG_CONFIG_PATH=$ENV_DIR/base

# Install astrometry.net and tractor
cd /tmp
folder=astrometry.net-$astrometry_version
curl -SsLO https://github.com/dstndstn/astrometry.net/releases/download/0.97/$folder.tar.gz
tar -zxvf $folder.tar.gz && rm $folder.tar.gz
cd $folder
# cairo headers can be under cairo folder
export CFLAGS="-I$ENV_DIR/base/include/cairo"
make
make py
make extra
make install INSTALL_DIR=${VIRTUAL_ENV}
mv $ENV_DIR/$pythonenv/lib/python/astrometry $TARGET_DIR

cd /tmp
git clone https://github.com/dstndstn/tractor.git
cd tractor
git checkout $tractor_commit
### -- patch PyString_Check -> PyUnicode_Check and PyInt_Check -> PyLong_Check -- ##
grep -RIl --exclude-dir=.git --exclude=*.o --exclude=*.so -E 'PyString_Check|PyInt_Check' --include='*.c' --include='*.h' --include='*.cc' --include='*.cpp' . \
  | xargs -r sed -i \
    -e 's/\bPyString_Check\s*(/PyUnicode_Check(/g' \
    -e 's/\bPyInt_Check\s*(/PyLong_Check(/g'
### -------------------------- ##
python setup.py build_ext --inplace --with-cython
uv pip install --no-cache . --no-build-isolation  --target ${TARGET_DIR}
cd $HOME
rm -rf $folder /tmp/tractor

# clean up
uv pip uninstall cython setuptools
# restore the environment
rm -rf $ENV_DIR/base
mv $ENV_DIR/base.off $ENV_DIR/base

# update the freeze file
uv pip list --format=freeze > $VIRTUAL_ENV/requirements-py-multiband_photometry.txt

micromamba clean -yaf
uv cache clean
rm -rf /tmp/*