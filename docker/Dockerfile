FROM python:3.7-alpine3.7
RUN apk add --update libffi-dev tini build-base git jpeg-dev zlib zlib-dev

RUN mkdir /bot
COPY . /bot
WORKDIR /bot

ENV LIBRARY_PATH=/lib:/usr/lib \
    PIPENV_VENV_IN_PROJECT=1

RUN pip install pipenv
RUN pipenv install --deploy --system

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["python", "-m", "bot"]
