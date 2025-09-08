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
cd $WORKDIR

# Deletes any existing contents of the working directory
#rm -rf * > /dev/null 2>&1
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
#wget $esass_link \
#	&& tar zxf $esass_file \
#	&& rm -f $esass_file
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
  - gcc
  - gfortran
  - gxx
  - binutils
  - automake
  - fftw
  - libtool
  - make
EOF

# Use the yml to create the eSASS env
#bash /usr/local/bin/conda-env-install.sh

micromamba install -y gcc gfortran gxx binutils automake fftw libtool make libcurl

# We need all those dependencies included in the repo in order to build eSASS, and
#  it will get tedious running everything via 'micromamba run -n esass-dr1', so
#  we'll just activate the environment here
#micromamba activate esassdr1

# Activate HEASOFT, as we'll need it for building eSASS
#export HEADAS=$ENV_DIR/heasoft/heasoft
#source $HEADAS/headas-init.sh
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

cat <<EOF > Makefile
# input Makefile
# DO NOT EDIT!
# Run ./configure to produce the Makefile instead.

# ------------------------------ global variables --------------------------

ALL       = c-void cpp-void f90-all healpy-void
TESTS     = c-void cpp-void f90-test healpy-void
CLEAN     = c-void cpp-void f90-clean healpy-void
TIDY      = c-void cpp-void f90-tidy healpy-void
DISTCLEAN = c-void cpp-void f90-distclean healpy-void

RM	= rm -f

# ------------------------------ variables for F90 --------------------------
HEALPIX	= /tmp/esass/eSASS4DR1/external/Healpix_3.50
F90_BINDIR	= /tmp/esass/eSASS4DR1/external/Healpix_3.50/bin
F90_INCDIR	= /tmp/esass/eSASS4DR1/external/Healpix_3.50/include
F90_LIBDIR	= /tmp/esass/eSASS4DR1/external/Healpix_3.50/lib
FITSDIR	= /opt/envs/heasoft/heasoft/lib
LIBFITS	= cfitsio
F90_BUILDDIR	= /tmp/esass/eSASS4DR1/external/Healpix_3.50/build

F90_FFTSRC	= healpix_fft
F90_ADDUS	=

F90_PARALL  =

F90_FC	= gfortran
F90_FFLAGS	= -O3 -I$(F90_INCDIR) -DGFORTRAN -fno-second-underscore -fPIC
F90_CC	= gcc
F90_CFLAGS	= -O3 -std=c99 -DgFortran -fPIC
F90_LDFLAGS	= -L$(F90_LIBDIR) -L$(FITSDIR) -lhealpix -lhpxgif -l$(LIBFITS) -Wl,-R$(FITSDIR)
F90_AR        = gfortran -fPIC -shared -o
F90_PPFLAGS	=
F90_I8FLAG  = -fdefault-integer-8
F90_LIBSUFFIX = .so
F90_FLAGNAMELIB = -Wl,-soname,

F90_PGFLAG  =
F90_PGLIBS  =

F90_MOD	= mod
F90_MODDIR	= "-J"

F90_OS	= Linux

F90_MKFLAGS	= FC="$(F90_FC)" FFLAGS="$(F90_FFLAGS)" LDFLAGS="$(F90_LDFLAGS)" \
	CC="$(F90_CC)" CFLAGS="$(F90_CFLAGS)" MOD="$(F90_MOD)" MODDIR=$(F90_MODDIR) \
	OS="$(F90_OS)" HEALPIX=$(HEALPIX) LIBSUFFIX="$(F90_LIBSUFFIX)"\
	LIBDIR=$(F90_LIBDIR) INCDIR=$(F90_INCDIR) BINDIR=$(F90_BINDIR) BUILDDIR=$(F90_BUILDDIR) \
	FFTSRC=$(F90_FFTSRC) ADDUS="$(F90_ADDUS)" PARALL="$(F90_PARALL)" AR="$(F90_AR)" FLAGNAMELIB="$(F90_FLAGNAMELIB)"\
	PPFLAGS="$(F90_PPFLAGS)" PGFLAG="$(F90_PGFLAG)" PGLIBS="$(F90_PGLIBS)" FI8FLAG="$(F90_I8FLAG)"


