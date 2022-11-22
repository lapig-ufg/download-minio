###############################################
# Base Image
###############################################
FROM python:3.10-slim as python-base

ENV LAPIG_ENV='dev' \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.0.5 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    VENV_PATH="/opt/pysetup/.venv"\
    PYTHONBREAKPOINT="web_pdb.set_trace" \
    GEOS_VERSION=3.10.4 \
    PROJ_VERSION=9.1.0 \
    PROJ_INCLUDE_DIR=/usr/include \
    GDAL_VERSION=3.6.0

ARG PYSETUP_PATH="/opt/pysetup" 

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

###############################################################
#Initial Image

RUN apt-get update && apt-get install --no-install-recommends -y \
            bzip2 \
            g++ \
            cmake \
            libsqlite3-dev \ 
            sqlite3 \
            libtiff-dev \
            libssl-dev \
            libcurl4-openssl-dev \
            curl \
            pkg-config \
            libtiff5-dev \
            libpq-dev postgresql \
            make \
            gcc \
            wget && \
        wget http://download.osgeo.org/geos/geos-${GEOS_VERSION}.tar.bz2 -P /tmp/resources/ && \
            cd /tmp/resources && \
            tar xjf geos-${GEOS_VERSION}.tar.bz2 && \
            cd geos-${GEOS_VERSION} && \
            ./configure  && \
            make -j24 install && \
        wget https://download.osgeo.org/proj/proj-${PROJ_VERSION}.tar.gz -P /tmp/resources/ && \
            cd /tmp/resources && \
            tar xfv proj-${PROJ_VERSION}.tar.gz && \
            cd proj-${PROJ_VERSION} && \
            mkdir build && \
            cd build && \
            cmake .. -DCMAKE_INSTALL_PREFIX=/usr && \
            cmake --build . --parallel 24 && \ 
            cmake --build . --target install && \ 
        apt-get update && apt-get -y install \
            libproj-dev \
            libgeos++-dev \
            libproj-dev \
            python3-dev \
            libgeos-dev &&\
        cd /tmp && \
            wget download.osgeo.org/gdal/${GDAL_VERSION}/gdal-${GDAL_VERSION}.tar.gz && \
            tar xfv gdal-${GDAL_VERSION}.tar.gz  && \
            cd gdal-${GDAL_VERSION} && \
            cp -rvp /usr/include/proj.h /usr/lib && cp -rvp /usr/include/proj.h /usr/local && \
            mkdir build &&\
            cd build &&\
            cmake .. -DCMAKE_INSTALL_PREFIX=/usr &&\
            cmake --build . --parallel 24 && \
            cmake --build . --target install 

FROM python:3.10-slim as builder-base


RUN apt-get update && apt-get install --no-install-recommends -y curl build-essential libpq-dev libpq5

# install poetry - respects $POETRY_VERSION & $POETRY_HOME
RUN pip3 install poetry 

# copy project requirement files here to ensure they will be cached.
WORKDIR $PYSETUP_PATH
COPY poetry.lock pyproject.toml ./

# install runtime deps - uses $POETRY_VIRTUALENVS_IN_PROJECT internally
RUN poetry install --only main --no-interaction --no-ansi

###############################################
# Production Image
###############################################
FROM python-base as production
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH


WORKDIR /APP

COPY ./ssh /root/.ssh 
COPY ./entrypoint.sh /APP


RUN apt-get update && \
    apt-get install -y git make build-essential libpq-dev libpq5 && \
    mkdir -p /APP && cd /APP && \
    rm -rf /var/lib/apt/lists/* && \
    chmod +x /APP/entrypoint.sh

ENTRYPOINT [ "/APP/entrypoint.sh"]
