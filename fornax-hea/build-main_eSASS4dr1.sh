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
rm -rf /tmp/esass/* > /dev/null 2>&1

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
EOF

# Use the yml to create the eSASS env
bash /usr/local/bin/conda-env-install.sh

# THOUGH WE'VE CREATED AN ENVIRONMENT FOR eSASS WE AREN'T GOING TO USE IT YET - instead we'll keep using the
#  heasoft environment, because it is easier to complete the build there then get the esassdr1 environment
#  set up to do it
# These dependencies are needed to build eSASS, and are temporarily installed in the HEASoft environment
micromamba install -y gcc gfortran gxx binutils automake fftw libtool make libcurl
###########################################################


############### Build HEALPix v3.50 for eSASS ##############
# FIRST WE MUST TRICK eSASS' HEALPIX INTO ACCEPTING A SHARED CFITSIO LIBRARY
if [ ! -L /opt/envs/heasoft/heasoft/lib/libcfitsio.a ]; then
  ln -s /opt/envs/heasoft/heasoft/lib/libcfitsio.so /opt/envs/heasoft/heasoft/lib/libcfitsio.a
fi

# The HEALPix source (and eventual build) lives in this directory
healpix_dir=$WORKDIR/$esass_dir_name/external/Healpix_3.50
echo $healpix_dir
cd $healpix_dir

mv $WORKDIR/support_files/Makefile $healpix_dir/

mkdir -p lib
mkdir -p bin
mkdir -p include
mkdir -p build

mv $WORKDIR/support_files/healpix.pc $healpix_dir/lib/

make
###########################################################


################### Setup to build eSASS ##################
cd $WORKDIR/$esass_dir_name/eSASS/autoconf

export CC=/opt/envs/heasoft/bin/gcc
export CXX=/opt/envs/heasoft/bin/g++
export FC=/opt/envs/heasoft/bin/gfortran
export F77=/opt/envs/heasoft/bin/gfortran
###########################################################


################# Build eSASS from source #################
aclocal
autoreconf -fi -v
./configure --with-caldb=$eSASS_CALDB --with-healpix=$healpix_dir \
   --with-headas=$HEADAS --with-gsl=compile --with-lapack=system

make
make install
make clean
###########################################################


############## Add conda (de)activation scripts ############
## Ensure that the directories we need actually exist
#mkdir -p $ENV_DIR/sas/etc/conda/activate.d
#mkdir -p $ENV_DIR/sas/etc/conda/deactivate.d
#
## These scripts set up SAS and handles additional environment variable setting
#cat <<EOF > $ENV_DIR/sas/etc/conda/activate.d/sas-general_activate.sh
##!/usr/bin/bash
#
## SAS can be very particular about Perl - this is the path we set when SAS was 'built'
#export SAS_PERL=$SAS_PERL
## And this is the conda environment we set up for it
#export SAS_PYTHON=$SAS_PYTHON
#
## Adds the SAS conda environment library to the library path - without this
##  we will get errors about not being able to find libsm.so.6
#export LD_LIBRARY_PATH="\$LD_LIBRARY_PATH:$ENV_DIR/sas/lib"
#
## Setting up HEASoft, otherwise SAS will fall over when you try to init it
#export HEADAS=\$ENV_DIR/heasoft/heasoft
#source \$HEADAS/headas-init.sh
#
## Any attempted init of SAS will fail without this path being set
#export SAS_DIR=\$ENV_DIR/sas/${sas_install_dir}
#source \$SAS_DIR/setsas.sh
#
## This sets the environment variable for the XMM Current Calibration Files (CCF)
#export SAS_CCFPATH=\$SUPPORT_DATA_DIR/xmm_ccf
#
#EOF
#
#######
## This scripts unsets many of the environment variables set in the activation scripts
## Honestly don't really know how much most of this matters, and am currently only getting the
##  environment variables that I know have been set, not those that the setsas.sh script sets
#cat <<EOF > $ENV_DIR/sas/etc/conda/deactivate.d/sas-general_deactivate.sh
##!/usr/bin/bash
#
#unset SAS_PERL
#unset SAS_PYTHON
#
## I _think_ this should be fine
#unset LD_LIBRARY_PATH
#
#unset SAS_DIR
#unset SAS_CCFPATH
#EOF
############################################################
############## Add conda (de)activation scripts ############
#
#
#
#
############# Moving unpacked SAS and installing ###########
## Moves all of the files unpacked from the SAS download into the conda environment directory
##  for SAS - it is easier to install SAS in-situ, rather than installing it then moving it, as
##  some file paths get baked in during the installation process
#mv * $ENV_DIR/sas/
## We must follow the unpacked files
#cd $ENV_DIR/sas/
#
## Run the SAS install script, specifically in the environment we've just created
#micromamba run -n sas ./install.sh
############################################################
#
####################### Final clean up #####################
## In the /opt/envs/sas directory, where we copied the unpacked contents of the SAS download
##  and installed them - time to clean up the left over files
#rm sas_python_packages.txt
#
#cd $HOME
#rm -rf $WORKDIR
############################################################