# #!/bin/bash
# # Build astronomy.net and tractor

# set -e 
# set -o pipefail

# pythonenv=py-multiband_photometry
# astrometry_commit=1b7d716
# tractor_commit=8059ae0

# mamba install cython
# mamba clean -yaf

# # Install astrometry.net and tractor
# cd /tmp
# git clone https://github.com/dstndstn/astrometry.net.git
# cd astrometry.net
# git config --global --add safe.directory $PWD
# git checkout $astrometry_commit
# make
# make py
# make extra
# make install INSTALL_DIR=${ENV_DIR}/${pythonenv}
# mv ${ENV_DIR}/${pythonenv}/lib/python/astrometry \
#    ${ENV_DIR}/${pythonenv}/lib/python3.??/

# cd /tmp
# git clone https://github.com/dstndstn/tractor.git
# cd tractor
# git checkout $tractor_commit
# python setup.py build_ext --inplace --with-cython
# pip install --no-cache-dir . --target ${ENV_DIR}/${pythonenv}/lib/python3.??/
# cd $HOME
# rm -rf /tmp/astrometry.net /tmp/tractor
