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
    # update PATH, so `which python` works correctly in the notebook
    KERNEL_JSON="$CONDA_DIR/share/jupyter/kernels/$env/kernel.json"
    jq ".env = (.env // {}) | .env.PATH = \"$ENV_DIR/$env/bin:$PATH\"" $KERNEL_JSON > /tmp/tmp.$$.json
    mv /tmp/tmp.$$.json $KERNEL_JSON
    uv pip freeze > $VIRTUAL_ENV/$ENVFILE
done

# clean
uv cache clean
pip cache purge

