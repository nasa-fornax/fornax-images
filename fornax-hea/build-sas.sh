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

# As the Fornax-Hea image that results from these installation scripts is no longer loaded directly into Fornax, and
#  is instead split up so that the large software packages are served in Amazon Machine Images (AMI), we can
#  must take some steps to ensure that this image is usable on platforms other than Fornax.
# First remove the existing, inevitably broken because it is pointing to a non-mounted Fornax resource, directory -
#  there is some directory-checking logic here because another of the build scripts may have already done this
[ -L $SUPPORT_DATA_DIR ] && ! [ -e $SUPPORT_DATA_DIR ] && rm $SUPPORT_DATA_DIR
# Then make a new support data directory
mkdir -p $SUPPORT_DATA_DIR

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
# Define the name of the environment to be set up
export ENV_NAME=sas

# SAS gets upset if it can't find Perl - this will need to be included in an activate.d script
#  as well, to make sure this path is set when the user loads the environment in
export SAS_PERL=/usr/bin/perl
# We set this to point at the conda environment we're just about to produce - ENV_DIR is not
#  set in this script, but we can trust that it will be
export SAS_PYTHON=$ENV_DIR/$ENV_NAME/bin/python

###########################################################


##################### DOWNLOADING SAS #####################
# SAS will be downloaded from HEASARC - this is the base for the populated URL
base_sas_link=https://heasarc.gsfc.nasa.gov/FTP/xmm/software/sas/${sas_version}/Linux/Ubuntu${ubuntu_version}/

# This is the structure of the software tar file name
sas_file=sas_${sas_version}-Ubuntu${ubuntu_version}.tgz

# Assembling the download link
sas_link=$base_sas_link${sas_file}
###########################################################


########### Download and unpack required files ############
wget -qL $sas_link \
	&& tar xvf $sas_file \
	&& rm -f $sas_file
###########################################################


########## Determine name of install directory  ###########
# Set the pattern to search for
pattern="xmmsas_${sas_version}-*bin*"

# Find all matching files and store them in an array
matches=($pattern)

