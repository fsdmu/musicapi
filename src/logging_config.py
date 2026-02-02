"""Logging configuration for the music API project."""
import queue

import logging
import os
from logging.handlers import RotatingFileHandler, QueueListener, QueueHandler

from src.logging.log_database_connector import LogDatabaseConnector
from src.logging.postgres_sql_handler import PostgresSQLHandler

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "musicapi.log")

_listener: QueueListener | None = None
log_queue = queue.Queue(-1)

def setup_logging(db_connector: LogDatabaseConnector = None):
    global _listener

    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    root_logger.setLevel(logging.INFO)

    quiet_loggers = [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "nicegui",
        "sqlalchemy.engine",
        "starlette",
        "httpcore",
        "httpx"
    ]

    for logger_name in quiet_loggers:
        ql = logging.getLogger(logger_name)
        ql.setLevel(logging.WARNING)
        ql.propagate = False
        ql.handlers = []

    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False

    # 1. Formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    # 2. File Handler
    if not any(isinstance(h, RotatingFileHandler) for h in app_logger.handlers):
        file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=3)
        file_handler.setFormatter(formatter)
        app_logger.addHandler(file_handler)

    # 3. Console Handler
    if not any(isinstance(h, logging.StreamHandler) for h in app_logger.handlers):
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        app_logger.addHandler(console)

    # 4. PostgreSQL Handler
    if db_connector:
        db_handler = PostgresSQLHandler(db_connector)
        _listener = QueueListener(log_queue, db_handler)
        _listener.start()

        q_handler = QueueHandler(log_queue)
        app_logger.addHandler(q_handler)

    return app_logger


def stop_logging():
    """Stop the logging listener if it exists."""
    global _listener
    if _listener:
        _listener.stop()
