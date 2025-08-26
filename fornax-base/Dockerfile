ARG BASE_TAG=latest
ARG REPOSITORY=nasa-fornax/fornax-images
ARG REGISTRY=ghcr.io

FROM ${REGISTRY}/${REPOSITORY}/jupyter-base:${BASE_TAG}

LABEL org.opencontainers.image.source=https://github.com/nasa-fornax/fornax-images
LABEL org.opencontainers.image.description="Fornax Base Image"
LABEL org.opencontainers.image.authors="Fornax Project"

ARG SUPPORT_DATA_MOUNT=/shared-storage/support-data


# Environment variables
ENV CACHE_DIR=/tmp/cache
ENV DEFAULT_ENV=python3 \
    LOCK_DIR=$ENV_DIR/lock \
    XDG_CACHE_HOME=$CACHE_DIR \
    XDG_CACHE_DIR=$CACHE_DIR \
    XDG_CACHE_DIR=$CACHE_DIR \
    PIP_CACHE_DIR=$CACHE_DIR/pip \
    UV_CACHE_DIR=$CACHE_DIR/uv \
    # for vscode
    CODE_EXECUTABLE=code-server \
    NOTEBOOK_DIR=/opt/notebooks \
    # support data; JH can pass ARG SUPPORT_DATA_MOUNT; SUPPORT_DATA_DIR points to it
    # scripts that rely on support data should use SUPPORT_DATA_DIR
    SUPPORT_DATA_DIR=/opt/support-data \
    # path
    PATH=$ENV_DIR/base/bin:$PATH:$ENV_DIR/other/code-server/bin \
    # For firefly
    FIREFLY_URL=https://irsa.ipac.caltech.edu/irsaviewer


# Copy our jupyter settings overrides
USER root
RUN mkdir -p $JUPYTER_DIR/share/jupyter/lab/settings/ \
 # Disable the announcement extension
 && jupyter labextension disable "@jupyterlab/apputils-extension:announcements"
COPY --chown=$NB_UID:$NB_GID overrides.json $JUPYTER_DIR/share/jupyter/lab/settings/

