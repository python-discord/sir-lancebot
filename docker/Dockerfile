FROM python:3.7.2-alpine3.9

ENTRYPOINT ["python"]
CMD ["-m", "bot"]

ENV PIP_NO_CACHE_DIR="false" \
    PIPENV_DONT_USE_PYENV="1" \
    PIPENV_HIDE_EMOJIS="1" \
    PIPENV_IGNORE_VIRTUALENVS="1" \
    PIPENV_NOSPIN="1"

RUN apk add --no-cache --update \
        build-base \
        git \
        libffi-dev \
        libwebp-dev \
        # Pillow dependencies
        freetype-dev \
        libjpeg-turbo-dev \
        zlib-dev
RUN pip install pipenv

COPY . /bot
WORKDIR /bot

RUN pipenv install --deploy --system
