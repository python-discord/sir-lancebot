FROM python:3.7-alpine3.7

COPY . /bot
WORKDIR /bot

ENV LIBRARY_PATH="/lib:/usr/lib" \
    PIP_NO_CACHE_DIR="false" \
    POETRY_INSTALLER="https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py"

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
    && wget -O- $POETRY_INSTALLER | python - -y \
    && ~/.poetry/bin/poetry config settings.virtualenvs.create false \
    && ~/.poetry/bin/poetry install --no-dev \
    \
    && rm -rf ~/.poetry \
    && apk del .build-deps

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["python", "-m", "bot"]
