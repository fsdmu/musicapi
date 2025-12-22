FROM python:3.12

COPY ./src/ /app/src/
WORKDIR /app

# ensure logs dir exists and provide default log location
ENV LOG_FILE=/app/logs/musicapi.log
RUN mkdir -p /app/logs

EXPOSE 8080

RUN python -m pip install -r /app/requirements.txt
CMD ["python", "/app/src/webui.py"]