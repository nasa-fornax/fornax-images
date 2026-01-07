#!/bin/bash
# Build astronomy.net and tractor
# Assumes build-01-notebook-req.sh has been run

# exit on failure; error on undefiend vars; print commands
set -eux
set -o pipefail


pythonenv=py-multiband_photometry
astrometry_version=0.97
tractor_commit=8dc2bd8


source $ENV_DIR/$pythonenv/bin/activate
TARGET_DIR=`ls -d $ENV_DIR/$pythonenv/lib/python3.??/site-packages/`


# We need some packages
micromamba install -y -p $ENV_DIR/base \
   make gcc cairo expat netpbm libpng zlib swig cfitsio binutils pkg-config
uv pip install cython setuptools
export PKG_CONFIG_PATH=/opt/envs/base

# Install astrometry.net and tractor
cd /tmp
folder=astrometry.net-$astrometry_version
curl -SsLO https://github.com/dstndstn/astrometry.net/releases/download/0.97/$folder.tar.gz
tar -zxvf $folder.tar.gz && rm $folder.tar.gz
cd $folder
make
make py
make extra
make install INSTALL_DIR=${VIRTUAL_ENV}
mv $ENV_DIR/$pythonenv/lib/python/astrometry $TARGET_DIR

cd /tmp
git clone https://github.com/dstndstn/tractor.git
cd tractor
git checkout $tractor_commit
### -- patch import_array() -- ##
find "tractor" -type f -name "*.i" | while read -r file; do
    if grep -q 'import_array();' "$file"; then
        echo "Patching: $file"
        cp "$file" "$file.bak"
        # Replace the line safely using sed
        sed -i 's/import_array();/if (_import_array() < 0) return -1;/' "$file"
    fi
done
### -------------------------- ##
python setup.py build_ext --inplace --with-cython
uv pip install --no-cache . --no-build-isolation  --target ${TARGET_DIR}
cd $HOME
rm -rf $folder /tmp/tractor

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