#!/bin/bash

# if something fails, keep going, we don't want to the stop the server from loading
set +e
timeout=10

# if NOTEBOOK_DIR is not defined; return or exit
if test -z $ADD_NOTEBOOKS; then
    # since this script is sourced, we return
    echo "ADD_NOTEBOOKS not defined; returning ..."
    return 0
fi


notebook_repos=(
    # main demo notebooks
    https://github.com/nasa-fornax/fornax-demo-notebooks.git
    # Documentation
    https://github.com/nasa-fornax/fornax-documentation.git
    # lsdb notebeooks
    https://github.com/lincc-frameworks/IVOA_2024_demo.git
)

mkdir -p $NOTEBOOK_DIR
cd $NOTEBOOK_DIR
# copy notebooks
echo "Cloning the notebooks to $NOTEBOOK_DIR ..."
for repo in ${notebook_repos[@]}; do
    name=`echo $repo | sed 's#.*/\([^/]*\)\.git#\1#'`
    if ! test -f $NOUPDATE; then
        # use nbgitpuller
        timeout $timeout $JUPYTER_DIR/bin/gitpuller $repo main $name
    fi
done

# change the default kernels in the notebooks;
# remove once they are changed upstream
if $JUPYTER_DIR/bin/jupyter kernelspec list  | grep multiband_photometry; then
    cd $NOTEBOOK_DIR/fornax-demo-notebooks
    jupytext --set-kernel py-multiband_photometry forced_photometry/multiband_photometry.md
    jupytext --set-kernel py-light_curve_generator light_curves/light_curve_generator.md
    jupytext --set-kernel py-light_curve_classifier light_curves/light_curve_classifier.md
    jupytext --set-kernel py-ml_agnzoo light_curves/ML_AGNzoo.md
    jupytext --set-kernel py-scale_up light_curves/scale_up.md
    jupytext --set-kernel py-spectra_generator spectroscopy/spectra_generator.md
fi
# ----------- #

# bring in the intro page
if test -f $JUPYTER_DIR/introduction.html; then
    cp $JUPYTER_DIR/introduction.html $NOTEBOOK_DIR
fi
# remove any old introduction.md
if test -f $NOTEBOOK_DIR/introduction.md; then
    rm $NOTEBOOK_DIR/introduction.md
fi

# make symlink for NOTEBOOD_DIR in HOME
cd $HOME
home_nb_dir=fornax-notebooks
# if there is a folder and is not a symlink, rename it
if test -d $home_nb_dir && ! test -L $home_nb_dir; then
    mv $home_nb_dir ${home_nb_dir}.rename
fi
if ! test -d $home_nb_dir; then
    ln -s $NOTEBOOK_DIR $home_nb_dir
fi

# reset location
cd $HOME