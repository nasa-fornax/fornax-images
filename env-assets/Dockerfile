# Kernel holder to help fornax-jupyter to avoid downloading the images
# with every build

ARG BASE_TAG=latest
ARG REPOSITORY=ghcr.io/nasa-fornax/fornax-images

FROM ${REPOSITORY}/env-core:${BASE_TAG} AS env_core
FROM ${REPOSITORY}/env-heasoft:${BASE_TAG} AS env_heasoft
FROM ${REPOSITORY}/env-ciao:${BASE_TAG} AS env_ciao
FROM ${REPOSITORY}/env-sas:${BASE_TAG} AS env_sas
FROM ${REPOSITORY}/env-fermi:${BASE_TAG} AS env_fermi
FROM ${REPOSITORY}/fornax-nb:${BASE_TAG} AS fornax_nb
FROM ${REPOSITORY}/archive-nb:${BASE_TAG} AS archive_nb

FROM scratch

ENV NOTEBOOK_DIR=/opt/notebooks
ENV KERNEL_DIR=/opt/jupyter/share/jupyter/kernels
ENV LOCK_DIR=/opt/envs/lock

# Add the notebooks
COPY --from=fornax_nb $NOTEBOOK_DIR $NOTEBOOK_DIR
COPY --from=archive_nb $NOTEBOOK_DIR $NOTEBOOK_DIR

# Kernels
COPY --from=env_heasoft $KERNEL_DIR /kernels/
COPY --from=env_ciao $KERNEL_DIR /kernels/
COPY --from=env_sas $KERNEL_DIR /kernels/
COPY --from=env_fermi $KERNEL_DIR /kernels/
COPY --from=fornax_nb $KERNEL_DIR /kernels/
COPY --from=archive_nb $KERNEL_DIR /kernels/
# keep env_core last because it has base
COPY --from=env_core $KERNEL_DIR /kernels/

# Locks
COPY --from=env_heasoft $LOCK_DIR /locks/
COPY --from=env_ciao $LOCK_DIR /locks/
COPY --from=env_sas $LOCK_DIR /locks/
COPY --from=env_fermi $LOCK_DIR /locks/
COPY --from=fornax_nb $LOCK_DIR /locks/
COPY --from=archive_nb $LOCK_DIR /locks/
COPY --from=env_core $LOCK_DIR /locks/