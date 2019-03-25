FROM python:3.7-alpine3.7

ENV LIBRARY_PATH="/lib:/usr/lib" \
    PIP_NO_CACHE_DIR="false" \
    PIPENV_DONT_USE_PYENV="1" \
    PIPENV_HIDE_EMOJIS="1" \
    PIPENV_IGNORE_VIRTUALENVS="1" \
    PIPENV_NOSPIN="1"

RUN apk add --no-cache --update \
        build-base \
        git \
        libffi-dev \
        # Pillow dependencies
        freetype-dev \
        libjpeg-turbo-dev \
        zlib-dev

RUN mkdir /bot
COPY . /bot
WORKDIR /bot

RUN pip install pipenv
RUN pipenv install --deploy --system

ENTRYPOINT ["python"]
CMD ["-m", "bot"]