# Copy our scripts
COPY --chmod=0777 --chown=$NB_UID:$NB_GID scripts/*.sh update-notebooks.sh link-notebooks.sh /usr/local/bin/
USER $NB_USER


# add packages to jupyter environment; mainly labextensions
COPY --chown=$NB_UID:$NB_GID jupyter-requirements.txt /tmp/
RUN export VIRTUAL_ENV=$JUPYTER_DIR \
 && uv pip install --no-cache -r /tmp/jupyter-requirements.txt \
 # get the latest fornax-labextension
 && curl -s "https://api.github.com/repos/nasa-fornax/fornax-labextension/releases/latest" -o /tmp/latest.json \
 && whlurl=`python -c "import json; d = json.loads(open('/tmp/latest.json').read()); print(d['assets'][0]['browser_download_url'])"` \
 && whlfile=`basename $whlurl` \
 && curl -sSLO $whlurl \
 && uv pip install --no-cache ./$whlfile \
 && rm -rf $whlfile jupyter-requirements.txt latest.json \
 && uv cache clean \
 # update lock file and make a copy in LOCK_DIR
 && uv pip list --format=freeze > $JUPYTER_DIR/requirements-jupyter.txt \
 && mkdir -p $LOCK_DIR \
 && cp $JUPYTER_DIR/requirements-jupyter.txt $LOCK_DIR/requirements-jupyter.txt

# Install system packages with micromamba
# we use microconda instead of apt, so they are portable
COPY --chown=$NB_UID:$NB_GID base.txt /tmp/
RUN micromamba create -y -p $ENV_DIR/base python=$PYTHON_VERSION \
 && xargs -a /tmp/base.txt micromamba install -y -p $ENV_DIR/base \
 && micromamba clean -yaf && rm /tmp/base.txt \
 && micromamba env export -p $ENV_DIR/base > $ENV_DIR/base/base-lock.yml \
 && cp $ENV_DIR/base/base-lock.yml $LOCK_DIR/

## install DEFAULT_ENV ##
COPY --chown=$NB_UID:$NB_GID requirements-$DEFAULT_ENV.txt /tmp/
RUN cd /tmp/ && bash /usr/local/bin/uv-env-install.sh \
 # fix the display name of DEFAULT_ENV
 && $ENV_DIR/$DEFAULT_ENV/bin/python -m ipykernel install --name $DEFAULT_ENV \
    --prefix $JUPYTER_DIR --display-name "$DEFAULT_ENV"
## ------------------- ##


# Make $DEFAULT_ENV default; do it at the global level
# because ~/.bashrc is not loaded when user space is mounted
# Also, add it to before-notebook.d main script
USER root
RUN echo "if [ -f \$ENV_DIR/\$DEFAULT_ENV/bin/activate ]; then" > /tmp/activate.sh \
 && echo "  echo activating python in \$ENV_DIR/\$DEFAULT_ENV" >> /tmp/activate.sh \
 && echo "  source \$ENV_DIR/\$DEFAULT_ENV/bin/activate" >> /tmp/activate.sh \
 && echo "elif [ -d \$ENV_DIR/\$DEFAULT_ENV/conda-meta ]; then" >> /tmp/activate.sh \
 && echo "  echo activating python in \$ENV_DIR/\$DEFAULT_ENV" >> /tmp/activate.sh \
 && echo "  micromamba activate \$DEFAULT_ENV" >> /tmp/activate.sh \
 && echo "else" >> /tmp/activate.sh \
 && echo "  echo DEFAULT_ENV=\$DEFAULT_ENV not found" >> /tmp/activate.sh \
 && echo "fi" >> /tmp/activate.sh \
 && echo "" >> /tmp/activate.sh \
 && cat /tmp/activate.sh >> /etc/bash.bashrc \
 && cat /tmp/activate.sh  >> /usr/local/bin/before-notebook.d/10activate-env.sh \
 && echo "bash /usr/local/bin/link-notebooks.sh" > /usr/local/bin/before-notebook.d/20link-notebooks.sh \
 && rm -r /tmp/* $HOME/.*

# reset user and location
WORKDIR ${HOME}
USER $NB_USER


# For outside mount when using outside fornax
RUN mkdir -p /opt/workspace
VOLUME /opt/workspace

# landing page; even an empty one
COPY --chown=$NB_UID:$NB_GID --chmod=644 introduction.md* $JUPYTER_DIR
RUN cd $JUPYTER_DIR \
    && if test -f introduction.md; then \
      pandoc introduction.md -o introduction.html --standalone --metadata title="Welcome to Fornax Science Console!"; \
    fi

# Add the notebooks to the image
RUN update-notebooks.sh && link-notebooks.sh


# Support data location; SUPPORT_DATA_DIR -> SUPPORT_DATA_MOUNT
# SUPPORT_DATA_MOUNT can be set by JH
RUN ln -s $SUPPORT_DATA_MOUNT $SUPPORT_DATA_DIR

# ==== Start ONBUILD commands ==== #
# These commands run in images the inherit fornax-images
# ================================ #

# Install OS packages and then clean up
ONBUILD RUN mkdir -p $HOME/build
ONBUILD COPY --chown=$NB_UID:$NB_GID apt* base* build-* requirements-* conda-* $HOME/build/
ONBUILD USER root
ONBUILD RUN cd build \
         && if test -f apt.txt; then \
            xargs bash /usr/local/bin/apt-install.sh; \
            rm apt.txt; \
         fi
ONBUILD USER $NB_USER
ONBUILD RUN cd build \
         && if test -f base.txt; then \
            xargs -a base.txt micromamba install -y -p $ENV_DIR/base; \
            micromamba clean -yaf ; rm base.txt; \
         fi
# ------------------------------------ #


# # setup uv environments
ONBUILD RUN cd build && bash /usr/local/bin/uv-env-install.sh \
 && bash /usr/local/bin/conda-env-install.sh
# # ----------------------- #

# Any other build-* scripts; e.g. build tractor, heasoft etc #
ONBUILD RUN cd build \
 ; for script in `ls build-*`; do \
 echo "Found script ${script} ..." \
 && chmod +x $script \
 && ./$script \
 ; done
# --------------------------- #


ONBUILD RUN rm -r $HOME/build
ONBUILD USER ${NB_USER}
ONBUILD WORKDIR ${HOME}
