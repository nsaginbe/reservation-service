FROM python:3.13-slim AS base

## Base setup
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1
ENV PYTHONUNBUFFERED 1
ENV ROOT /app
ENV PYTHONPATH "${PYTHONPATH}:/app/src/"

WORKDIR $ROOT

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

# Poetry configs
RUN poetry config virtualenvs.create false

# Install packages
COPY pyproject.toml poetry.lock $ROOT/
RUN poetry install --without dev
# Install Playwright browsers with system deps
RUN python -m playwright install --with-deps chromium

# Add commands
COPY docker/commands $ROOT/commands
RUN chmod +x $ROOT/commands/* && sed -i 's/\r$//' $ROOT/commands/*
ENV PATH="$ROOT/commands:$PATH"


FROM base AS dev

## Base setup
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1
ENV PYTHONUNBUFFERED 1
ENV ROOT /app
ENV PYTHONPATH "${PYTHONPATH}:/app/src/"

WORKDIR $ROOT

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install packages
RUN poetry install --with dev
# Ensure Playwright browsers are available in dev images too
RUN python -m playwright install --with-deps chromium

CMD [ "bash", "-l" ]


FROM base AS app

## Base setup
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1
ENV PYTHONUNBUFFERED 1
ENV ROOT /app
ENV PYTHONPATH "${PYTHONPATH}:/app/src/"

COPY src $ROOT/src

WORKDIR $ROOT

CMD [ "start.sh" ]
