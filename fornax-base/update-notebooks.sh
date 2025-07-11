#!/bin/bash

# if something fails, keep going, we don't want to the stop the server from loading
set -e
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