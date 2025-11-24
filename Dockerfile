FROM python:3.12.12:latest

WORKDIR /app
COPY .src/ /app/src/

RUN python3 -m pip install /app/src/requirements.txt