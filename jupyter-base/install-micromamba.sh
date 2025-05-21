#!/usr/bin/bash

cd /tmp
set -x
arch=$(uname -m)
if [ "${arch}" = "x86_64" ]; then
    # Should be simpler, see <https://github.com/mamba-org/mamba/issues/1437>
    arch="64";
fi

# https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html#linux-and-macos
wget --progress=dot:giga -O - \
    "https://micro.mamba.pm/api/micromamba/linux-${arch}/latest" | tar -xvj bin/micromamba

PYTHON_SPECIFIER="python=${PYTHON_VERSION}"
if [[ "${PYTHON_VERSION}" == "default" ]]; then PYTHON_SPECIFIER="python"; fi

# Install the packages
./bin/micromamba install \
    --root-prefix="${CONDA_DIR}" \
    --prefix="${CONDA_DIR}" \
    --yes \
    'conda' \
    'mamba' \
    "${PYTHON_SPECIFIER}"
rm -rf /tmp/bin/

# Pin major.minor version of python
# https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-pkgs.html#preventing-packages-from-updating-pinning
mamba list --full-name 'python' | awk 'END{sub("[^.]*$", "*", $2); print $1 " " $2}' >> "${CONDA_DIR}/conda-meta/pinned"
# Temporarily pin libxml2 to avoid ABI breakage
# https://github.com/conda-forge/libxml2-feedstock/issues/145
echo 'libxml2<2.14.0' >> /opt/conda/conda-meta/pinned
mamba clean --all -f -y
fix-permissions "${CONDA_DIR}"
fix-permissions "/home/${NB_USER}"

# default condarc
printf """
auto_update_conda: false
show_channel_urls: true
channels:
    - conda-forge
pkgs_dirs:
    - /tmp/cache/conda
""" >> ${CONDA_DIR}/.condarc

# clean
mamba clean -yaf
pip cache purge
find ${CONDA_DIR} -follow -type f -name '*.a' -name '*.pyc' -delete
find ${CONDA_DIR} -follow -type f -name '*.js.map' -delete