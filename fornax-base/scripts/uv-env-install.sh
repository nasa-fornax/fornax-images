#!/bin/bash
# Handle uv environment
# Creates an environment for every requirements-{env-name}.txt file

# emvdir: where to install the new environment
# if not given, default to ENV_DIR
envdir=$1
if [ -z $envdir ]; then
    envdir=$ENV_DIR
fi

if [[ "$envdir" == "-h" || "$envdir" == "--help" ]]; then
    echo "
    Setup pip-based python environment using uv.
    Also setup the corresponding notebook kernel.

    USAGE: $0 environment_dir
    -----

      1. Create a standard requirements text file named: requirements-{env_name}.txt.
    Where {env_name} is the name of your environment.
    
      2. environment_dir is the directory where you want the environment to be installed.
    Use: ~/user-envs/ if you want them to persist.
    If not given, install in \$ENV_DIR, which is reset with a new session.
    
    Activate with: source environment_dir/env_name/bin/activate
"
    exit 0
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
    # if environment exists, error
    if [ -d $envdir/$env ]; then
        echo "*ERROR*: $envdir/$env exists! Cannot install $env from $ENVFILE"
        exit 1
    fi
    # ensure we use the same python in jupyter so dask works
    uv venv $VIRTUAL_ENV -p $ENV_DIR/base/bin/python$PYTHON_VERSION
    uv pip install -r $ENVFILE
    # add our useful packages
    uv pip install ipykernel pip
    # install the kernel so jupyter can find it;
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
    # set PATH, so `!which python` works correctly in the notebook
    # set VIRTUAL_ENV so `!uv ..` works too.
    jq ".env = (.env // {}) 
        | .env.PATH = \"$envdir/$env/bin:$PATH\" 
        | .env.VIRTUAL_ENV = \"$VIRTUAL_ENV\"" $KERNEL_JSON > /tmp/tmp.$$.json
    mv /tmp/tmp.$$.json $KERNEL_JSON
    # clean up
    find $VIRTUAL_ENV -follow -type f \( -name '*.a' -o -name '*.pyc' -o -name '*.js.map' \) -delete
done

# clean
uv cache clean
