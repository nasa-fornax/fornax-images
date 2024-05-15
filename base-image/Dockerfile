FROM jupyter/base-notebook:2023-04-17

LABEL org.opencontainers.image.source=https://github.com/fornax-navo/fornax-images
LABEL org.opencontainers.image.ref.name="Fornax Base Image"
LABEL org.opencontainers.image.version=0.1
LABEL maintainer="Fornax Project"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# copy anything we have so we can use it
COPY --chown=jovyan:jovyan . /home/jovyan


# Install OS packages and then clean up
USER root
RUN apt-get update --fix-missing > /dev/null \
    # Read apt.txt line by line, and execute apt-get install -y for each line in apt.txt
    && xargs -a apt.txt apt-get install -y \
    && apt-get clean \
    && apt-get -y autoremove \
    && rm -rf /var/lib/apt/lists/*
USER $NB_USER
# ------------------------------------ #

# if we have base-lock.txt, use it
RUN LOCKFILE="environment-lock.yml" ENVFILE="environment.yml" \
 && echo "Checking for lock or environment files" \
 ; if test -f $LOCKFILE; then \
 echo "Found $LOCKFILE, using it ..." \
 && echo "Found $LOCKFILE" > /tmp/tmp.txt \
 && mamba env update -n base --file $LOCKFILE \
 ; elif test -f $ENVFILE; then \
 echo "Found $ENVFILE, using it ..." > /tmp/tmp.txt \
 && echo "Found $ENVFILE" > /tmp/tmp.txt \
 && mamba env update -n base --file $ENVFILE \
 ; fi \
