#!/bin/bash

# Clone the notbeooks
# USAGE:
#  ./script fornax | irsa | mast | heasarc

# if NOTEBOOK_DIR is not defined; return or exit
if test -z $NOTEBOOK_DIR; then
    # since this script is sourced, we return
    echo "NOTEBOOK_DIR not defined; returning ..."
    return 0
fi

# Get argument
choice=$1

# Parse argument
case "$choice" in
    fornax)
        repo="https://github.com/nasa-fornax/fornax-demo-notebooks.git"
        branch="deployed_notebooks"
        ;;
    irsa)
        repo="https://github.com/Caltech-IPAC/irsa-tutorials.git"
        branch="deploy_to_fornax"
        ;;
    mast)
        repo="https://github.com/sedonaprice/mast_notebooks.git"
        branch="deploy_to_fornax"
        ;;
    heasarc)
        repo="https://github.com/heasarc/heasarc-tutorials.git"
        branch="production-notebooks"
        ;;
    *)
        # Handle invalid input
        echo "Error: Invalid argument '$choice'."
        echo "Usage: $0 {fornax|irsa|mast|heasarc}"
        exit 1
        ;;
esac

mkdir -p $NOTEBOOK_DIR
cd $NOTEBOOK_DIR
# copy notebooks
echo "Cloning the notebooks to $NOTEBOOK_DIR ..."

name=`echo $repo | sed 's#.*/\([^/]*\)\.git#\1#'`
echo "++++ Updating $name from $repo ..."
if [ -d $name ]; then
    # first ensure we can delete it
    find $name -type d -exec chmod 755 {} +
    find $name -type f -exec chmod 644 {} +
    # now delete
    rm -rf $name
fi
# get a fresh clone of the the repo
git clone --branch $branch --single-branch --depth 1 $repo
rm -rf $name/.git
echo "+++++ Done with $name!"


# fix subforlder in irsa-tutorials
if [ "$choice" == "irsa" ]; then
    cd $NOTEBOOK_DIR
    if [ -d irsa-tutorials/irsa-tutorials ]; then
        mv irsa-tutorials/*.* irsa-tutorials/irsa-tutorials
        mv irsa-tutorials irsa-tutorials.off
        mv irsa-tutorials.off/irsa-tutorials .
        rm -r irsa-tutorials.off
    fi
fi

# fix names in mast-tutorials
if [ "$choice" == "mast" ]; then
    cd $NOTEBOOK_DIR
    if [ -d mast_notebooks/mast_notebooks ]; then
        mv mast_notebooks/*.* mast_notebooks/mast_notebooks
        mv mast_notebooks mast_notebooks.off
        mv mast_notebooks.off/mast_notebooks mast-tutorials
        mv mast-tutorials/requirements_mast_tutorials.txt mast-tutorials/requirements-py-mast-tutorials.txt 
        rm -r mast_notebooks.off
    fi
fi

if [ "$choice" == "heasarc" ]; then
    # remove extra files from heasarc tutorials
    cd $NOTEBOOK_DIR/heasarc-tutorials/
    rm README.md
    find . -type f -name '*.ipynb' -delete
fi

# add fornax-main manifest
if [ "$choice" == "fornax" ]; then
    cd $NOTEBOOK_DIR
    cat <<EOF > fornax-demo-notebooks/fornax-manifest.txt
crossmatch/ztf_ps1_crossmatch.md: Cross-Match ZTF and Pan-STARRS using LSDB
forced_photometry/multiband_photometry.md: Automated Multiband Forced Photometry on Large Datasets
light_curves/ML_AGNzoo.md: AGN Zoo, Comparison of AGN seleceted different metrics
light_curves/light_curve_classifier.md: Light Curve Classifer
light_curves/light_curve_collector.md: Make Multi-wavelength light curves using archival data.
light_curves/scale_up.md: Make Multi-wavelength light Curves for Large Samples
spectroscopy/spectra_collector.md: Extract Multi-wavelength Spectroscopy From Archival Data
EOF
fi


# Now make the notebooks files read-only
find $name -type f -exec chmod 444 {} +

# reset location
cd $HOME
