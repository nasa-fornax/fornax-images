#!/bin/bash

timeout=10

# if NOTEBOOK_DIR is not defined; return or exit
if test -z $NOTEBOOK_DIR; then
    # since this script is sourced, we return
    echo "NOTEBOOK_DIR not defined; returning ..."
    return 0
fi


notebook_repos=(
    # main demo notebooks
    https://github.com/nasa-fornax/fornax-demo-notebooks.git
    # irsa
    https://github.com/Caltech-IPAC/irsa-tutorials.git
    # heasarc
    https://github.com/heasarc/heasarc-tutorials.git
)

# Branch to pull from, preferably a curated, deployed branch rather than the development default
deployed_branches=(
    # main demo notebooks
    deployed_notebooks
    # irsa
    deploy_to_fornax
    # heasarc
    production-notebooks
)

mkdir -p $NOTEBOOK_DIR
cd $NOTEBOOK_DIR
# copy notebooks
echo "Cloning the notebooks to $NOTEBOOK_DIR ..."

for i in ${!notebook_repos[@]}; do
    repo=${notebook_repos[i]}
    branch=${deployed_branches[i]}
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
done

# bring in the intro and release notes page
if test -f $JUPYTER_DIR/introduction.md && ! test -L $NOTEBOOK_DIR/introduction.md; then
    cp $JUPYTER_DIR/introduction.md $NOTEBOOK_DIR/introduction.mdv
fi
if test -f $JUPYTER_DIR/changes.md && ! test -L $NOTEBOOK_DIR/changes.md; then
    cp $JUPYTER_DIR/changes.md $NOTEBOOK_DIR/changes.mdv
fi

# fix subforlder in irsa-tutorials
cd $NOTEBOOK_DIR
if [ -d irsa-tutorials/irsa-tutorials ]; then
    mv irsa-tutorials/*.* irsa-tutorials/irsa-tutorials
    mv irsa-tutorials irsa-tutorials.off
    mv irsa-tutorials.off/irsa-tutorials .
    rm -r irsa-tutorials.off
fi

# fix kernel names for irsa
for nb in `find . -name 'irsa-tutorials/*.md'`; do
    $JUPYTER_DIR/bin/jupytext --set-kernel py-irsa-tutorials $nb
done

# remove extra files from heasarc tutorials
cd $NOTEBOOK_DIR/heasarc-tutorials/
rm README.md
find . -type f -name '*.ipynb' -delete

# add fornax-main manifest
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
# parse the manifests
if [ -f $JUPYTER_DIR/bin/parse_nb_manifest.py ]; then
    echo "Parsing manifests of archive notebooks"
    $JUPYTER_DIR/bin/python $JUPYTER_DIR/bin/parse_nb_manifest.py
fi

# Now make the notebooks files read-only
for i in ${!notebook_repos[@]}; do
    repo=${notebook_repos[i]}
    branch=${deployed_branches[i]}
    name=`echo $repo | sed 's#.*/\([^/]*\)\.git#\1#'`

    find $name -type f -exec chmod 444 {} +
done

# reset location
cd $HOME
