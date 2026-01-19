FROM ghcr.io/astral-sh/uv:python3.13-bookworm

ARG BUILD_ENVIRONMENT=local
ARG APP_HOME=/app
ARG DEBIAN_FRONTEND=noninteractive
# ARG MULTIPLE_PYTHON  # Set to True if you want to use multiple Python versions

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BUILD_ENV=${BUILD_ENVIRONMENT}
ENV MULTIPLE_PYTHON=True
ENV PYTHONPATH="${APP_HOME}:${APP_HOME}/src:${PYTHONPATH:-}"
ENV DJANGO_SETTINGS_MODULE=example_project.settings

WORKDIR ${APP_HOME}
ENV PATH="/app/.venv/bin:$PATH"

# Install apt packages
RUN apt-get update
RUN apt-get install -y \
    # Some basic tools and libraries
    bash curl wget git make gcc libc6 \
    build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev \
    libsqlite3-dev llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev \
    libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev python3-pip

# Update pip
RUN pip install --upgrade pip cffi

# Install multiple Python versions with uv
RUN if [ "$MULTIPLE_PYTHON" = "True" ] ; then \
    uv python install 3.11; \
    uv python install 3.12; \
    uv python install 3.13; \
    uv python install 3.14; \
    fi

# Copy requirements files
COPY pyproject.toml uv.lock requirements.txt ${APP_HOME}/

# Copy remaining project files
COPY noxfile.py manage.py ${APP_HOME}
COPY .darglint .editorconfig .flake8 .gitignore .pre-commit-config.yaml .prettierignore .readthedocs.yml bandit.yml ${APP_HOME}
COPY CHANGELOG.md CODE_OF_CONDUCT.md CONTRIBUTING.md LICENSE README.md ${APP_HOME}
COPY ./docs/ ${APP_HOME}/docs
COPY ./example_project/ ${APP_HOME}/example_project/
COPY ./src/ ${APP_HOME}/src/

# Install dependencies using uv
RUN uv venv --python 3.13
RUN uv sync --extra dev --prerelease=allow

# Project initialization:
COPY ./compose/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

# Initialize git and add .
RUN git init
RUN git add .

ENTRYPOINT ["/entrypoint"]
