ARG BASE_TAG=latest
ARG REPOSITORY=ghcr.io/nasa-fornax/fornax-images

FROM ${REPOSITORY}/env-heasoft:${BASE_TAG} AS env_heasoft
FROM ${REPOSITORY}/env-ciao:${BASE_TAG} AS env_ciao
FROM ${REPOSITORY}/env-fermi:${BASE_TAG} AS env_fermi
FROM ${REPOSITORY}/env-sas:${BASE_TAG} AS env_sas
FROM ${REPOSITORY}/fornax-jupyter:${BASE_TAG}


LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax High Energy Image"
LABEL org.opencontainers.image.authors="Fornax Project"

# where the data is mounted
ARG SUPPORT_DATA_MOUNT=/shared-storage/support-data


# Copy from env-heasoft #
RUN --mount=type=bind,from=env_heasoft,source=/opt/,target=/tmp/opt \
    cp -a /tmp/opt/envs/heasoft /opt/envs/ \
 && cp -a /tmp/opt/envs/lock/heasoft-lock.yml /opt/envs/lock/ \
 && cp -a /tmp/opt/envs/lock/build-env-heasoft /opt/envs/lock/ \
 && cp -a /tmp/opt/jupyter/share/jupyter/kernels/heasoft /opt/jupyter/share/jupyter/kernels/

RUN --mount=type=bind,from=env_heasoft,source=$SUPPORT_DATA_MOUNT/,target=/tmp/$SUPPORT_DATA_MOUNT \
    cp -a /tmp/$SUPPORT_DATA_MOUNT/heasoft-* $SUPPORT_DATA_MOUNT/
 

ENV DEFAULT_ENV=heasoft
# ------------------- #

# Copy from env-ciao #
RUN --mount=type=bind,from=env_ciao,source=/opt/,target=/tmp/opt \
    cp -r /tmp/opt/envs/ciao /opt/envs/ \
 && cp -r /tmp/opt/envs/lock/ciao-lock.yml /opt/envs/lock/ \
 && cp -r /tmp/opt/envs/lock/build-env-ciao /opt/envs/lock/ \
 && cp -r /tmp/opt/jupyter/share/jupyter/kernels/ciao /opt/jupyter/share/jupyter/kernels/

RUN --mount=type=bind,from=env_ciao,source=$SUPPORT_DATA_MOUNT/,target=/tmp/$SUPPORT_DATA_MOUNT \
    cp -a /tmp/$SUPPORT_DATA_MOUNT/ciao-* $SUPPORT_DATA_MOUNT/
# ------------------- #

# Copy from env-fermi #
RUN --mount=type=bind,from=env_fermi,source=/opt/,target=/tmp/opt \
    cp -r /tmp/opt/envs/fermi /opt/envs/ \
 && cp -r /tmp/opt/envs/lock/fermi-lock.yml /opt/envs/lock/ \
 && cp -r /tmp/opt/envs/lock/build-env-fermi /opt/envs/lock/ \
 && cp -r /tmp/opt/jupyter/share/jupyter/kernels/fermi /opt/jupyter/share/jupyter/kernels/

RUN --mount=type=bind,from=env_fermi,source=$SUPPORT_DATA_MOUNT/,target=/tmp/$SUPPORT_DATA_MOUNT \
    cp -a /tmp/$SUPPORT_DATA_MOUNT/fermitools-* $SUPPORT_DATA_MOUNT/
# ------------------- #

# Copy from env-sas #
RUN --mount=type=bind,from=env_sas,source=/opt/,target=/tmp/opt \
    cp -r /tmp/opt/envs/sas /opt/envs/ \
 && cp -r /tmp/opt/envs/lock/sas-lock.yml /opt/envs/lock/ \
 && cp -r /tmp/opt/envs/lock/build-env-sas /opt/envs/lock/ \
 && cp -r /tmp/opt/jupyter/share/jupyter/kernels/sas /opt/jupyter/share/jupyter/kernels/ 

RUN --mount=type=bind,from=env_sas,source=$SUPPORT_DATA_MOUNT/,target=/tmp/$SUPPORT_DATA_MOUNT \
    cp -a /tmp/$SUPPORT_DATA_MOUNT/xmmsas-* $SUPPORT_DATA_MOUNT/
# ------------------- #
