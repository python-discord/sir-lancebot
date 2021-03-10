FROM python:3.9-slim

# Set pip to have cleaner logs and no saved cache
ENV PIP_NO_CACHE_DIR=false \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false

# Install git to be able to dowload git dependencies in the Pipfile
RUN apt-get -y update \
    && apt-get install -y \
        ffmpeg \
        gcc \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --user poetry
ENV PATH="${PATH}:/root/.local/bin"

WORKDIR /bot

COPY pyproject.toml poetry.lock /bot/

RUN poetry install --no-dev --no-interaction --no-ansi

# Set SHA build argument
ARG git_sha="development"
ENV GIT_SHA=$git_sha

COPY . .

CMD ["python", "-m", "bot"]

# Define docker persistent volumes
VOLUME /bot/bot/log /bot/data
