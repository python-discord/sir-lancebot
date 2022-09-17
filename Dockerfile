FROM --platform=linux/amd64 ghcr.io/chrislovering/python-poetry-base:3.9-slim

# Install dependencies
WORKDIR /bot
COPY pyproject.toml poetry.lock ./
RUN poetry install --without dev

# Set SHA build argument
ARG git_sha="development"
ENV GIT_SHA=$git_sha

# Copy the rest of the project code
COPY . .

# Start the bot
ENTRYPOINT ["poetry", "run"]
CMD ["python", "-m", "bot"]
