FROM python:3.7-alpine3.7

COPY . /bot
WORKDIR /bot

ENV LIBRARY_PATH=/lib:/usr/lib

RUN set -euxo pipefail \
    && apk add --update \
        build-base \
        git \
        libffi-dev \
        tini \
        # Pillow dependencies
        freetype-dev \
        jpeg-dev \
        zlib \
        zlib-dev \
    && pip install poetry \
    && poetry config settings.virtualenvs.create false \
    && poetry install --no-dev

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["python", "-m", "bot"]
