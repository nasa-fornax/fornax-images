# ONBUILD instructions in base-image/Dockerfile are used to
# perform certain actions based on the presence of specific
# files (such as conda-linux-64.lock, start) in this repo.
# Refer to the base-image/Dockerfile for documentation.
ARG BASE_TAG=latest
ARG REPOSITORY=nasa-fornax/fornax-images
ARG REGISTRY=ghcr.io

FROM ${REGISTRY}/${REPOSITORY}/fornax-base:${BASE_TAG}

LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax Main Astronomy Image"
LABEL org.opencontainers.image.authors="Fornax Project"

# setup julia
ARG JULIA_VERSION=1.8.0
ENV JULIA_DEPOT_PATH=$ENV_DIR/julia-$JULIA_VERSION \
    JULIA_PKGDIR=$ENV_DIR/julia-$JULIA_VERSION \
    PATH=$ENV_DIR/julia-$JULIA_VERSION/bin:$PATH
RUN mkdir -p $ENV_DIR && cd $ENV_DIR \
 && JULIA_DIR=julia-${JULIA_VERSION} \
 && curl -SsLO https://julialang-s3.julialang.org/bin/linux/x64/${JULIA_VERSION%.*}/${JULIA_DIR}-linux-x86_64.tar.gz \
 && tar -xf ${JULIA_DIR}-linux-x86_64.tar.gz && rm ${JULIA_DIR}-linux-x86_64.tar.gz \
 && julia -e 'import Pkg; Pkg.update(); Pkg.add(["IJulia"]); using IJulia;Pkg.precompile();' \
 && mv ~/.local/share/jupyter/kernels/julia-* $JUPYTER_DIR/share/jupyter/kernels \
 && mkdir -p ${JULIA_DIR}/config \
 && cat <<'JRC' > ${JULIA_DIR}/config/juliarc.jl && fix-permissions $ENV_DIR/${JULIA_DIR}
push!(Libdl.DL_LOAD_PATH, joinpath(ENV["MAMBA_ROOT_PREFIX"], "lib"))
JRC