FROM python:3.12

COPY ./src/ /app/src/
WORKDIR /app

EXPOSE 8080

RUN python -m pip install -r /app/src/requirements.txt
CMD ["python", "/app/src/webui.py"]