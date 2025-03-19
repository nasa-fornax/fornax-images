#!/bin/bash

set -e
set -o pipefail

# handle conda environment and lock files
# look for conda-{env}-lock.yml and conda-{env}.yml files

for envfile in `ls conda-*.yml | grep -v lock`; do
    env=`echo $envfile | sed -n 's/conda-\(.*\)\.yml/\1/p'`
    if test -f conda-${env}-lock.yml; then
        ENVFILE=conda-${env}-lock.yml
        echo "Found $ENVFILE, using it ..."
        # create the environment if it doesn't exist
        mamba env list | grep -q "^[[:space:]]*$env " || mamba create -n ${env}
        mamba env update -n ${env} -f $ENVFILE
    elif test -f conda-${env}.yml; then
        ENVFILE=conda-${env}.yml
        echo "Found $ENVFILE, using it ..."
        # create the environment if it doesn't exist
        mamba env list | grep -q "^[[:space:]]*$env " || mamba create -n ${env}
        mamba env update -n ${env} -f $ENVFILE
    elif [[ "$env"=="$CONDA_ENV" ]]; then
        echo "Defaulting to basic env ..." 
        mamba create --name $env python=3.12 jupyterlab
    fi
    if [ "$env" != "$CONDA_ENV" ]; then
        # add the environment as a jupyter kernel
        # CONDA_ENV is defined in the dockerfile
        mamba install -n $env ipykernel
        mamba run -n $env python -m ipykernel install --name $env --prefix $CONDA_DIR/envs/$CONDA_ENV
    fi
done

# clean
mamba clean -yaf
pip cache purge
find ${CONDA_DIR} -follow -type f -name '*.a' -name '*.pyc' -delete
find ${CONDA_DIR} -follow -type f -name '*.js.map' -delete
