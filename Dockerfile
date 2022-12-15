###############################################
# Base Image
###############################################
FROM registry.lapig.iesa.ufg.br/lapig-images-prod/download-minio:base as python-base

ENV LAPIG_ENV="production" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.0.5 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"\
    PYTHONBREAKPOINT="web_pdb.set_trace"

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"
###############################################
# Builder Image
###############################################
FROM python-base as builder-base
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

# Clone app and npm install on server
ENV URL_TO_APPLICATION_GITHUB="https://github.com/lapig-ufg/download-minio.git"
ENV BRANCH="develop"

RUN apt-get update && \
    apt-get install -y git make libpq-dev libpq5 && \
    mkdir -p /APP && cd /APP && \
    git clone -b ${BRANCH} ${URL_TO_APPLICATION_GITHUB} && \
    rm -rf /var/lib/apt/lists/* && chmod +x /APP/download-minio/start.sh

CMD sh -c "cd /APP/download-minio && python creat_cach_mapfile.py && gunicorn -k  uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080 -w 32 -t 0 app.server:app"
