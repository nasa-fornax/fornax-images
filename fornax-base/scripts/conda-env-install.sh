#!/bin/bash

# handle conda environment and lock files
# look for conda-{env}-lock.yml and conda-{env}.yml files

for envfile in `ls conda-*.yml`; do
    env=`echo $envfile | sed -n 's/conda-\(.*\)\.yml/\1/p'`
    ENVFILE=conda-${env}.yml
    echo "Found $ENVFILE, using it ..."
    # if environment exists, error
    if [ -d $ENV_DIR/$env ]; then
        echo "*ERROR*: $ENV_DIR/$env exists! Cannot install $env from $ENVFILE"
        exit 1
    fi
    echo "Creating $env ..."
    micromamba create -y -n $env -f $ENVFILE -r $ENV_DIR/.. --use-uv

    # add our useful packages
    micromamba install -n $env -y -r $ENV_DIR/.. ipykernel pip

    # add the environment as a jupyter kernel
    micromamba run -n $env -r $ENV_DIR/.. python -m ipykernel install --name $env --prefix $JUPYTER_DIR
    
    # Run the kernel with 'conda run -n $env', so the etc/condat/activate.d scripts
    # are called correctly; this is needed when jupyterlab is running outside the kernel
    KERNEL_JSON="$JUPYTER_DIR/share/jupyter/kernels/$env/kernel.json"
    jq ".argv = [\"/usr/local/bin/micromamba\", \"run\", \"-n\", \"$env\", \"-r\", \"$ENV_DIR/..\", \"python\"] + .argv[1:]" $KERNEL_JSON > /tmp/tmp.$$.json
    mv /tmp/tmp.$$.json $KERNEL_JSON
    # save lock file
    micromamba env -n $env -r $ENV_DIR/.. export > $ENV_DIR/$env/${env}-lock.yml
    # also save it in one location
    mkdir -p $LOCK_DIR
    cp $ENV_DIR/$env/${env}-lock.yml $LOCK_DIR
    # clean up
    find $ENV_DIR/$env -follow -type f \( -name '*.a' -o -name '*.pyc' -o -name '*.js.map' \) -delete
done

# clean
micromamba clean -yaf
uv cache clean
