"""Tests for the event logger utility functions and decorators."""

import asyncio
from unittest.mock import patch

import pytest

from src.logging.event_logger import (
    _SENSITIVE_INDICATORS,
    _clean_args,
    _get_clean_params,
    _get_env_redact_values,
    _mask_value,
    _redact,
    _safe_serialize,
    generate_session_id,
    log_event,
)


def test_mask_value_short():
    """Verify that short strings are fully masked."""
    assert _mask_value("123") == "***"
    assert _mask_value("123456") == "******"


def test_mask_value_long():
    """Verify that long strings show only the start and end characters."""
    # Should show first 3 and last 3: "pas***ord"
    result = _mask_value("password")
    assert result.startswith("pas")
    assert result.endswith("ord")
    assert "*" in result


def test_mask_value_non_string():
    """Verify that non-string values are returned unchanged."""

    class Broken:
        def __str__(self):
            raise ValueError("I am broken")

    assert _mask_value(12345) == "*****"
    assert _mask_value(None) == "****"
    assert _mask_value(Broken()) == "***REDACTED***"


@patch("inspect.signature")
def test_clean_args(mock_signature):
    """Verify that clean_args correctly filters and renames arguments."""
    mock_signature.return_value.parameters = {
        "self": None,
        "arg1": None,
        "arg2": None,
        "arg3": None,
    }

    class SampleClass:
        def sample_func(self, arg1, arg2, arg3):
            pass

        def sample_cls(cls, arg1, arg2, arg3):
            pass

    args = ("self", "value1", "value2", "value3")

    result = _clean_args(SampleClass.sample_func, args)
    result_cls = _clean_args(SampleClass.sample_cls, args)
    assert result == {"arg1": "value1", "arg2": "value2", "arg3": "value3"}
    assert result_cls == {"arg1": "value1", "arg2": "value2", "arg3": "value3"}


def test_generate_session_id():
    """Verify that generated session IDs are valid non-empty strings."""
    session_id = generate_session_id()
    assert isinstance(session_id, str)
    assert len(session_id) > 0


def test_safe_serialize_redaction():
    """Verifies that sensitive keys in dictionaries are masked and normalized."""
    data = {
        "User": "felix",
        "PASSWORD": "super-secret-password",
        "api_key": "123456789",
    }
    serialized = _safe_serialize(data)

    # Check normalization to lowercase
    assert "user" in serialized
    assert serialized["user"] == "felix"

    # Check masking (D401 compliant phrasing: "Ensure sensitive data is masked")
    assert "password" in serialized
    assert serialized["password"] != "super-secret-password"
    assert serialized["password"].startswith("sup")

    assert "api_key" in serialized
    assert serialized["api_key"] != "123456789"


def test_safe_serialize_broken_str():
    """Verifies that objects with broken __str__ methods are handled correctly."""

    class ExplodingKey:
        def __hash__(self):
            return 123

        def __eq__(self, other):
            return isinstance(other, ExplodingKey)

        def __str__(self):
            raise RuntimeError("I refuse to be a string!")

    data = {"normal": "value", ExplodingKey(): "broken_value"}
    serialized = _safe_serialize(data)

    assert serialized["normal"] == "value"

    broken_key = next(k for k in serialized.keys() if "unparseable_ref_" in k)
    assert serialized[broken_key] == "broken_value"


def test_safe_serialize_nested_structures():
    """Verifies that serialization works recursively for nested lists and dicts."""
    data = {
        "outer": {"inner_secret": "hidden", "list": [1, {"secret_item": "hide_me"}]}
    }
    serialized = _safe_serialize(data)

    # Verifies deep nesting
    assert serialized["outer"]["inner_secret"] != "hidden"
    assert serialized["outer"]["list"][1]["secret_item"] != "hide_me"
    assert serialized["outer"]["list"][0] == 1


def test_safe_serialize_unserializable_repr():
    """Verifies fallback when an object has a broken __repr__."""

    class TotalMeltdown:
        def __repr__(self):
            raise Exception("Total failure")

    assert _safe_serialize(TotalMeltdown()) == "<unserializable>"


@pytest.mark.asyncio
async def test_async_log_event_decorator(caplog):
    """Verifies that the async decorator logs start and end events."""
    caplog.set_level("INFO")

    @log_event("async_event")
    async def async_sample(x, session_id=None):
        return x * 2

    result = await async_sample(5, session_id="async-session")

    assert result == 10
    assert "async_event.start" in caplog.text
    assert "async_event.end" in caplog.text


def test_log_event_error(caplog):
    """Verifies that exceptions are caught and logged as errors."""
    caplog.set_level("ERROR")

    @log_event("fail_event")
    def faulty_func():
        raise ValueError("Something went wrong")

    with pytest.raises(ValueError, match="Something went wrong"):
        faulty_func()

    assert "fail_event.error" in caplog.text


@pytest.mark.parametrize(
    "value,expected",
    [
        ({"key": "value"}, {"key": "value"}),
        ({1, 2, 3}, {1, 2, 3}),
        (12345, 12345),
        ("sensitive_value456789", "[REDACTED]456789"),
        ("sensitive_value", "[REDACTED]"),
        ("short", "short"),
        (None, None),
    ],
)
def test_redact(value, expected):
    """Verifies that the redact function masks sensitive information."""
    with patch("src.logging.event_logger._REDACT_VALUES", {"sensitive_value"}):
        result = _redact(value)
        assert result == expected


def test_get_env_redact_values():
    """Verifies that environment variables are correctly added to the redact list."""
    env = {}

    for indicator in _SENSITIVE_INDICATORS:
        env[f"TEST_{indicator.upper()}"] = f"test_{indicator}_value"

    with patch.dict("os.environ", env):
        redact_values = _get_env_redact_values()

        for indicator in _SENSITIVE_INDICATORS:
            assert f"test_{indicator}_value" in redact_values


