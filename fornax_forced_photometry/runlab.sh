#!/bin/bash -x

echo 1>&2 "Starting, home is ${HOME}"
export HOME=/home/${JUPYTERHUB_USER}
echo 1>&2 "Now home is ${HOME}"

function copy_etc_skel() {
    es="/etc/skel"
    for i in $(find ${es}); do
        if [ "${i}" == "${es}" ]; then
            continue
        fi
        b=$(echo ${i} | cut -d '/' -f 4-)
        hb="${HOME}/${b}"
        if ! [ -e ${hb} ]; then
            cp -a ${i} ${hb}
        fi
    done
}

# Set DEBUG to a non-empty value to turn on debugging
if [ -n "${DEBUG}" ]; then
    set -x
fi

# source the profile defined in the image
. /etc/profile

# Bump up node max storage to allow rebuild
NODE_OPTIONS=${NODE_OPTIONS:-"--max-old-space-size=6144"}
export NODE_OPTIONS
sync
cd ${HOME}
# Do /etc/skel copy (in case we didn't provision homedir but still need to
#  populate it)
copy_etc_skel
# Replace API URL with service address if it exists
if [ -n "${HUB_SERVICE_HOST}" ]; then
    jh_proto=$(echo $JUPYTERHUB_API_URL | cut -d '/' -f -1)
    jh_path=$(echo $JUPYTERHUB_API_URL | cut -d '/' -f 4-)
    port=${HUB_SERVICE_PORT_API}
    if [ -z "${port}" ]; then
        port="8081"
    fi
    jh_api="${jh_proto}//${HUB_SERVICE_HOST}:${port}/${jh_path}"
    JUPYTERHUB_API_URL=${jh_api}
fi
export JUPYTERHUB_API_URL

cmd="jupyter-labhub \
     --ip='*' --port=8888 \
     --hub-api-url=${JUPYTERHUB_API_URL} \
     --notebook-dir=${HOME}"
if [ -n "${DEBUG}" ]; then
    cmd="${cmd} --debug"
fi
echo 1>&2 "JupyterLab command: '${cmd}'"
# Run idle culler.
if [ -n "${JUPYTERLAB_IDLE_TIMEOUT}" ] && \
   [ "${JUPYTERLAB_IDLE_TIMEOUT}" -gt 0 ]; then
     touch ${HOME}/idleculler/culler.output && \
       nohup python3 /usr/local/bin/selfculler.py >> \
             ${HOME}/idleculler/culler.output 2>&1 &
fi
if [ -n "${DEBUG}" ]; then
    # Spin while waiting for interactive container use.
    while : ; do
        ${cmd}
        d=$(date)
        echo 1>&2 "${d}: sleeping."
        sleep 60
    done
    exit 0 # Not reached
fi
# Start Lab
exec ${cmd}
