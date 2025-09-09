#!/usr/bin/bash

# Build script to setup a conda environment for eROSITA's eSASS toolkit

########### Validation and setup of directories ###########
# Location of support data
if [ -z $SUPPORT_DATA_DIR ]; then
    echo "ERROR: SUPPORT_DATA_DIR not defined"
    exit 1
fi

# Sets up the working directory where SAS will assembled
WORKDIR=/tmp/esass
mkdir -p $WORKDIR
# Deletes any existing contents of the working directory
rm -rf $WORKDIR/*
#> /dev/null 2>&1

# Make sure to setup a support file directory for some makefiles we want to copy in
mkdir -p $WORKDIR/support_files

# Moves the supporting files we need to make automating the installation of eSASS easier
mv requirements-esassdr1-healpix.pc $WORKDIR/support_files/healpix.pc
mv requirements-esassdr1-healpix-Makefile $WORKDIR/support_files/Makefile

# Moves us to the working directory
cd $WORKDIR
###########################################################


############# Definition of software versions #############
esass_version=1.0.1
py_version=$PYTHON_VERSION
###########################################################


############### Setting up useful variables ###############
# This is where we will be putting the eROSITA DR1 calibration files
export eSASS_CALDB=$SUPPORT_DATA_DIR/erosita_caldb4DR1/
###########################################################


#################### DOWNLOADING eSASS ####################
# TODO Ask about mirroring the software - would be nice to have it on HEASARC and control the file name
# For now we are going to have to download from a URL whose naming scheme may not be consistent
esass_link=https://erosita.mpe.mpg.de/dr1/eSASS4DR1/eSASS4DR1_installation/eSASS4DR${esass_version}.tgz

# Split the URL and get the name of the file programmatically
esass_file="${esass_link##*/}"

# And then split the file name into the directory name when unpacked
esass_dir_name="${esass_file%%.*}"
###########################################################


########### Download and unpack required files ############
wget $esass_link \
	&& tar zxf $esass_file \
	&& rm -f $esass_file
###########################################################


############ Setup the eSASS Conda environment ############
# Creates a Conda definition file that can be used to setup the environment that eSASS
#  will be associated with
cat <<EOF > conda-esassdr1.yml
name: esassdr1
channels:
  - conda-forge
dependencies:
  - python=$py_version
  - pytest
  - fftw
EOF

# Use the yml to create the eSASS env
bash /usr/local/bin/conda-env-install.sh

# Updating the lock file and moving it to the lock file directory
micromamba env -n esassdr1 export > $ENV_DIR/esassdr1/esassdr1-lock.yml
cp $ENV_DIR/esassdr1/esassdr1-lock.yml $LOCK_DIR

# THOUGH WE'VE CREATED AN ENVIRONMENT FOR eSASS WE AREN'T GOING TO USE IT YET - instead we'll keep using the
#  heasoft environment, because it is easier to complete the build there then get the esassdr1 environment
#  set up to do it
# These dependencies are needed to build eSASS, and are temporarily installed in the HEASoft environment
export conda_extra="gcc gfortran gxx binutils automake fftw libtool make"
micromamba install -y -n heasoft $conda_extra
###########################################################


############### Build HEALPix v3.50 for eSASS ##############
# FIRST WE MUST TRICK eSASS' HEALPIX INTO ACCEPTING A SHARED CFITSIO LIBRARY
if [ ! -L /opt/envs/heasoft/heasoft/lib/libcfitsio.a ]; then
  ln -s /opt/envs/heasoft/heasoft/lib/libcfitsio.so /opt/envs/heasoft/heasoft/lib/libcfitsio.a
fi

# The HEALPix source (and eventual build) lives in this directory
healpix_dir=$WORKDIR/$esass_dir_name/external/Healpix_3.50
cd $healpix_dir

mv $WORKDIR/support_files/Makefile $healpix_dir/

mkdir -p lib
mkdir -p bin
mkdir -p include
mkdir -p build

mv $WORKDIR/support_files/healpix.pc $healpix_dir/lib/

micromamba run -n heasoft make
###########################################################


################### Setup to build eSASS ##################
cd $WORKDIR/$esass_dir_name/eSASS/autoconf

export CC=$ENV_DIR/heasoft/bin/gcc
export CXX=$ENV_DIR/heasoft/bin/g++
export FC=$ENV_DIR/heasoft/bin/gfortran
export F77=$ENV_DIR/heasoft/bin/gfortran
###########################################################


################# Build eSASS from source #################
micromamba run -n heasoft aclocal
micromamba run -n heasoft autoreconf -fi -v
micromamba run -n heasoft ./configure --with-caldb=$eSASS_CALDB --with-healpix=$healpix_dir \
                                      --with-headas=$HEADAS --with-gsl=compile --with-lapack=system

micromamba run -n heasoft make
micromamba run -n heasoft make install
micromamba run -n heasoft make clean
###########################################################


################ Move eSASS to environment ################
cd $WORKDIR
mv $esass_dir_name $ENV_DIR/esassdr1

# Make a variable with the final installation path of eSASS
export esass_final_path=$ENV_DIR/esassdr1/$esass_dir_name/eSASS
###########################################################


############# Add conda (de)activation scripts ############
# Ensure that the directories we need actually exist
mkdir -p $ENV_DIR/esassdr1/etc/conda/activate.d
mkdir -p $ENV_DIR/esassdr1/etc/conda/deactivate.d

# These scripts set up SAS and handles additional environment variable setting
cat <<EOF > $ENV_DIR/esassdr1/etc/conda/activate.d/esassdr1-general_activate.sh
#!/usr/bin/bash

export ESASS_PREV_PATH=\$PATH
export ESASS_PREV_PFILES=\$PFILES

# Setting up HEASoft, some parts of eSASS require it
export HEADAS=\$ENV_DIR/heasoft/heasoft
source \$HEADAS/headas-init.sh

# Call the setup script for eSASS
source \$ENV_DIR/esassdr1/$esass_dir_name/eSASS/bin/esass-init.sh

# And we make sure the library path has every entry that it needs
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/opt/envs/heasoft/heasoft/lib:/opt/envs/heasoft/lib:/opt/envs/esassdr1/lib:\
                        /opt/envs/esassdr1/eSASS4DR1/external/Healpix_3.50/lib"

EOF

######
# This scripts unsets many of the environment variables set in the activation scripts
cat <<EOF > $ENV_DIR/esassdr1/etc/conda/deactivate.d/esassdr1-general_deactivate.sh
#!/usr/bin/bash

unset SASS_BIN_ROOT
unset SASS_SETUP
unset SASS_ROOT
unset E_ROOT
unset CALDB
unset CALDBCONFIG
unset SASS_TEMPLATES
unset E_MOD
unset E_LIB
unset SASS_CALVERS
unset SASS_DIR

export PFILES=\$ESASS_PREV_PFILES
unset ESASS_PREV_PFILES
export PATH=\$ESASS_PREV_PATH
unset ESASS_PREV_PATH

EOF
###########################################################


####################### Final clean up #####################
cd $HOME
rm -rf $WORKDIR

# Remove the extra conda libraries we installed
micromamba remove -y -n heasoft $conda_extra
# Unset the environment variables used by the eSASS build
unset CC
unset CXX
unset FC
unset F77
############################################################