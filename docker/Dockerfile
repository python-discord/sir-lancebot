FROM python:3.7-alpine3.7
RUN apk add --update libffi-dev build-base git jpeg-dev zlib zlib-dev

RUN mkdir /bot
COPY . /bot
WORKDIR /bot

ENV LIBRARY_PATH="/lib:/usr/lib" \
    PIP_NO_CACHE_DIR="false" \
    PIPENV_DONT_USE_PYENV="1" \
    PIPENV_HIDE_EMOJIS="1" \
    PIPENV_IGNORE_VIRTUALENVS="1" \
    PIPENV_NOSPIN="1"

RUN pip install pipenv
RUN pipenv install --deploy --system

ENTRYPOINT ["python"]
CMD ["-m", "bot"]
