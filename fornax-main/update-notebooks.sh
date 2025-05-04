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
        timeout $timeout python -m nbgitpuller.pull $repo main $name
    fi
done
cd $HOME
