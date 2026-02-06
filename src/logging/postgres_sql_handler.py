"""Custom logging handler to write logs to a PostgresSQL database using SQLAlchemy."""

import logging

from src.logging.database_tables import AppLog
from src.logging.log_database_connector import LogDatabaseConnector

logger = logging.getLogger("app.postgres_sql_handler")


class PostgresSQLHandler(logging.Handler):
    """Logging handler to write log records to a PostgresSQL database."""

    def __init__(self, connector: LogDatabaseConnector) -> None:
        """Initialize the PostgresSQLHandler.

        Args:
            connector: An instance of LogDatabaseConnector for database operations.

        """
        super().__init__()
        self.connector = connector

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to the PostgresSQL database.

        Args:
            record: The log record to be written to the database.

        """
        self._write_to_db(record)

    def _write_to_db(self, record: logging.LogRecord) -> None:
        """Write the log record to the database.

        Args:
            record: The log record to be written to the database.

        """
        session = self.connector.ScopedSession()
        try:
            log_entry = AppLog(
                level=record.levelname,
                module=record.module,
                message=record.getMessage(),
                meta=getattr(record, "meta", {}),
                session_id=getattr(record, "session_id", None),
            )
            session.add(log_entry)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Logging to DB failed: {e}")
        finally:
            self.connector.ScopedSession.remove()
