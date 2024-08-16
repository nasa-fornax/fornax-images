# ONBUILD instructions in base-image/Dockerfile are used to
# perform certain actions based on the presence of specific
# files (such as conda-linux-64.lock, start) in this repo.
# Refer to the base-image/Dockerfile for documentation.
ARG IMAGE_TAG=latest
FROM fornax/base-image:${IMAGE_TAG}

# set default conda env
ENV CONDA_ENV=heasoft

USER root
RUN mamba run -n $CONDA_ENV python -m ipykernel install --sys-prefix --name $CONDA_ENV
USER $NB_USER