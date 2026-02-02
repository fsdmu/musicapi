"""Database table definitions for logging application events optimized for Grafana visualization."""

import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase
import logging

logger = logging.getLogger("app.log_db_tables")


class LogBase(DeclarativeBase):
    """Base class for logging declarative models."""
    pass

class AppLog(LogBase):
    """Model for application logs optimized for Grafana."""
    __tablename__ = "app_logs"

    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    log_time = sa.Column(
        sa.DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False
    )
    level = sa.Column(
        sa.Enum("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", name="log_level"),
        nullable=False,
        index=True
    )
    module = sa.Column(sa.String(50), nullable=False)
    message = sa.Column(sa.Text, nullable=False)

    meta = sa.Column(JSONB, nullable=True)

    session_id = sa.Column(sa.String(36), nullable=True, index=True)