# ------------------------------ variables for C --------------------------
#
# Compiler Options
C_CC  =
C_PIC =
C_OPT =
#
# Where you want to install the library and header file
C_LIBDIR =
C_INCDIR =
C_AR     =
#
# Where you have the cfitsio installation
C_WITHOUT_CFITSIO =
C_CFITSIO_INCDIR =
C_CFITSIO_LIBDIR =
C_WLRPATH =
C_EXTRA_LIB =
#
# Libraries to install (static, shared, dynamic)
C_ALL =

C_MKFLAGS = CC="$(C_CC)" PIC="$(C_PIC)" OPT="$(C_OPT)" \
	LIBDIR="$(C_LIBDIR)" INCDIR="$(C_INCDIR)" AR="$(C_AR)" \
	WITHOUT_CFITSIO="$(C_WITHOUT_CFITSIO)" CFITSIO_INCDIR="$(C_CFITSIO_INCDIR)" \
	CFITSIO_LIBDIR="$(C_CFITSIO_LIBDIR)" WLRPATH="$(C_WLRPATH)" \
	EXTRA_LIB="$(C_EXTRA_LIB)" \
	RM="$(RM)"

# ------------------------------ variables for C++ --------------------------

HEALPIX_TARGET =
EXTERNAL_CFITSIO=yes
CFITSIO_EXT_LIB=
CFITSIO_EXT_INC=
export HEALPIX_TARGET EXTERNAL_CFITSIO CFITSIO_EXT_LIB CFITSIO_EXT_INC

# ------------------------------ variables for Python healpy --------------------------

HPY_SETUP  =
HPY_PYTHON =
# ------------------------------- global rules -------------------------

all: $(ALL)


test: $(TESTS)


clean: $(CLEAN)


tidy: $(TIDY)


distclean: $(DISTCLEAN)
	$(RM) Makefile
	$(RM) Makefile_tmp
	$(RM) Makefile_bk*

# ------------------------------- F90 rules ----------------------------


f90-progs = map2gif anafast smoothing synfast ud_grade hotspot plmgen alteralm median_filter ngsims_full_sky process_mask
f90-libs  = f90-libsharp f90-modules f90-libgif

f90-all: $(f90-libs) $(f90-progs)

# itemized list instead of loop to allow parallel compiling

# libraries
f90-libsharp:
	@cd src/f90/sharp; $(MAKE) $(F90_MKFLAGS)

f90-modules: f90-libsharp
	@cd src/f90/mod; $(MAKE) $(F90_MKFLAGS)

f90-libgif: f90-modules
	@cd src/f90/lib; $(MAKE) $(F90_MKFLAGS)

# visualization code
map2gif: $(f90-libs)
	@cd src/f90/$@; $(MAKE) $(F90_MKFLAGS)

# processing codes
anafast: $(f90-libs)
	@cd src/f90/$@; $(MAKE) $(F90_MKFLAGS)

smoothing: $(f90-libs)
	@cd src/f90/$@; $(MAKE) $(F90_MKFLAGS)

synfast: $(f90-libs)
	@cd src/f90/$@; $(MAKE) $(F90_MKFLAGS)

ud_grade: $(f90-libs)
	@cd src/f90/$@; $(MAKE) $(F90_MKFLAGS)

hotspot: $(f90-libs)
	@cd src/f90/$@; $(MAKE) $(F90_MKFLAGS)

plmgen: $(f90-libs)
	@cd src/f90/$@; $(MAKE) $(F90_MKFLAGS)

alteralm: $(f90-libs)
	@cd src/f90/$@; $(MAKE) $(F90_MKFLAGS)

median_filter: $(f90-libs)
	@cd src/f90/$@; $(MAKE) $(F90_MKFLAGS)

