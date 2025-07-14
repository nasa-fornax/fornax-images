#!/bin/bash

# if NOTEBOOK_DIR is not defined; return or exit
if test -z $NOTEBOOK_DIR; then
    # since this script is sourced, we return
    echo "NOTEBOOK_DIR not defined; exiting ..."
    return 0
fi

echo "Linking the notebooks in $HOME ..."

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

# bring in the intro page
if test -f $JUPYTER_DIR/introduction.html && ! test -L $NOTEBOOK_DIR/introduction.html; then
    cp $JUPYTER_DIR/introduction.html $NOTEBOOK_DIR
fi