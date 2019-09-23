FROM python:3.7-slim

# Set pip to have cleaner logs and no saved cache
ENV PIP_NO_CACHE_DIR=false \
    PIPENV_HIDE_EMOJIS=1 \
    PIPENV_IGNORE_VIRTUALENVS=1 \
    PIPENV_NOSPIN=1

# Install pipenv
RUN pip install -U pipenv

# Copy the project files into working directory
WORKDIR /bot
COPY . .

# Install project dependencies
RUN pipenv install --deploy --system

ENTRYPOINT ["python"]
CMD ["-m", "bot"]

# Define docker persistent volumes
VOLUME /bot/bot/log
VOLUME /bot/data
