#!/bin/bash
# Handle uv environment
# Creates an environment for every requirements-{env-name}.txt file

# emvdir: where to install the new environment
# if not given, default to ENV_DIR
envdir=$1
if [ -z envdir ]; then
    envdir=$ENV_DIR
fi
echo "Installing environment in: $envdir"


for envfile in `ls requirements-*.txt`; do
    env=`echo $envfile | sed -n 's/requirements-\(.*\)\.txt/\1/p'`
    if test -f requirements-${env}-lock.txt; then
        ENVFILE=requirements-${env}-lock.txt
    else
        ENVFILE=requirements-${env}.txt
    fi
    echo "Found $ENVFILE, using it ..."
    export VIRTUAL_ENV=$envdir/$env
    # ensure we use the same python in jupyter so dask works
    uv venv $VIRTUAL_ENV -p $ENV_DIR/base/bin/python$PYTHON_VERSION
    uv pip install -r $ENVFILE
    # add our useful packages
    uv pip install ipykernel pip
    # install the kernel so jupyter can find it;
    # update PATH, so `which python` works correctly in the notebook
    if [ "$envdir" == "$ENV_DIR" ]; then
        uv run python -m ipykernel install --name $env --prefix $JUPYTER_DIR
        KERNEL_JSON="$JUPYTER_DIR/share/jupyter/kernels/$env/kernel.json"
        # also do the locks
        uv pip list --format=freeze > $VIRTUAL_ENV/$ENVFILE
        mkdir -p $LOCK_DIR
        cp $VIRTUAL_ENV/$ENVFILE $LOCK_DIR
    else
        uv run python -m ipykernel install --name $env --user
        KERNEL_JSON="$HOME/.local/share/jupyter/kernels/$env/kernel.json"
    fi
    jq ".env = (.env // {}) | .env.PATH = \"$envdir/$env/bin:$PATH\"" $KERNEL_JSON > /tmp/tmp.$$.json
    mv /tmp/tmp.$$.json $KERNEL_JSON
    # clean up
    find $VIRTUAL_ENV -follow -type f \( -name '*.a' -o -name '*.pyc' -o -name '*.js.map' \) -delete
done

# clean
uv cache clean
