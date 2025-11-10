ARG BASE_TAG=latest
ARG REPOSITORY=nasa-fornax/fornax-images
ARG REGISTRY=ghcr.io

FROM ${REGISTRY}/${REPOSITORY}/jupyter-base:${BASE_TAG}

ARG SUPPORT_DATA_DIR=/data/

USER root
RUN mkdir -p $SUPPORT_DATA_DIR \
 && fix-permissions $SUPPORT_DATA_DIR
USER $NB_USER

COPY --chown=$NB_UID:$NB_GID data-*.sh /tmp/
RUN cd /tmp/ \
 ; for script in `ls data-*`; do \
 echo "Found script ${script} ..." \
 && chmod +x $script \
 && ./$script \
 ; done \
 && rm -rf data-*