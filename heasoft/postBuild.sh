#!/bin/bash

pythonenv=heasoft
heasoft_version=6.33.1

export PYTHON=${CONDA_DIR}/envs/${pythonenv}/bin/python
heasoft_tarfile_suffix=src_no_xspec_modeldata
echo "  --- Downloading heasoft ---"
wget https://heasarc.gsfc.nasa.gov/FTP/software/lheasoft/lheasoft${heasoft_version}/heasoft-${heasoft_version}${heasoft_tarfile_suffix}.tar.gz
tar xzvf heasoft-${heasoft_version}${heasoft_tarfile_suffix}.tar.gz
rm -f heasoft-${heasoft_version}${heasoft_tarfile_suffix}.tar.gz
cd heasoft-${heasoft_version}


## Configure, make, and install ...
echo "  --- Configure heasoft ---"
cd BUILD_DIR/
./configure --prefix=/opt/heasoft 2>&1 | tee config.log.txt

echo "  --- Build heasoft ---"
make 2>&1 | tee build.log.txt
make install 2>&1 | tee install.log.txt
make clean 2>&1
gzip -9 *.log.txt && mv *.log.txt.gz /opt/heasoft
cd ..
cp -p Xspec/BUILD_DIR/hmakerc /opt/heasoft/x86_64*/bin/
cp -p Xspec/BUILD_DIR/Makefile-std /opt/heasoft/x86_64*/bin/
mv Release_Notes* /opt/heasoft/
cd heasoft-${heasoft_version}

# Tweak Xspec settings for a no-X11 environment
printf "setplot splashpage off\ncpd /GIF\n" >> /opt/heasoft/spectral/scripts/global_customize.tcl

# enable remote CALDB for now.
export CALDBCONFIG=/opt/caldb/caldb.config
export CALDBALIAS=/opt/caldb/alias_config.fits 
export CALDB=/home/jovyan/efs/caldb
mkdir -p /opt/caldb/
cd /opt/caldb
wget -q https://heasarc.gsfc.nasa.gov/FTP/caldb/software/tools/caldb.config
wget -q https://heasarc.gsfc.nasa.gov/FTP/caldb/software/tools/alias_config.fits

# setup scripts so it runs when (heasoft) is activated
HEADAS=`ls -d /opt/heasoft/x86_64*`
CALDB=https://heasarc.gsfc.nasa.gov/FTP/caldb

# bash
echo "
export HEADAS=$HEADAS
export CALDB=$CALDB
source \$HEADAS/headas-init.sh
if [ -z \$CALDB ] ; then
    printf \"\\\n** No CALDB data. **\\\n\"
elif [[ \$CALDB == http* ]]; then
   printf \"\\\n** Using Remote CALDB **\\\n\" 
elif [ -d \$CALDB ]; then
  printf \"\\\n** Using CALDB in \$CALDB **\\\n\" 
  source \$CALDB/software/tools/caldbinit.sh
else
  printf \"\\\n** No CALDB data. **\\\n\"
fi
" > activate_heasoft.sh

_activatedir=$CONDA_DIR/envs/heasoft/etc/conda/activate.d/
mkdir -p $_activatedir
mv activate_heasoft.sh $_activatedir

