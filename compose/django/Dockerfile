FROM python:3.11-slim

ARG BUILD_ENVIRONMENT=local
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV BUILD_ENV ${BUILD_ENVIRONMENT}

# Install apt packages
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update \
    && apt-get --no-install-recommends install -y \
    # dependencies for building Python packages
    build-essential \
    # psycopg dependencies
    libpq-dev \
    # needed for psql
    postgresql-client \
    # cleaning up unused files
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install psycopg-binary ipdb poetry

WORKDIR ${APP_HOME}
COPY poetry.lock pyproject.toml ${APP_HOME}
COPY ./src/* ${APP_HOME}/src/

# Project initialization:
RUN --mount=type=cache,target=/root/.cache/poetry \
    poetry config virtualenvs.create false && poetry install --with dev --no-interaction --no-ansi --no-root

# copy application files
COPY ./pytest.ini ${APP_HOME}
COPY ./manage.py ${APP_HOME}
COPY ./tests/* ${APP_HOME}
COPY ./compose/* ${APP_HOME}

COPY ./compose/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

ENTRYPOINT ["/entrypoint"]
