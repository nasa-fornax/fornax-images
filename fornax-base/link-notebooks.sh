#!/bin/bash

# if NOTEBOOK_DIR is not defined; return or exit
if test -z $NOTEBOOK_DIR; then
    # since this script is sourced, we return
    echo "NOTEBOOK_DIR not defined; exiting ..."
    return 0
fi

echo "Linking the notebooks in /home/$NB_USER ..."

# make symlink for NOTEBOOD_DIR in HOME
cd /home/$NB_USER
home_nb_dir=fornax-notebooks
# if there is a folder and is not a symlink, rename it
if test -d $home_nb_dir && ! test -L $home_nb_dir; then
    mv $home_nb_dir ${home_nb_dir}.rename
fi
if ! test -d $home_nb_dir; then
    ln -s $NOTEBOOK_DIR $home_nb_dir
fi