#!/usr/bin/bash

# Build script to setup a conda environment for INTEGRAL's OSA toolkit

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

# Sets up the working directory where OSA will assembled
WORKDIR=/tmp/osa
mkdir -p $WORKDIR
cd $WORKDIR

# Deletes any existing contents of the working directory
rm -rf * > /dev/null 2>&1
###########################################################


############# Definition of software versions #############
osa_ubuntu_version=20.04
osa_version=11.2
osa_cat_version=43

py_version=$PYTHON_VERSION
###########################################################


############### Setting up useful variables ###############
# Define the name of the environment to be set up
export ENV_NAME=osa
###########################################################


##################### DOWNLOADING OSA #####################
# OSA will be downloaded from HEASARC - this is the base for the populated URL
osa_base_link=https://heasarc.gsfc.nasa.gov/FTP/integral/software/

# The name of the OSA file
osa_file=osa${osa_version}-Ubuntu_${osa_ubuntu_version}_x86_64.tar.gz

# Put-together URL to download OSA
osa_link=$osa_base_link$osa_file
###########################################################


########### Download and unpack required files ############
wget -qL $osa_link \
	&& tar xvf $osa_file \
	&& rm -f $osa_file
############################################################


########## Determine name of install directory  ###########
# Set the pattern to search for
pattern="osa*"

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
  # A single, real match was found, and we have our directory name
  osa_install_dir="${matches[0]}"
fi

puts $osa_install_dir
###########################################################


############# Setup the OSA Conda environment #############
# Creates a Conda definition file that can be used to setup the environment that OSA
#  will be associated with
# We use the Conda-hosted HEASoft to avoid downloading and building HEASoft manually
cat <<EOF > conda-$ENV_NAME.yml
name: $ENV_NAME
channels:
  - https://heasarc.gsfc.nasa.gov/FTP/software/conda
  - conda-forge
dependencies:
  - python=$py_version
  - boto3
  - astroquery
  - astropy
  - s3fs
  - pip
EOF

# Use the yml to create the OSA environment
bash /usr/local/bin/conda-env-install.sh
###########################################################


############ Updating the environment lock file ###########
# Updating the lock file and moving it to the lock file directory
micromamba env -n $ENV_NAME export > $ENV_DIR/$ENV_NAME/$ENV_NAME-lock.yml
cp $ENV_DIR/$ENV_NAME/$ENV_NAME-lock.yml $LOCK_DIR
###########################################################


################### Moving unpacked OSA  ##################
# Untarring and decompressing the downloaded OSA file should result in
#  a single directory, we'll move that to the new conda env directory now
mv $osa_install_dir $ENV_DIR/$ENV_NAME/
# We must follow the unpacked files
cd $ENV_DIR/$ENV_NAME/
###########################################################


############# Add conda (de)activation scripts ############
# Ensure that the directories we need actually exist
mkdir -p $ENV_DIR/$ENV_NAME/etc/conda/activate.d
mkdir -p $ENV_DIR/$ENV_NAME/etc/conda/deactivate.d

# These scripts set up OSA and handles additional environment variable setting
cat <<EOF > $ENV_DIR/$ENV_NAME/etc/conda/activate.d/osa-general_activate.sh
#!/usr/bin/bash

# Recording the pre-OSA environment LD_LIBRARY_PATH environment variable
OSA_PREV_LD_LIBRARY_PATH=$LD_LIBRARY_PATH
# Same for the binaries PATH
OSA_PREV_PATH=$PATH

# The absolute path to the OSA install directory
export ISDC_ENV=$ENV_DIR/$ENV_NAME/${osa_install_dir}

# Initialize OSA by calling an included bash script
#  This sets up a few environment variables, including adding to the PATH and
#  LD_LIBRARY_PATH. There doesn't appear to be an uninit script, so we looked
#  for the environment variables it sets and unset them in the deactivation script
source $ISDC_ENV/bin/isdc_init_env.sh

# Setting the path to the INTEGRAL reference catalog
#export ISDC_REF_CAT=

# Should stop the OSA GUI popping up
export COMMONSCRIPT=1


# Adds the OSA conda environment library to the library path, as well as the HEASoft conda
#  environment library
export LD_LIBRARY_PATH="\$LD_LIBRARY_PATH:$ENV_DIR/$ENV_NAME/lib:$ENV_DIR/heasoft/lib"


# TODO NEED TO FIGURE OUT HOW TO UNINIT HEASOFT
# Setting up HEASoft
export HEADAS=\$ENV_DIR/heasoft/heasoft
source \$HEADAS/headas-init.sh

EOF

######
# This scripts unsets many of the environment variables set in the activation scripts
cat <<EOF > $ENV_DIR/$ENV_NAME/etc/conda/deactivate.d/osa-general_deactivate.sh
#!/usr/bin/bash

unset ISDC_ENV
#unset ISDC_REF_CAT

unset COMMONSCRIPT

export LD_LIBRARY_PATH=$OSA_PREV_LD_LIBRARY_PATH
unset OSA_PREV_LD_LIBRARY_PATH

export PATH=$OSA_PREV_PATH
unset OSA_PREV_PATH

# Some environment variables created by the OSA init script
unset ISDC_SCRIPT_PATH
unset CFITSIO_INCLUDE_FILES
unset MANPATH
unset ROOTSYS
EOF
###########################################################


###################### Move OSA data ######################
# Here we move an existing directory and put symlink it back to its original location - this is to minimize the
#  size of the AMI environment images (as they will just use the support-data directory that is already on
#  Fornax), and make sure that the Fornax-Hea image will still have access to the support data when it runs on
#  another platform.

# TODO POSSIBLY REMOVE
#mkdir -p $SUPPORT_DATA_DIR/osa-${osa_version}

#mv $ENV_DIR/$ENV_NAME/${osa_install_dir}/lib/data $SUPPORT_DATA_DIR/osa-${osa_version}/sas_data
# And then symlink it back
#ln -s $SUPPORT_DATA_DIR/xmmsas-${sas_version}/sas_data $ENV_DIR/$ENV_NAME/${sas_install_dir}/lib/data

#rm -r $ENV_DIR/$ENV_NAME/${sas_install_dir}/doc
###########################################################


###################### Final clean up #####################
cd $HOME
rm -rf $WORKDIR
###########################################################
