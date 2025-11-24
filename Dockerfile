FROM ubuntu:24.04

COPY ./src/ /app/src/
WORKDIR /app

RUN python -m pip install /app/src/requirements.txt