ngsims_full_sky: $(f90-libs)
	@cd src/f90/$@; $(MAKE) $(F90_MKFLAGS)

process_mask: $(f90-libs)
	@cd src/f90/$@; $(MAKE) $(F90_MKFLAGS)

f90-test: f90-all
	@cd test; \
	$(RM) test*; \
	$(F90_BINDIR)/synfast syn.par; \
	$(F90_BINDIR)/map2gif -inp test_map.fits -out test_map.gif -bar t -ttl 'CMB Map'; \
	$(F90_BINDIR)/smoothing smo.par; \
	$(F90_BINDIR)/map2gif -inp test_sm.fits -out test_sm.gif -bar t -ttl 'Smoothed CMB Map'; \
	$(F90_BINDIR)/ud_grade udg.par ; \
	$(F90_BINDIR)/map2gif -inp test_LOres.fits -out test_LOres.gif -bar t -ttl 'Degraded Map'; \
	$(F90_BINDIR)/hotspot hot.par ; \
	$(F90_BINDIR)/map2gif -inp test_ext.fits -out test_ext.gif -bar t -ttl 'Extrema Only Map'; \
	$(F90_BINDIR)/anafast ana.par; \
        $(F90_BINDIR)/anafast ana2maps.par ; \
        $(F90_BINDIR)/anafast ana_w2.par ; \
	$(F90_BINDIR)/alteralm alt.par; \
	$(F90_BINDIR)/median_filter med.par ; \
	$(F90_BINDIR)/map2gif -inp test_mf.fits -out test_mf.gif -bar t -ttl 'Median Filtered Map'; \
	$(F90_BINDIR)/sky_ng_sim ngfs.par ; \
	$(F90_BINDIR)/map2gif -inp test_ngfs.fits -out test_ngfs.gif -bar t -ttl 'Non-Gaussian Map'; \
	$(F90_BINDIR)/process_mask prmask.par ; \
	$(F90_BINDIR)/map2gif -inp test_distmask.fits -out test_distmask.gif -bar t -ttl 'Distance to mask border'; \
	echo "Healpix F90 tests done" ; \
	echo "success rate: `ls -1 test*fits | wc -l`/12"

