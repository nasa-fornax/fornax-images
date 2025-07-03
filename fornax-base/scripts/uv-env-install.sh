#!/bin/bash
# Handle uv environment
# Creates an environment for every requirements-{env-name}.txt file

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
    # add our useful packages
    uv pip install ipykernel pip
    # install the kernel so jupyter can find it
    uv run python -m ipykernel install --name $env --prefix $JUPYTER_DIR
    # update PATH, so `which python` works correctly in the notebook
    KERNEL_JSON="$JUPYTER_DIR/share/jupyter/kernels/$env/kernel.json"
    jq ".env = (.env // {}) | .env.PATH = \"$ENV_DIR/$env/bin:$PATH\"" $KERNEL_JSON > /tmp/tmp.$$.json
    mv /tmp/tmp.$$.json $KERNEL_JSON
    uv pip list --format=freeze > $VIRTUAL_ENV/$ENVFILE
    # also save it in one location
    mkdir -p $LOCK_DIR
    cp $VIRTUAL_ENV/$ENVFILE $LOCK_DIR
    # clean up
    find $VIRTUAL_ENV -follow -type f \( -name '*.a' -o -name '*.pyc' -o -name '*.js.map' \) -delete
done

# clean
uv cache clean
