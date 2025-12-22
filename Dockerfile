FROM python:3.11-slim

WORKDIR /app

COPY ./src /app/src
ENV PYTHONPATH=/app

RUN mkdir -p /app/logs && chmod -R 777 /app/logs
RUN pip install --no-cache-dir -r /app/src/requirements.txt

EXPOSE 8080

CMD ["python", "/app/src/webui.py"]
