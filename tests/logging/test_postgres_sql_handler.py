"""Tests for the PostgresSQLHandler."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from src.logging.postgres_sql_handler import PostgresSQLHandler


@pytest.fixture
def mock_connector():
    """Create a mock database connector with a scoped session."""
    connector = MagicMock()
    session_mock = MagicMock()
    connector.ScopedSession.return_value = session_mock
    return connector


def test_handler_emit_success(mock_connector):
    """Verify that emit correctly maps LogRecord attributes to the AppLog model."""
    handler = PostgresSQLHandler(connector=mock_connector)

    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_path.py",
        lineno=10,
        msg="Test log message",
        args=(),
        exc_info=None,
    )
    record.meta = {"user_id": 123}
    record.session_id = "test-session-uuid"

    with patch("src.logging.postgres_sql_handler.AppLog") as MockAppLog:
        handler.emit(record)

        MockAppLog.assert_called_once_with(
            level="INFO",
            module="test_path",
            message="Test log message",
            meta={"user_id": 123},
            session_id="test-session-uuid",
        )

        session = mock_connector.ScopedSession()
        session.add.assert_called_once()
        session.commit.assert_called_once()
        mock_connector.ScopedSession.remove.assert_called_once()


def test_handler_emit_failure_triggers_rollback(mock_connector, caplog):
    """Verify that a database error triggers a rollback and logs the failure."""
    handler = PostgresSQLHandler(connector=mock_connector)
    session = mock_connector.ScopedSession()
    session.commit.side_effect = Exception("DB Connection Lost")

    record = logging.LogRecord("name", logging.ERROR, "path", 1, "msg", (), None)

    with caplog.at_level(logging.ERROR):
        handler.emit(record)

    session.rollback.assert_called_once()
    mock_connector.ScopedSession.remove.assert_called_once()

    assert "Logging to DB failed: DB Connection Lost" in caplog.text


def test_handler_handles_missing_attributes(mock_connector):
    """Verify handler works correctly even if meta or session_id are missing."""
    handler = PostgresSQLHandler(connector=mock_connector)
    record = logging.LogRecord("name", logging.INFO, "path", 1, "msg", (), None)

    with patch("src.logging.postgres_sql_handler.AppLog") as MockAppLog:
        handler.emit(record)

        kwargs = MockAppLog.call_args.kwargs
        assert kwargs["meta"] == {}
        assert kwargs["session_id"] is None
