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
        conda env update -n ${env} -f $ENVFILE --solver libmamba
    elif test -f conda-${env}.yml; then
        ENVFILE=conda-${env}.yml
        echo "Found $ENVFILE, using it ..."
        # create the environment if it doesn't exist
        mamba env list | grep -q "^[[:space:]]*$env " || mamba create -n ${env}
        conda env update -n ${env} -f $ENVFILE --solver libmamba
    fi
    if [ "$env" != "base" ]; then
        # add the environment as a jupyter kernel
        # DEFAULT_ENV is defined in the dockerfile
        mamba install -n $env -y ipykernel
        mamba run -n $env python -m ipykernel install --name $env --prefix $CONDA_DIR
        # update PATH, so `which python` works correctly in the notebook
        KERNEL_JSON="$CONDA_DIR/share/jupyter/kernels/$env/kernel.json"
        # Insert env block after: "language": "python", so calling cli commands from notebooks works.
        if [ "$env" == "heasoft" ]; then
            sed -i -e 's/"language": "python",/"language": "python",\n "env": {"PATH": "$CONDA_DIR\/envs\/$env\/heasoft\/bin:$CONDA_DIR\/envs\/$env\/bin:${PATH}"},/' $KERNEL_JSON
        else
            sed -i -e 's/"language": "python",/"language": "python",\n "env": {"PATH": "$CONDA_DIR\/envs\/$env\/bin:${PATH}"},/' $KERNEL_JSON
        fi
    fi
    # save lock file
    mamba env -n $env export > $CONDA_DIR/envs/$env/${env}-lock.yml
done

# clean
mamba clean -yaf
pip cache purge
find ${CONDA_DIR} -follow -type f -name '*.a' -name '*.pyc' -delete
find ${CONDA_DIR} -follow -type f -name '*.js.map' -delete
