#!/bin/bash

set -e
set -o pipefail

pythonenv=notebook
heasoft_version=6.34
install_dir=/opt/heasoft
caldb_dir=/opt/caldb

# option to compile only part of heasoft when testing
# set to "yes" to activate
fast="no"

export PYTHON=${CONDA_DIR}/envs/${pythonenv}/bin/python
heasoft_tarfile_suffix=src_no_xspec_modeldata
echo "  --- Downloading heasoft ---"
wget -q https://heasarc.gsfc.nasa.gov/FTP/software/lheasoft/lheasoft${heasoft_version}/heasoft-${heasoft_version}${heasoft_tarfile_suffix}.tar.gz
tar xzf heasoft-${heasoft_version}${heasoft_tarfile_suffix}.tar.gz > tar.log.txt
rm -f heasoft-${heasoft_version}${heasoft_tarfile_suffix}.tar.gz
cd heasoft-${heasoft_version}

if [ $fast == "yes" ]; then
  rm -r demo integral nicer suzaku Xspec calet heagen heasim hitomixrism ixpe maxi nustar swift
  rm -r attitude ftools heasptools heatools tcltk
fi

# ----------------------- #
# Handle large refdata that we don't want in the image
# we add them later
refdata=(
  "ftools/xstar/data/atdb.fits"
  "heasim/skyback/torus1006.fits"
)
# remove refdata from the image
for file in "${refdata[@]}"; do
  rm -f $file
done
# ----------------------- #

## Configure, make, and install ...
echo "  --- Configure heasoft ---"
cd BUILD_DIR/
# write stdout to a file (can be long), and leave stderr on screen
./configure --prefix=$install_dir --enable-collapse > config.log.txt

echo "  --- Build heasoft ---"
make > build.log.txt
make install > install.log.txt
make clean > clean.log.txt
gzip -9 *.log.txt && mv *.log.txt.gz $install_dir
cd ..
if [ ! $fast == "yes" ]; then
  cp -p Xspec/BUILD_DIR/hmakerc $install_dir/x86_64*/bin/
  cp -p Xspec/BUILD_DIR/Makefile-std $install_dir/x86_64*/bin/
fi
mv Release_Notes* $install_dir
cd .. && rm -rf heasoft-${heasoft_version}

# Tweak Xspec settings for a no-X11 environment
if [ ! $fast == "yes" ]; then
  printf "setplot splashpage off\ncpd /GIF\n" >> $install_dir/spectral/scripts/global_customize.tcl
fi

# enable remote CALDB for now.
export CALDBCONFIG=$caldb_dir/caldb.config
export CALDBALIAS=$caldb_dir/alias_config.fits 
export CALDB=/home/jovyan/efs/caldb
mkdir -p $caldb_dir
cd $caldb_dir
wget -q https://heasarc.gsfc.nasa.gov/FTP/caldb/software/tools/caldb.config
wget -q https://heasarc.gsfc.nasa.gov/FTP/caldb/software/tools/alias_config.fits

# setup scripts so it runs when (heasoft) is activated
HEADAS=`ls -d $install_dir/x86_64*`
CALDB=https://heasarc.gsfc.nasa.gov/FTP/caldb

# bash init script
cat <<EOF > activate_heasoft.sh
export HEADAS=$HEADAS
export CALDB=$CALDB
source \$HEADAS/headas-init.sh
if [ -z \$CALDB ] ; then
    echo "** No CALDB data. **"
elif [[ \$CALDB == http* ]]; then
   echo "** Using Remote CALDB **" 
elif [ -d \$CALDB ]; then
  echo "** Using CALDB in \$CALDB **" 
  source \$CALDB/software/tools/caldbinit.sh
else
  echo "** No CALDB data. **"
fi
EOF

_activatedir=$CONDA_DIR/envs/${pythonenv}/etc/conda/activate.d/
mkdir -p $_activatedir
mv activate_heasoft.sh $_activatedir


# ----------------------- #
# write a script to download the refdata
cat <<EOF > $HEADAS/bin/download-refdata.sh
#!/usr/bin/env bash

if test -z \$HEADAS; then
  echo "\$HEADAS is not defined. Make sure heasoft is installed"
else
  cd \$HEADAS/refdata
  for file in ${refdata[@]}; do
    if ! test -f \$(basename \$file); then
      echo "downloading \$file ..."
      wget -q https://heasarc.gsfc.nasa.gov/FTP/software/lheasoft/lheasoft${heasoft_version}/heasoft-${heasoft_version}/\$file
    fi
  done
fi
EOF
chmod +x $HEADAS/bin/download-refdata.sh