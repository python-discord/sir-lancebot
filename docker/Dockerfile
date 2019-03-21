FROM python:3.7-alpine3.7
RUN apk add --update libffi-dev tini build-base git jpeg-dev zlib zlib-dev freetype-dev

RUN mkdir /bot
COPY . /bot
WORKDIR /bot

ENV LIBRARY_PATH=/lib:/usr/lib

RUN pip install poetry
RUN poetry config settings.virtualenvs.create false
RUN poetry install

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["python", "-m", "bot"]
