ARG BASE_TAG=latest
ARG REPOSITORY=ghcr.io/nasa-fornax/fornax-images

FROM ${REPOSITORY}/env-heasoft:${BASE_TAG} AS heasoft
FROM ${REPOSITORY}/fornax-base:${BASE_TAG}

LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax XMM SAS Image"
LABEL org.opencontainers.image.authors="Fornax Project"

ENV DEFAULT_ENV=sas

COPY --from=heasoft /opt/envs/heasoft /opt/envs/heasoft
