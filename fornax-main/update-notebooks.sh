#!/bin/bash
set +e
timeout=10

notebook_repos=(
    # main demo notebooks
    https://github.com/nasa-fornax/fornax-demo-notebooks.git
    # Documentation
    https://github.com/nasa-fornax/fornax-documentation.git
    # lsdb notebeooks
    https://github.com/lincc-frameworks/IVOA_2024_demo.git
)

if test -z $NOTEBOOK_DIR; then export NOTEBOOK_DIR=$HOME/notebooks; fi
mkdir -p $NOTEBOOK_DIR
cd $NOTEBOOK_DIR
# copy notebooks
echo "Cloning the notebooks to $notebook_dir ..."
for repo in ${notebook_repos[@]}; do
    name=`echo $repo | sed 's#.*/\([^/]*\)\.git#\1#'`
    if ! test -f $NOUPDATE; then
        timeout $timeout $CONDA_DIR/bin/python -m nbgitpuller.pull $repo main $name
    fi
done
cd $HOME

# change the default kernels in the notebooks;
# remove once they are changed upstream
cd $NOTEBOOK_DIR/fornax-demo-notebooks
sed -i 's/display_name: notebook/display_name: py-multiband_photometry/' forced_photometry/multiband_photometry.md
sed -i -e 's/display_name: notebook/display_name: py-light_curve_generator/' light_curves/light_curve_generator.md
sed -i -e 's/display_name: notebook/display_name: py-light_curve_classifier/' light_curves/light_curve_classifier.md
sed -i -e 's/display_name: notebook/display_name: py-ml_agnzoo/' light_curves/ML_AGNzoo.md
sed -i -e 's/display_name: notebook/display_name: py-scale_up/' light_curves/scale_up.md
sed -i -e 's/display_name: notebook/display_name: py-spectra_generator/' spectroscopy/spectra_generator.md
cd $HOME