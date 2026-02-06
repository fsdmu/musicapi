"""Database connector for managing PostgresSQL logging database."""

import logging
import os

import sqlalchemy as sa
from sqlalchemy.orm import scoped_session, sessionmaker

logger = logging.getLogger("app.log_db_connector")


class LogDatabaseConnector:
    """Database connector for managing logging database."""

    def __init__(self):
        """Initialize the DatabaseConnector."""
        self.engine = self._get_engine()
        # sessionmaker creates a factory for database sessions
        self.session_factory = sessionmaker(bind=self.engine)
        # scoped_session ensures thread-safety for the logging handler
        self.ScopedSession = scoped_session(self.session_factory)

        try:
            with self.engine.connect() as conn:
                conn.execute(sa.text("SELECT 1"))
            logger.info("Successfully connected to the logging database.")
        except Exception as e:
            logger.error(f"Failed to connect to the logging database: {e}")
            raise

    @staticmethod
    def _sanitize_env_val(v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        return v.replace("\n", "").replace("\r", "").replace("\t", "")

    @staticmethod
    def _get_engine() -> sa.Engine:
        """Create and return a PostgresSQL SQLAlchemy engine using environment variables.

        Returns:
            A SQLAlchemy Engine instance.

        Raises:
            RuntimeError: If any required environment variables are missing or if the
                password is not set.

        """
        from urllib.parse import quote_plus

        user = LogDatabaseConnector._sanitize_env_val(os.environ.get("LOG_DB_USER"))
        password = LogDatabaseConnector._sanitize_env_val(
            os.environ.get("LOG_DB_PASSWORD")
        )
        host = LogDatabaseConnector._sanitize_env_val(os.environ.get("LOG_DB_HOST"))
        port = LogDatabaseConnector._sanitize_env_val(os.environ.get("LOG_DB_PORT"))
        db_name = LogDatabaseConnector._sanitize_env_val(os.environ.get("LOG_DB_NAME"))

        missing = [
            k
            for k, v in {
                "LOG_DB_USER": user,
                "LOG_DB_PASSWORD": password,
                "LOG_DB_HOST": host,
                "LOG_DB_PORT": port,
                "LOG_DB_NAME": db_name,
            }.items()
            if not v
        ]

        if missing:
            raise RuntimeError(
                f"Logging DB environment variables missing: {', '.join(missing)}"
            )

        password_quoted = quote_plus(password)  # type: ignore
        url = f"postgresql://{user}:{password_quoted}@{host}:{port}/{db_name}"
        return sa.create_engine(url, pool_pre_ping=True)
