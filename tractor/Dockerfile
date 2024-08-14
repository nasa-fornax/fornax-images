# ONBUILD instructions in base-image/Dockerfile are used to
# perform certain actions based on the presence of specific
# files (such as conda-linux-64.lock, start) in this repo.
# Refer to the base-image/Dockerfile for documentation.
LABEL org.opencontainers.image.ref.name="Fornax Tractor Image"
LABEL org.opencontainers.image.version=0.2
LABEL maintainer="Fornax Project"

ARG IMAGE_TAG=latest
FROM fornax/base-image:${IMAGE_TAG}
