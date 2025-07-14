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
    # use nbgitpuller
    timeout $timeout $JUPYTER_DIR/bin/gitpuller $repo main $name
done

# bring in the intro page
if test -f $JUPYTER_DIR/introduction.html && ! test -L $NOTEBOOK_DIR/introduction.html; then
    cp $JUPYTER_DIR/introduction.html $NOTEBOOK_DIR
fi



# reset location
cd $HOME