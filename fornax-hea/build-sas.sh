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
py_version=$PYTHON_VERSION
###########################################################


############### Setting up useful variables ###############
# SAS gets upset if it can't find Perl - this will need to be included in an activate.d script
#  as well, to make sure this path is set when the user loads the environment in
export SAS_PERL=/usr/bin/perl
# We set this to point at the conda environment we're just about to produce - ENV_DIR is not
#  set in this script, but we can trust that it will be
export SAS_PYTHON=$ENV_DIR/sas/bin/python

# This is where we will be putting the calibration files for XMM
export SAS_CCFPATH=$SUPPORT_DATA_DIR/xmm_ccf/

##### DOWNLOADING SAS #####
# SAS will be downloaded from HEASARC - this is the base for the populated URL
base_sas_link=https://heasarc.gsfc.nasa.gov/FTP/xmm/software/sas/${sas_version}/Linux/Ubuntu${ubuntu_version}/

# This is the more general structure of the tar file name (see it in the HEASARC FTP for other versions
#  of SAS), but unfortunately there isn't a file with this easy to populate name structure for
#  the Ubuntu version (24.04) that I'm working with right now
# sas_file=sas_${sas_version}-Ubuntu${ubuntu_version}.tgz

# HARD CODED - this is the non-generalised file link to the tar of SAS I'm working with right now (22.1.0 for Ubuntu 24.04)
sas_file=sas_${sas_version}-a8f2c2afa-20250304-ubuntu${ubuntu_version}-gcc13.3.0-x86_64.tgz
# HARD CODED - This is the non-generalised name of the directory that XMM-SAS gets 'built' in
sas_install_dir=xmmsas_22.1.0-a8f2c2afa-20250304

# Assembling the download link
sas_link=$base_sas_link${sas_file}
###########################


###########################################################

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
  - rsync
EOF

# Use the yml to create the SAS env
bash /usr/local/bin/conda-env-install.sh

# Use the Python requirements file included in the SAS directory to install
#  the module that it wants for some included Python bits (e.g. pySAS)
# Other build scripts for Fornax images seem to use the uv package manager, so we 
#  will as well - particularly the pip CLI version
micromamba run -n sas uv pip install -r sas_python_packages.txt
###########################################################


############ Moving unpacked SAS and installing ###########
# Moves all of the files unpacked from the SAS download into the conda environment directory
#  for SAS - it is easier to install SAS in-situ, rather than installing it then moving it, as 
#  some file paths get baked in during the installation process
mv * $ENV_DIR/sas/
# We must follow the unpacked files
cd $ENV_DIR/sas/

# Run the SAS install script, specifically in the environment we've just created
micromamba run -n sas ./install.sh
###########################################################


# TODO - finalize handling of calibration files. Not just XMM, but all missions. Current version of XMM CCF is
#  stored in 'support-data', which will do for now
##################### Download XMM CCF ####################
# We download it straight into the support data directory - this command cannot work on Fornax images without
#  ensuring we install rsync through Conda, which is why we added it to the sas conda env
# The ';' on the end of the rsync call means that the rest of the script will proceed if this command fails
#mkdir -p $SUPPORT_DATA_DIR/xmm_sas/
#micromamba run -n sas rsync -v -a --delete --delete-after --force --include='*.CCF' --exclude='*/' sasdev-xmm.esac.esa.int::XMM_VALID_CCF $SAS_CCFPATH;

# Rather than the rsync method, we'll download all .CCF files from the HEASARC mirror
#  of XMM calibration files using wget. This doesn't necessarily seem as safe
#  as the rsync method, but will do for. This command is set up to recursively download level-1 (i.e. not going 
#  down into sub-directories) files that have the .CCF extension. Sub-directories are not downloaded, and the files
#  are put into the $SAS_CCFPATH path set at the top of this script.
# wget -r -l1 -nd --accept .CCF -P $SAS_CCFPATH -e robots=off https://heasarc.gsfc.nasa.gov/FTP/caldb/data/xmm/ccf/
###########################################################


################ Add conda (de)activation scripts ###############
# These scripts set up SAS and handles additional environment variable setting
cat <<EOF > $ENV_DIR/sas/etc/conda/activate.d/sas-general_activate.sh
#!/usr/bin/bash

# SAS can be very particular about Perl - this is the path we set when SAS was 'built'
export SAS_PERL=/usr/bin/perl
# And this is the conda environment we set up for it
export SAS_PYTHON=\$ENV_DIR/sas/bin/python

# Adds the SAS conda environment library to the library path - without this
#  we will get errors about not being able to find libsm.so.6 
export LD_LIBRARY_PATH="\$LD_LIBRARY_PATH:$ENV_DIR/sas/lib"

# Any attempted init of SAS will fail without this path being set
export SAS_DIR=\$ENV_DIR/sas/${sas_install_dir}
source \$SAS_DIR/setsas.sh
EOF


cat <<EOF > $ENV_DIR/sas/etc/conda/activate.d/sas-ccf_activate.sh
#!/usr/bin/bash

# This sets the environment variable for the XMM Current Calibration Files (CCF)
export SAS_CCFPATH=${SAS_CCFPATH}
EOF

######
# This scripts unsets many of the environment variables set in the activation scripts
# Honestly don't really know how much most of this matters, and am currently only getting the 
#  environment variables that I know have been set, not those that the setsas.sh script sets
cat <<EOF > $ENV_DIR/sas/etc/conda/deactivate.d/sas-general_deactivate.sh
#!/usr/bin/bash

unset SAS_PERL
unset SAS_PYTHON

# I _think_ this should be fine
unset LD_LIBRARY_PATH

unset SAS_DIR
unset SAS_CCFPATH
EOF
###########################################################


###################### Final clean up #####################
# In the /opt/envs/sas directory, where we copied the unpacked contents of the SAS download
#  and installed them - time to clean up the left over files
rm sas_python_packages.txt

cd $HOME
rm -rf $WORKDIR
###########################################################
