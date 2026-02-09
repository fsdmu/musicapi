"""Utility functions and decorators for logging with sensitive data handling."""

import functools
import inspect
import logging
import os
import time
import uuid
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("app.event")
_SENSITIVE_INDICATORS = {"pass", "secret", "token", "key", "credential", "auth", "pwd"}


def _get_env_redact_values() -> set[str]:
    """Extract sensitive environment variable values for redaction.

    Returns:
        A set of sensitive values from environment variables.

    """
    return set(
        v
        for k, v in os.environ.items()
        if any(s.lower() in k.lower() for s in _SENSITIVE_INDICATORS)
    )


_REDACT_VALUES = _get_env_redact_values()


def _mask_value(val: Any) -> str:
    """Generic Mask used for sensitive values."""  # ignore: D401
    try:
        s = str(val)
        if len(s) <= 6:
            return "*" * len(s)
        return s[:3] + "*" * (len(s) - 6) + s[-3:]
    except Exception:
        return "***REDACTED***"


def _clean_args(func: Callable, args: tuple[Any, ...]) -> dict[str, Any]:
    """Clean function arguments for logging.

    Args:
        func: The function whose arguments are being cleaned.
        args: The positional arguments passed to the function.

    Returns:
        A dictionary of cleaned arguments suitable for logging.

    """
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())

    clean_dict = {}
    for i, arg in enumerate(args):
        if i < len(params) and params[i] in ("self", "cls"):
            continue

        if isinstance(arg, (str, int, float, bool, list, dict)) or arg is None:
            name = params[i] if i < len(params) else f"arg_{i}"
            clean_dict[name] = arg

    return clean_dict


def generate_session_id() -> str:
    """Generate a unique trace ID using UUID4.

    Returns:
        A string representation of the UUID4.

    """
    return str(uuid.uuid4())


def _make_meta(
    event_type: str, name: str, payload: dict[str, Any] | None = None
) -> dict[str, str | dict]:
    """Create structured meta information for logging.

    Args:
        event_type: The type of the event (e.g., function name).
        name: The name of the event (e.g., function qualified name).
        payload: Additional data to include in the meta.

    Returns:
        A dictionary containing the structured meta information.

    """
    return {
        "event_type": event_type,
        "name": name,
        "payload": _safe_serialize(payload),
    }


def _redact(value: str) -> str:
    """Redact sensitive environment values or substrings in a string."""
    if not isinstance(value, str):
        return value
    for r_str in _REDACT_VALUES:
        if r_str and r_str in value:
            value = value.replace(r_str, "[REDACTED]")
    return value


def _safe_serialize(obj: Any) -> Any:
    """Safely serializes an object and redacts sensitive information.

    Args:
        obj: The object to serialize.

    Returns:
        A serialized representation of the object suitable for logging.
    """
    if obj is None:
        return None
    if isinstance(obj, (int, float, bool)):
        return obj
    if isinstance(obj, str):
        return _redact(obj)

    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            try:
                key_str = str(k).lower()
            except Exception:
                key_str = f"unparseable_ref_{id(k)}"

            if any(ind in key_str for ind in _SENSITIVE_INDICATORS):
                out[key_str] = _mask_value(v)
            else:
                out[key_str] = _safe_serialize(v)
        return out

    if isinstance(obj, (list, tuple, set)):
        return [_safe_serialize(x) for x in obj]

    try:
        return repr(obj)
    except Exception:
        return "<unserializable>"


def _get_clean_params(
    func: Callable, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> dict[str, Any]:
    """Extract and clean function parameters for logging.

    Args:
        func: The function whose parameters are being extracted.
        args: The positional arguments passed to the function.
        kwargs: The keyword arguments passed to the function.

    Returns:
        A dictionary of cleaned parameters suitable for logging.

    """
    sig = inspect.signature(func)
    try:
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        params = dict(bound_args.arguments)

        params.pop("self", None)
        params.pop("cls", None)
        return params
    except Exception:
        return {"error": "Could not bind arguments"}


# noqa: D401
def log_event(event_name: str = "event") -> Callable:
    """Decorator to log the start, end, and errors of a function execution.

    Args:
        event_name: The base name of the event to log.

    Returns:
        A decorator that wraps the target function for logging.

    """

    # noqa: D401
    def decorator(func: Callable) -> Callable:
        """The decorator function.

        Args:
            func: The function to be decorated.

        Returns:
            The wrapped function with logging.

        """

        def _get_common_data(args, kwargs):
            """Extract common data like session_id and cleaned parameters.

            Args:
                args: Positional arguments passed to the function.
                kwargs: Keyword arguments passed to the function.

            Returns:
                A tuple of (session_id, cleaned parameters).

            """
            session_id = kwargs.get("session_id", generate_session_id())
            params = _get_clean_params(func, args, kwargs)
            return session_id, params

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                """Async wrapper for logging function execution.

                Args:
                    *args: Positional arguments.
                    **kwargs: Keyword arguments.

                Returns:
                    The result of the function execution.

                """
                session_id, params = _get_common_data(args, kwargs)
                start_time = time.perf_counter()

                logger.info(
                    f"{event_name}.start",
                    extra={
                        "meta": _make_meta(event_name, func.__qualname__, params),
                        "session_id": session_id,
                    },
                )
                try:
                    result = await func(*args, **kwargs)
                    duration = time.perf_counter() - start_time
                    logger.info(
                        f"{event_name}.end",
                        extra={
                            "meta": _make_meta(
                                event_name,
                                func.__qualname__,
                                {"result": result, "duration_sec": round(duration, 4)},
                            ),
                            "session_id": session_id,
                        },
                    )
                    return result
                except Exception as e:
                    logger.exception(
                        f"{event_name}.error",
                        extra={
                            "meta": _make_meta(
                                event_name, func.__qualname__, {"error": str(e)}
                            ),
                            "session_id": session_id,
                        },
                    )
                    raise

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                """Sync wrapper for logging function execution.

                Args:
                    *args: Positional arguments.
                    **kwargs: Keyword arguments.

                Returns:
                    The result of the function execution.

                """
                session_id, params = _get_common_data(args, kwargs)
                start_time = time.perf_counter()

                logger.info(
                    f"{event_name}.start",
                    extra={
                        "meta": _make_meta(event_name, func.__qualname__, params),
                        "session_id": session_id,
                    },
                )
                try:
                    result = func(*args, **kwargs)
                    duration = time.perf_counter() - start_time
                    logger.info(
                        f"{event_name}.end",
                        extra={
                            "meta": _make_meta(
                                event_name,
                                func.__qualname__,
                                {"result": result, "duration_sec": round(duration, 4)},
                            ),
                            "session_id": session_id,
                        },
                    )
                    return result
                except Exception as e:
                    logger.exception(
                        f"{event_name}.error",
                        extra={
                            "meta": _make_meta(
                                event_name, func.__qualname__, {"error": str(e)}
                            ),
                            "session_id": session_id,
                        },
                    )
                    raise

            return sync_wrapper

    return decorator
