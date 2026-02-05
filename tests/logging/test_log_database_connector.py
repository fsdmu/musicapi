"""Tests for the LogDatabaseConnector."""

import os
from unittest.mock import patch

import pytest
import sqlalchemy as sa

from src.logging.log_database_connector import LogDatabaseConnector


def test_sanitize_env_val():
    """Verify that environment values are stripped of whitespace and newlines."""
    assert LogDatabaseConnector._sanitize_env_val("  user123  \n") == "user123"
    assert LogDatabaseConnector._sanitize_env_val(None) is None
    assert LogDatabaseConnector._sanitize_env_val("host\r\t") == "host"


@patch.dict(
    os.environ,
    {
        "LOG_DB_USER": "test_user",
        "LOG_DB_PASSWORD": "p@ssword!",
        "LOG_DB_HOST": "localhost",
        "LOG_DB_PORT": "5432",
        "LOG_DB_NAME": "logs",
    },
)
def test_get_engine_success():
    """Verify engine creation and password URL encoding."""
    engine = LogDatabaseConnector._get_engine()

    assert engine.url.username == "test_user"
    assert engine.url.password == "p@ssword!"

    rendered_url = engine.url.render_as_string(hide_password=False)

    assert "p%40ssword%21" in rendered_url
    assert "test_user" in rendered_url


def test_get_engine_missing_vars():
    """Verify RuntimeError is raised when environment variables are missing."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(
            RuntimeError, match="Logging DB environment variables missing"
        ):
            LogDatabaseConnector._get_engine()


def test_connector_init_success(caplog):
    """Verify successful initialization and thread-safe session creation."""
    test_engine = sa.create_engine("sqlite:///:memory:", poolclass=sa.pool.StaticPool)

    with (
        patch.object(LogDatabaseConnector, "_get_engine", return_value=test_engine),
        caplog.at_level("INFO"),
    ):
        connector = LogDatabaseConnector()

        assert connector.engine == test_engine
        assert "Successfully connected" in caplog.text

        # Test that ScopedSession works
        session = connector.ScopedSession()
        assert session is not None
        connector.ScopedSession.remove()


def test_connector_init_failure(caplog):
    """Verify that initialization fails if the database is unreachable."""
    # Create an engine that will fail on connection
    test_engine = sa.create_engine(
        "postgresql://invalid_user:invalid@localhost/nonexistent"
    )

    with (
        patch.object(LogDatabaseConnector, "_get_engine", return_value=test_engine),
        caplog.at_level("ERROR"),
    ):
        # SQLAlchemy won't actually try to connect until engine.connect() is called
        # which happens in your __init__
        with pytest.raises(Exception):
            LogDatabaseConnector()

        assert "Failed to connect to the logging database" in caplog.text
