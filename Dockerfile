FROM ubuntu:24.04

WORKDIR /app
COPY .src/ /app/src/

RUN python3 -m pip install /app/src/requirements.txt