ARG BASE_TAG=latest
ARG REPOSITORY=ghcr.io/nasa-fornax/fornax-images

FROM ${REPOSITORY}/env-heasoft:${BASE_TAG} AS heasoft
FROM ${REPOSITORY}/fornax-base:${BASE_TAG}

COPY --chown=$NB_UID:$NB_GID --from=heasoft /opt/envs/heasoft /opt/envs/heasoft

# Install any uv/conda environments and call build-* scripts
RUN mkdir -p $HOME/build
COPY --chown=$NB_UID:$NB_GID install-* requirements-* conda-* $HOME/build/

RUN cd build \
 && chmod +x install-main_eSASS4dr1.sh \
 && ./install-main_eSASS4dr1.sh

LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax eROSITA eSASS Image"
LABEL org.opencontainers.image.authors="Fornax Project"

ENV DEFAULT_ENV=esassdr1