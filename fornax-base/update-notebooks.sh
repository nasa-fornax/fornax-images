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
)

# Branch to pull from, preferably a curated, deployed branch rather than the development default
deployed_branches=(
    deployed_notebooks
)

mkdir -p $NOTEBOOK_DIR
cd $NOTEBOOK_DIR
# copy notebooks
echo "Cloning the notebooks to $NOTEBOOK_DIR ..."
for i in ${!notebook_repos[@]}; do
    repo=${notebook_repos[i]}
    branch=${deployed_branches[i]}
    name=`echo $repo | sed 's#.*/\([^/]*\)\.git#\1#'`
    # use nbgitpuller
    timeout $timeout $JUPYTER_DIR/bin/gitpuller $repo $branch $name
done

# TEMPORARY fix for kernel names; remove once fixed upstream
if $JUPYTER_DIR/bin/jupyter kernelspec list  | grep multiband_photometry; then
    cd $NOTEBOOK_DIR/fornax-demo-notebooks
    jupytext --set-kernel py-light_curve_collector light_curves/light_curve_collector.md
fi

# bring in the intro page
if test -f $JUPYTER_DIR/introduction.html && ! test -L $NOTEBOOK_DIR/introduction.html; then
    cp $JUPYTER_DIR/introduction.html $NOTEBOOK_DIR
fi



# reset location
cd $HOME
