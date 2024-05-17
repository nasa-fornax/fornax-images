#!/bin/bash

# handle conda environment and lock files
# look for conda-{env}-lock.yml and conda-{env}.yml files

for envfile in `ls conda-*.yml | grep -v lock`; do
    echo "Found env file ${envfile}"
    env=`echo $envfile | sed -n 's/conda-\(.*\)\.yml/\1/p'`
    LOCKFILE="conda-${env}-lock.yml"
    ENVFILE="conda-${env}.yml"
    if test -f $LOCKFILE; then
        echo "Found $LOCKFILE, using it ..."
        conda-lock install --name ${env} $LOCKFILE
    elif test -f $ENVFILE; then
        echo "Found $ENVFILE, using it ..."
        mamba env create -n ${env} -f $ENVFILE
    elif [[ "$env"=="$CONDA_ENV" ]]; then
        echo "Defaulting to basic env ..." 
        mamba create --name $env python=3.11 jupyterlab
    fi
done

# clean
mamba clean -yaf
find ${CONDA_DIR} -follow -type f -name '*.a' -delete
find ${CONDA_DIR} -follow -type f -name '*.js.map' -delete
