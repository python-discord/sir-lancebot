FROM --platform=linux/amd64 python:3.9-slim

# Set pip to have cleaner logs and no saved cache
ENV PIP_NO_CACHE_DIR=false \
    POETRY_VIRTUALENVS_CREATE=false

# Install Poetry
RUN pip install --upgrade poetry

WORKDIR /bot

# Copy dependencies and lockfile
COPY pyproject.toml poetry.lock /bot/

# Install dependencies and lockfile, excluding development
# dependencies,
RUN poetry install --no-dev --no-interaction --no-ansi

# Set SHA build argument
ARG git_sha="development"
ENV GIT_SHA=$git_sha

# Copy the rest of the project code
COPY . .

# Start the bot
CMD ["python", "-m", "bot"]
