#!/bin/bash


# Setup Julia environment
mkdir -p $ENV_DIR && cd $ENV_DIR
JULIA_DIR=julia-${JULIA_VERSION}
curl -SsLO https://julialang-s3.julialang.org/bin/linux/x64/${JULIA_VERSION%.*}/${JULIA_DIR}-linux-x86_64.tar.gz
tar -xf ${JULIA_DIR}-linux-x86_64.tar.gz && rm ${JULIA_DIR}-linux-x86_64.tar.gz

# Add useful packages
julia -e 'import Pkg; Pkg.update(); Pkg.add(["FITSIO", "DataFrames", "Plots", "AstroLib", "AstroImages"]);'
julia -e 'import Pkg; Pkg.update(); Pkg.add(["IJulia"]); using IJulia;Pkg.precompile();'

# Setup the kernel
mv ~/.local/share/jupyter/kernels/julia-* $JUPYTER_DIR/share/jupyter/kernels
mkdir -p ${JULIA_DIR}/config

# Save the lock file
mkdir -p $LOCK_DIR/julia && cp $JULIA_PKGDIR/environments/*/*toml $LOCK_DIR/julia

cat <<'JRC' > ${JULIA_DIR}/config/juliarc.jl
push!(Libdl.DL_LOAD_PATH, joinpath(ENV["MAMBA_ROOT_PREFIX"], "lib"))
JRC

# fix the permission
fix-permissions $ENV_DIR/${JULIA_DIR}