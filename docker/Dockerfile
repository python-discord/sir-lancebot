FROM python:3.7-alpine3.7

COPY . /bot
WORKDIR /bot

ENV LIBRARY_PATH="/lib:/usr/lib" \
    PIP_NO_CACHE_DIR="false" \

RUN set -euxo pipefail \
    && apk add --no-cache --update --virtual .build-deps \
        build-base \
        git \
        libffi-dev \
    && apk add --no-cache --update \
        tini \
        # Pillow dependencies
        freetype-dev \
        libjpeg-turbo-dev \
        zlib-dev \
    \
    # Upgrade pip to get fix pypa/pip#6219
    && pip install -U pip \
    && pip install poetry \
    && poetry config settings.virtualenvs.create false \
    && poetry install --no-dev \
    \
    && apk del .build-deps

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["python", "-m", "bot"]
