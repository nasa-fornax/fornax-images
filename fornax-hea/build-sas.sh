#!/usr/bin/bash

# Build script to setup a conda environment for XMM's SAS toolkit - based on the 
#  build-ciao.sh script and the SciServer XMMSAS dockerfile 
#  (https://github.com/sciserver/sciserver-compute-images/blob/master/heasarc/xmmsas/Dockerfile)


########### Validation and setup of directories ###########
# Location of support data
if [ -z $SUPPORT_DATA_DIR ]; then
    echo "ERROR: SUPPORT_DATA_DIR not defined"
    exit 1
fi

# Sets up the working directory where SAS will assembled
WORKDIR=/tmp/sas
mkdir -p $WORKDIR
cd $WORKDIR

# Deletes any existing contents of the working directory
rm -rf * > /dev/null 2>&1
###########################################################


############# Definition of software versions #############
ubuntu_version=24.04
sas_version=22.1.0
py_version=3.12
###########################################################


############### Setting up useful variables ###############
# SAS gets upset if it can't find Perl - this will need to be included in an activate.d script
#  as well, to make sure this path is set when the user loads the environment in
export SAS_PERL=/usr/bin/perl
# We set this to point at the conda environment we're just about to produce - ENV_DIR is not
#  set in this script, but we can trust that it will be
export SAS_PYTHON=$ENV_DIR/sas/bin/python

# SAS will be downloaded from HEASARC - this is the base for the populated URL
base_sas_link=https://heasarc.gsfc.nasa.gov/FTP/xmm/software/sas/${sas_version}/Linux/Ubuntu${ubuntu_version}/

# This is the more general structure of the tar file name (see it in the HEASARC FTP for other versions
#  of SAS), but unfortunately there isn't a file with this easy to populate name structure for
#  the Ubuntu version (24.04) that I'm working with right now
# sas_file=sas_${sas_version}-Ubuntu${ubuntu_version}.tgz

# HARD CODED - this is the non-generalised file link to the tar of SAS I'm working with right now (22.1.0 for Ubuntu 24.04)
sas_file=sas_${sas_version}-a8f2c2afa-20250304-ubuntu${ubuntu_version}-gcc13.3.0-x86_64.tgz

# Assembling the download link
sas_link=$base_sas_link${sas_file}
###########################################################


############# NOTES #############
# Exact Perl version could be tricky - the SAS docs say 5.34.1, the Fornax
#  version currently is v5.38.2. The exact right version isn't available through conda 
#  as far as I can see. On the other hand, my local install of SAS has Perl v5.40.1
#  and it seems to work fine, so won't worry about this right now
#
# Could we include SAS in the https://heasarc.gsfc.nasa.gov/FTP/software/conda channel?
#################################



########### Download and unpack required files ############
wget $sas_link \
	&& tar xvf $sas_file \
	&& rm -f $sas_file 
###########################################################



############# Setup the SAS Conda environment #############
# Creates a Conda definition file that can be used to setup the environment that SAS 
#  will be associated with
# We use the Conda-hosted HEASoft to avoid downloading and building HEASoft manually
cat <<EOF > conda-sas.yml
name: sas
channels:
  - https://heasarc.gsfc.nasa.gov/FTP/software/conda
  - conda-forge
dependencies:
  - python=$py_version
  - heasoft=6.35.*
  - pytest
EOF

# Use the yml to create the SAS env
bash /usr/local/bin/conda-env-install.sh

# Use the Python requirements file included in the SAS directory to install
#  the module that it wants for some included Python bits (e.g. pySAS)
# Other build scripts for Fornax images seem to use the uv package manager, so we 
#  will as well - particularly the pip CLI version
micromamba run -n sas uv pip install -r sas_python_packages.txt

# Run the SAS install script, specifically in the environment we've just created
micromamba run -n sas ./install.sh
###########################################################


################ Add (de)activation scripts ###############
# This script sets up SAS and handles additional environment variable setting

cat <<EOF > $ENV_DIR/sas/etc/conda/activate.d/sas-general_activate.sh
#!/usr/bin/bash

# SAS can be very particular about Perl - this is the path we set when SAS was 'built'
export SAS_PERL=/usr/bin/perl
# And this is the conda environment we set up for it
export SAS_PYTHON=$ENV_DIR/sas/bin/python

# Adds the SAS conda environment library to the library path - without this
#  we will get errors about not being able to find libsm.so.6 
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$ENV_DIR/sas/lib"

# WILL HAVE TO CHANGE THIS WHEN I FIGURE OUT WHERE IT ACTUALLY LIVES
export SAS_DIR=/tmp/sas/xmmsas_22.1.0-a8f2c2afa-20250304
source $SAS_DIR/setsas.sh
EOF

###########################################################



###################### Final clean up #####################
cd $HOME
# rm -rf $WORKDIR
###########################################################




# ORPHANED CODE FROM THE DONOR CIAO SCRIPT



# delete the model data and caldb; create simlinks below
# rm -rf $ENV_DIR/ciao/spectral/modelData
# rm -rf $ENV_DIR/ciao/CALDB | true

# # Remove these files
# rm -rf $ENV_DIR/ciao/test
# rm -rf $ENV_DIR/ciao/docs

# Set SAS version
# SAS_VERSION=$(micromamba list ciao -p $ENV_DIR/ciao --json | jq -r '.[0].version')
## CALDB_VERSION=$(micromamba list caldb_main -p $ENV_DIR/ciao --json | jq -r '.[0].version')

# # link modelData
# ln -sf $SUPPORT_DATA_DIR/ciao-${CIAO_VERSION}/spectral/modelData $ENV_DIR/ciao/spectral/modelData
# # link caldb.
# ln -sf $SUPPORT_DATA_DIR/ciao-caldb-${CIAO_VERSION}/CALDB $ENV_DIR/ciao/CALDB

