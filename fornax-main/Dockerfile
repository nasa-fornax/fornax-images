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

# add julia to path
ENV PATH=$ENV_DIR/julia/bin:$PATH \
    JULIA_DEPOT_PATH=$ENV_DIR/julia \
    JULIAUP_DEPOT_PATH=$ENV_DIR/julia
RUN curl -fsSL https://install.julialang.org | sh -s -- -y -p $ENV_DIR/julia/ \
 # add julia kernel
 && julia -e 'using Pkg; Pkg.add("IJulia")' \
 && mv ~/.local/share/jupyter/kernels/julia-* $JUPYTER_DIR/share/jupyter/kernels \
 && fix-permissions $JULIA_DEPOT_PATH
