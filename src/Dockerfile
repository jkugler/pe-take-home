FROM ubuntu:20.04

ENV STATIC_URL /static
ENV STATIC_PATH /app/static

USER root

RUN apt-get update -y
RUN apt-get dist-upgrade -y

RUN apt-get install -y gunicorn python3-flask python3-flask-api

COPY . /app

RUN /usr/bin/python3 -m compileall /app/

WORKDIR /app

EXPOSE 8080

ENTRYPOINT ["/usr/bin/gunicorn3", "--bind", ":8080", "--workers", "4", "--chdir", "/app", "main:app"]
