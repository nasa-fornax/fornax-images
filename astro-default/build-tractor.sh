#!/bin/bash
set -e 
set -o pipefail

pythonenv=notebook
astrometry_commit=1b7d716
tractor_commit=8059ae0

# Install astrometry.net and tractor
cd /tmp
git clone https://github.com/dstndstn/astrometry.net.git
cd astrometry.net
git config --global --add safe.directory $PWD
git checkout $astrometry_commit
mamba run -n $pythonenv make
mamba run -n $pythonenv make py
mamba run -n $pythonenv make extra
mamba run -n $pythonenv make install INSTALL_DIR=${CONDA_DIR}/envs/${pythonenv}
mv ${CONDA_DIR}/envs/$pythonenv/lib/python/astrometry \
   ${CONDA_DIR}/envs/$pythonenv/lib/python3.??/

cd /tmp
git clone https://github.com/dstndstn/tractor.git
cd tractor
git checkout $tractor_commit
conda run -n $pythonenv python setup.py build_ext --inplace --with-cython
conda run -n $pythonenv pip install --no-cache-dir . --target ${CONDA_DIR}/envs/$pythonenv/lib/python3.??/
cd $HOME
rm -rf /tmp/astrometry.net /tmp/tractor
