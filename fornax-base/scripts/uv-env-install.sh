#!/bin/bash
set -e
set -o pipefail

# handle uv environment

for envfile in `ls requirements-*.txt`; do
    env=`echo $envfile | sed -n 's/requirements-\(.*\)\.txt/\1/p'`
    if test -f requirements-${env}-lock.txt; then
        ENVFILE=requirements-${env}-lock.txt
    else
        ENVFILE=requirements-${env}.txt
    fi
    echo "Found $ENVFILE, using it ..."
    export VIRTUAL_ENV=$ENV_DIR/$env
    uv venv $VIRTUAL_ENV
    uv pip install -r $ENVFILE
    uv pip install ipykernel
    uv run python -m ipykernel install --name $env --prefix $CONDA_DIR
    uv pip freeze > $VIRTUAL_ENV/$ENVFILE
done

# clean
uv cache clean
pip cache purge

