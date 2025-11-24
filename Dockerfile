FROM python:3.12

COPY ./src/ /app/src/
WORKDIR /app

RUN python -m pip install -r /app/src/requirements.txt