def test_get_clean_params_success():
    """Verifies that parameters are correctly bound and mapped to their names."""

    def sample_func(a, b, c=3):
        pass

    args = (1,)
    kwargs = {"b": 2}

    params = _get_clean_params(sample_func, args, kwargs)

    assert params["a"] == 1
    assert params["b"] == 2
    assert params["c"] == 3  # Check that apply_defaults() worked


def test_get_clean_params_excludes_self():
    """Verify that 'self' is not included in params when calling bound methods."""

    class MockClass:
        def method(self, x):
            pass

    obj = MockClass()
    # For a bound method (obj.method), Python has already handled 'self'.
    # We only pass 'x'.
    args = (10,)
    kwargs = {}

    params = _get_clean_params(obj.method, args, kwargs)

    assert "x" in params
    assert params["x"] == 10
    assert "self" not in params


def test_get_clean_params_bind_error():
    """Verifies fallback when arguments do not match the function signature."""

    def strict_func(a, b):
        pass

    # Missing required argument 'b'
    args = (1,)
    kwargs = {}

    params = _get_clean_params(strict_func, args, kwargs)

    assert "error" in params
    assert params["error"] == "Could not bind arguments"


def test_get_clean_params_var_args():
    """Verifies handling of variable arguments (*args and **kwargs)."""

    def var_func(a, *args, **kwargs):
        pass

    args = (1, 2, 3)
    kwargs = {"extra": "data"}

    params = _get_clean_params(var_func, args, kwargs)

    assert params["a"] == 1
    assert params["args"] == (2, 3)
    assert params["kwargs"] == {"extra": "data"}


def test_sync_wrapper_logs_and_returns(caplog):
    """Verify that the sync wrapper logs start/end and preserves return values."""
    caplog.set_level("INFO")

    @log_event("sync_op")
    def identity(value, session_id=None):
        """Simple identity function."""
        return value

    result = identity("hello", session_id="sync-123")

    assert result == "hello"
    # Filter for our specific event logs
    events = [r for r in caplog.records if "sync_op" in r.msg]
    assert len(events) == 2

    assert events[0].msg == "sync_op.start"
    assert events[0].session_id == "sync-123"
    assert events[0].meta["payload"]["value"] == "hello"

    assert events[1].msg == "sync_op.end"
    assert events[1].meta["payload"]["result"] == "hello"


@pytest.mark.asyncio
async def test_async_wrapper_logs_and_returns(caplog):
    """Verify that the async wrapper handles awaits and logs correctly."""
    caplog.set_level("INFO")

    @log_event("async_op")
    async def async_identity(value, session_id=None):
        """Simple async identity function."""
        await asyncio.sleep(0.01)
        return value

    result = await async_identity("world", session_id="async-456")

    assert result == "world"
    events = [r for r in caplog.records if "async_op" in r.msg]
    assert len(events) == 2
    assert events[0].msg == "async_op.start"
    assert events[1].msg == "async_op.end"
    assert events[1].session_id == "async-456"


def test_wrapper_exception_logging(caplog):
    """Verify that exceptions are logged with traceback and re-raised."""
    caplog.set_level("ERROR")

    @log_event("fail_op")
    def fail(session_id=None):
        """Function that always fails."""
        raise ValueError("Intentional failure")

    with pytest.raises(ValueError, match="Intentional failure"):
        fail(session_id="fail-789")

    # Check that the exception was logged
    error_log = next(r for r in caplog.records if r.msg == "fail_op.error")
    assert error_log.levelname == "ERROR"
    assert error_log.session_id == "fail-789"
    assert error_log.meta["payload"]["error"] == "Intentional failure"


def test_wrapper_generates_default_session(caplog):
    """Verify that a session_id is generated if not provided in kwargs."""
    caplog.set_level("INFO")

    @log_event("gen_session")
    def no_session_func():
        return True

    no_session_func()

    # The record should have an automatically generated UUID-style string
    assert hasattr(caplog.records[0], "session_id")
    assert len(caplog.records[0].session_id) == 36  # Length of a standard UUID


def test_wrapper_preserves_metadata():
    """Verify that functools.wraps preserves the original function metadata."""

    @log_event("meta_check")
    def original_func():
        """Original docstring."""
        return None

    assert original_func.__name__ == "original_func"
    assert original_func.__doc__ == "Original docstring."


def test_log_event_sync_exception(caplog):
    """Verify sync wrapper logs exceptions with meta and re-raises."""
    caplog.set_level("ERROR")

    @log_event("sync_fail")
    def crashing_func():
        raise ValueError("Sync Crash")

    # 1. Verify the exception is re-raised (raise)
    with pytest.raises(ValueError, match="Sync Crash"):
        crashing_func()

    # 2. Verify the log record (logger.exception)
    error_records = [r for r in caplog.records if r.levelname == "ERROR"]
    assert len(error_records) == 1

    record = error_records[0]
    assert record.msg == "sync_fail.error"
    assert record.session_id is not None
    assert record.meta["name"] == "test_log_event_sync_exception.<locals>.crashing_func"
    assert record.meta["payload"]["error"] == "Sync Crash"


@pytest.mark.asyncio
async def test_log_event_async_exception(caplog):
    """Verify async wrapper logs exceptions and re-raises."""
    caplog.set_level("ERROR")

    @log_event("async_fail")
    async def crashing_async_func():
        await asyncio.sleep(0)
        raise RuntimeError("Async Crash")

    with pytest.raises(RuntimeError, match="Async Crash"):
        await crashing_async_func()

    error_record = next(r for r in caplog.records if r.msg == "async_fail.error")
    assert error_record.meta["payload"]["error"] == "Async Crash"