f90-clean:
	for p in $(f90-progs) lib mod sharp; do \
	$(RM) src/f90/$$p/*.o src/f90/$$p/*.$(F90_MOD) src/f90/$$p/lib*.a src/f90/$$p/*.pc src/f90/$$p/*.pcl src/f90/$$p/*.il ; \
	done
	$(RM) -r $(F90_BUILDDIR)

f90-vclean: f90-clean
	for p in $(f90-progs); do \
	$(RM) $(F90_BINDIR)/$$p; \
	done
	$(RM) $(F90_BINDIR)/sky_ng_sim*
	$(RM) $(F90_INCDIR)/*.$(F90_MOD)
	$(RM) $(F90_INCDIR)/*.pc $(F90_INCDIR)/*.pcl
	$(RM) $(F90_LIBDIR)/*.a $(F90_LIBDIR)/*$(F90_LIBSUFFIX) $(F90_LIBDIR)/*.pc

f90-tidy: f90-vclean
	$(RM) Makefile.bak test/test*

f90-distclean: f90-tidy
	$(RM) Makefile
	$(RM) -r $(F90_BINDIR) $(F90_INCDIR) $(F90_LIBDIR)

f90-void:

# ------------------------------- C rules ----------------------------

c-all: $(C_ALL)


c-static:      # all flavors
	@cd src/C/subs; \
	$(MAKE) static  $(C_MKFLAGS)  ; \
	$(MAKE) install $(C_MKFLAGS)  ; \
	cd ../../..

c-dynamic:     # Mac OS only
	@cd src/C/subs; \
	$(MAKE) dynamic $(C_MKFLAGS) PIC="$(C_PIC)" ; \
	$(MAKE) install $(C_MKFLAGS) PIC="$(C_PIC)" ; \
	cd ../../..

c-shared:      # Other Unix/Linux
	@cd src/C/subs; \
	$(MAKE) shared  $(C_MKFLAGS) PIC="$(C_PIC)" ; \
	$(MAKE) install $(C_MKFLAGS) PIC="$(C_PIC)" ; \
	cd ../../..

c-test:    # will only test *static* library
	@cd src/C/subs; \
	$(MAKE) static  $(C_MKFLAGS)  ; \
	$(MAKE) tests   $(C_MKFLAGS)  ; \
	cd ../../..

c-clean:
	@cd src/C/subs; \
	$(MAKE) clean $(C_MKFLAGS); \
	cd ../../..

c-tidy:
	@cd src/C/subs; \
	$(MAKE) tidy $(C_MKFLAGS); \
	cd ../../..

c-distclean:
	@cd src/C/subs; \
	$(MAKE) distclean $(C_MKFLAGS); \
	cd ../../..

c-void:

# ------------------------------- C++ rules ----------------------------

cpp-all:
	@cd src/cxx; \
	$(MAKE) ; \
	cd ../..

cpp-test: cpp-all
	@cd src/cxx;   \
	$(MAKE) test ; \
	cd ../..

cpp-clean:
	@cd src/cxx ; \
	$(MAKE) distclean; \
	cd ../..

cpp-tidy:
	@cd src/cxx ; \
	$(MAKE) distclean ; \
	cd ../..

cpp-distclean: cpp-tidy

cpp-void:

# ------------------------------- healpy rules ----------------------------

healpy-all:
	@cd src/healpy; \
	$(HPY_PYTHON) $(HPY_SETUP) build ; \
	$(HPY_PYTHON) $(HPY_SETUP) install --user --prefix=; \
	cd ../..

healpy-test: healpy-all
	@cd /tmp ; \
	$(HPY_PYTHON) -c "import pylab; import healpy; import numpy ; hpv=healpy.__version__ ; print ('\n\n Welcome to Healpy %s! \n\n'%(hpv)); healpy.mollview(numpy.arange(12),title='Healpy %s'%(hpv)); pylab.show()" ; \
	cd $(HEALPIX)

healpy-clean:
	@cd src/healpy ; \
	$(HPY_PYTHON) $(HPY_SETUP) clean --all ; \
	cd ../..

healpy-tidy: healpy-clean

healpy-distclean: healpy-tidy

healpy-void:
EOF

mkdir -p lib
mkdir -p bin
mkdir -p include
mkdir -p build

cat <<EOF > lib/healpix.pc
# HEALPix/F90 pkg-config file
# compiled with gfortran

prefix=/tmp/esass/eSASS4DR1/external/Healpix_3.50
suffix=
exec_prefix=${prefix}/bin${suffix}
libdir=${prefix}/lib${suffix}
includedir=${prefix}/include${suffix}

Name: HEALPix
Description: F90 library for HEALPix (Hierarchical Equal-Area iso-Latitude) pixelisation of the sphere
Version: 3_50
URL: https://healpix.sourceforge.io
Requires: cfitsio >= 3.20
Libs: -L${libdir} -lhealpix -lhpxgif
Cflags: -I${includedir} -fopenmp -fPIC
EOF

make
###########################################################


#################### Setup to build eSASS ##################
#cd $WORKDIR/$esass_dir_name/eSASS/autoconf
#
#export CC=/opt/envs/heasoft/bin/gcc
#export CXX=/opt/envs/heasoft/bin/g++
#export FC=/opt/envs/heasoft/bin/gfortran
#export F77=/opt/envs/heasoft/bin/gfortran
############################################################
#
#
################## Build eSASS from source #################
#aclocal
#autoreconf -fi -v
#./configure --with-caldb=$eSASS_CALDB --with-healpix=$healpix_dir \
#   --with-headas=$HEADAS --with-gsl=compile --with-lapack=system
#
#make
#make install
#make clean
############################################################


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