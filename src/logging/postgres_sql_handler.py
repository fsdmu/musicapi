import logging

from src.logging.log_database_connector import LogDatabaseConnector

from src.logging.database_tables import AppLog

logger = logging.getLogger("app.postgres_sql_handler")


class PostgresSQLHandler(logging.Handler):
    def __init__(self, connector: LogDatabaseConnector) -> None:
        super().__init__()
        self.connector = connector

    def emit(self, record: logging.LogRecord) -> None:
        self._write_to_db(record)

    def _write_to_db(self, record: logging.LogRecord) -> None:
        session = self.connector.ScopedSession()
        try:
            log_entry = AppLog(
                level=record.levelname,
                module=record.module,
                message=record.getMessage(),
                meta=getattr(record, 'meta', {}),
                session_id=getattr(record, 'session_id', None)
            )
            session.add(log_entry)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Logging to DB failed: {e}")
        finally:
            self.connector.ScopedSession.remove()
