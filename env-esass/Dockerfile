ARG BASE_TAG=latest
ARG REPOSITORY=ghcr.io/nasa-fornax/fornax-images

FROM ${REPOSITORY}/env-heasoft:${BASE_TAG} AS heasoft
FROM ${REPOSITORY}/fornax-base:${BASE_TAG}

COPY --chown=$NB_UID:$NB_GID --from=heasoft /opt/envs/heasoft /opt/envs/heasoft
# This will leave the HEASoft kernel definition in the image (it is required for the eSASS build script)
#  but that should be fine because the we manually set which kernels to copy in the fornax-hea build script,
#  so there is no risk of collision with the 'real' heasoft kernel.
COPY --chown=$NB_UID:$NB_GID --from=heasoft /opt/jupyter/share/jupyter/kernels/heasoft /opt/jupyter/share/jupyter/kernels/heasoft

# Install any uv/conda environments and call build-* scripts
RUN mkdir -p $HOME/build
COPY --chown=$NB_UID:$NB_GID install-* requirements-* conda-* $HOME/build/


RUN cd build && echo "Found script install-main_eSASS4dr1.sh ..." \ \
 && chmod +x install-main_eSASS4dr1.sh \
 && ./install-main_eSASS4dr1.sh

LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax eROSITA eSASS Image"
LABEL org.opencontainers.image.authors="Fornax Project"

ENV DEFAULT_ENV=esassdr1