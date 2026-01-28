#!/bin/bash

# Add ~/.profile if it does not exist; which sources ~/.bashrc
# JL terminals source ~/.profile not ~/.bashrc
# But some user software may need ~/.bashrc (e.g. rust, julia)

# if something fails, keep going
set +ex
if [ ! -f /home/$NB_USER/.profile ]; then
    cat <<PROFILE > /home/$NB_USER/.profile
if [ -f /home/$NB_USER/.bashrc ]; then
    source /home/$NB_USER/.bashrc
fi
PROFILE
    chown $NB_USER:$NB_USER /home/$NB_USER/.profile
fi
# reset exit-on-error
set -e

## ----------------------------------------- ##
## Define some runtime environment variables ##
# for custom user environments
export USER_ENV_DIR="/home/$NB_USER/user-envs"
# for vscode
export CODE_EXECUTABLE=code-server
export CODE_EXTENSIONSDIR="/home/$NB_USER/.local/share/code-server/extensions"
# For firefly
export FIREFLY_URL=https://irsa.ipac.caltech.edu/irsaviewer \
# for dask
export DASK_DISTRIBUTED__DASHBOARD__LINK="/jupyter/user/{JUPYTERHUB_USER}/proxy/{port}/status"

## ----------------------------------------- ##
## run a kernel warmer in the background     ##
# warmup ipykernel so it loads faster in the environments
script=/tmp/kernel-warmer.sh
cat <<EOF > $script
echo "Starting kernel warmer ..."
for dd in \$(echo python3 heasoft py-* ciao fermi); do
    env=\$ENV_DIR/\$dd
    if test -x "\$env/bin/python"; then
        echo "warming \$env .."
        \$env/bin/python -m ipykernel -h > /dev/null
    fi
done
echo "warming base .."
find \$ENV_DIR/base/bin/ -type f | xargs -n 100 cat >/dev/null
echo "Done with kernel warmer ..."

# remove the script
rm -- $script
EOF
# run it in the background
bash $script & disown
## ----------------------------------------- ##