# Get the number of matches
num_matches=${#matches[@]}

# Check the conditions
# The first part checks if there are no matches, or if there is exactly one match
# AND that match is the pattern itself (meaning no files were found).
if [[ $num_matches -eq 0 ]] || [[ $num_matches -eq 1 && "${matches[0]}" == "$pattern" ]]; then
  echo "Error: No matching files found for '$pattern'." >&2
  exit 1
elif [[ $num_matches -gt 1 ]]; then
  echo "Error: Multiple matching files found for '$pattern'." >&2
  exit 1
else
  # A single, real match was found, so we split the file name to retrieve the installation folder
  sas_bin_file="${matches[0]}"
  sas_install_dir="${sas_bin_file%%-bin*}"
fi
###########################################################


############# Setup the SAS Conda environment #############
# Creates a Conda definition file that can be used to setup the environment that SAS
#  will be associated with
# We use the Conda-hosted HEASoft to avoid downloading and building HEASoft manually
cat <<EOF > conda-$ENV_NAME.yml
name: $ENV_NAME
channels:
  - https://heasarc.gsfc.nasa.gov/FTP/software/conda
  - conda-forge
dependencies:
  - python=$py_version
  - ghostscript
  - pip
  - pip:
    - pytest
    - astroquery
    - astropy
    - s3fs
    - boto3
    - xmmpysas
EOF

# Use the yml to create the SAS env
bash /usr/local/bin/conda-env-install.sh
###########################################################


############ Updating the environment lock file ###########
# Updating the lock file and moving it to the lock file directory
micromamba env -n $ENV_NAME export > $ENV_DIR/$ENV_NAME/$ENV_NAME-lock.yml
cp $ENV_DIR/$ENV_NAME/$ENV_NAME-lock.yml $LOCK_DIR
###########################################################


############ Moving unpacked SAS and installing ###########
# Moves all of the files unpacked from the SAS download into the conda environment directory
#  for SAS - it is easier to install SAS in-situ, rather than installing it then moving it, as
#  some file paths get baked in during the installation process
mv * $ENV_DIR/$ENV_NAME/
# We must follow the unpacked files
cd $ENV_DIR/$ENV_NAME/

# Run the SAS install script, specifically in the environment we've just created
micromamba run -n $ENV_NAME ./install.sh
###########################################################


################ Add conda (de)activation scripts ###############
# Ensure that the directories we need actually exist
mkdir -p $ENV_DIR/$ENV_NAME/etc/conda/activate.d
mkdir -p $ENV_DIR/$ENV_NAME/etc/conda/deactivate.d

# These scripts set up SAS and handles additional environment variable setting
cat <<EOF > $ENV_DIR/$ENV_NAME/etc/conda/activate.d/sas-general_activate.sh
#!/usr/bin/bash

# SAS can be very particular about Perl - this is the path we set when SAS was 'built'
export SAS_PERL=$SAS_PERL
# And this is the conda environment we set up for it
export SAS_PYTHON=\$ENV_DIR/$ENV_NAME/bin/python

# Adds the SAS conda environment library to the library path, as well as the HEASoft conda
#  environment library (this helps us to avoid replication of some basic libraries
#  and saves space)
export LD_LIBRARY_PATH="\$LD_LIBRARY_PATH:$ENV_DIR/$ENV_NAME/lib:$ENV_DIR/heasoft/lib"

# Setting up HEASoft, otherwise SAS will fall over when you try to init it
export HEADAS=\$ENV_DIR/heasoft/heasoft
source \$HEADAS/headas-init.sh

# Any attempted init of SAS will fail without this path being set
export SAS_DIR=\$ENV_DIR/$ENV_NAME/${sas_install_dir}
source \$SAS_DIR/setsas.sh

# This sets the environment variable for the XMM Current Calibration Files (CCF)
export SAS_CCFPATH=\$SUPPORT_DATA_DIR/xmm_ccf

EOF

######
# This scripts unsets many of the environment variables set in the activation scripts
# Honestly don't really know how much most of this matters, and am currently only getting the
#  environment variables that I know have been set, not those that the setsas.sh script sets
cat <<EOF > $ENV_DIR/$ENV_NAME/etc/conda/deactivate.d/sas-general_deactivate.sh
#!/usr/bin/bash

unset SAS_PERL
unset SAS_PYTHON

export LD_LIBRARY_PATH=$SAS_PREV_LD_LIBRARY_PATH

unset SAS_DIR
unset SAS_CCFPATH
EOF
###########################################################


################# Move XMM SAS data ##################
# Here we move an existing directory and put symlink it back to its original location - this is to minimize the
#  size of the AMI environment images (as they will just use the support-data directory that is already on
#  Fornax), and make sure that the Fornax-Hea image will still have access to the support data when it runs on
#  another platform.
mkdir -p $SUPPORT_DATA_DIR/xmmsas-${sas_version}
# This data directory IS necessary for SAS to work
mv $ENV_DIR/$ENV_NAME/${sas_install_dir}/lib/data $SUPPORT_DATA_DIR/xmmsas-${sas_version}/sas_data
# And then symlink it back
ln -s $SUPPORT_DATA_DIR/xmmsas-${sas_version}/sas_data $ENV_DIR/$ENV_NAME/${sas_install_dir}/lib/data

# We also remove the documentation source and build, once again to save space (don't bother symlinking this one,
#  the documentation are very easily found online).
rm -r $ENV_DIR/$ENV_NAME/${sas_install_dir}/doc
######################################################


###################### Final clean up #####################
# In the /opt/envs/sas directory, where we copied the unpacked contents of the SAS download
#  and installed them - time to clean up the left over files
rm sas_python_packages.txt

# We remove the pySAS baked in to the current release of XMM-SAS - we have instead installed the
#  xmmpysas package maintained by the NASA XMM GOF
rm -rf $ENV_DIR/$ENV_NAME/$sas_install_dir/lib/python/pysas

cd $HOME
rm -rf $WORKDIR
###########################################################
