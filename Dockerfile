FROM bitnami/python:3.7-prod

ENV PIP_NO_CACHE_DIR=false \
    PIPENV_HIDE_EMOJIS=1 \
    PIPENV_IGNORE_VIRTUALENVS=1 \
    PIPENV_NOSPIN=1

WORKDIR /bot
COPY . .

# Update setuptools by removing egg first, add other dependencies
RUN rm -r /opt/bitnami/python/lib/python3.*/site-packages/setuptools* && \
    pip install --no-cache-dir -U setuptools pipenv
RUN pipenv install --deploy --system

ENTRYPOINT ["python"]
CMD ["-m", "bot"]

VOLUME /bot/bot/log
VOLUME /bot/data
