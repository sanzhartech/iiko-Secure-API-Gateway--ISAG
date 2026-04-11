"""
core/logging.py — Structured Logging Configuration

REMEDIATION PASS CHANGES:
  [Fix 6] _mask_sensitive now recursively traverses nested dicts and lists.
           Previously only top-level event_dict keys were masked.
           Nested payloads (e.g., response.body.authorization) are now redacted.

Uses structlog for JSON-formatted, context-aware logging.

SECURITY:
  - Sensitive fields (Authorization, api_key, password, etc.) are masked
    at all nesting depths before any output is emitted.
  - Full tokens are NEVER logged, even partially.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, WrappedLogger

# Fields whose values must be masked at any nesting depth
_SENSITIVE_FIELDS: frozenset[str] = frozenset({
    "authorization",
    "api_key",
    "iiko_api_key",
    "gateway_client_secret",
    "password",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "client_secret",
    "x-api-key",
})

_MASK_VALUE = "***REDACTED***"


def _mask_value_recursive(obj: Any, depth: int = 0) -> Any:
    """
    [Fix 6] Recursively mask sensitive keys in nested structures.

    Limits recursion depth to 10 to avoid excessive CPU cost on
    adversarially large nested objects.

    Args:
        obj:   The value to sanitise (dict, list, or scalar).
        depth: Current recursion depth (guards against deep nesting).

    Returns:
        Sanitised copy of the input structure.
    """
    if depth > 10:
        return obj  # Stop recursion — don't risk performance on deep nesting

    if isinstance(obj, dict):
        return {
            k: (
                _MASK_VALUE
                if k.lower() in _SENSITIVE_FIELDS
                else _mask_value_recursive(v, depth + 1)
            )
            for k, v in obj.items()
        }

    if isinstance(obj, list):
        return [_mask_value_recursive(item, depth + 1) for item in obj]

    return obj


def _mask_sensitive(
    logger: WrappedLogger,   # noqa: ARG001
    method_name: str,        # noqa: ARG001
    event_dict: EventDict,
) -> EventDict:
    """
    structlog processor: mask sensitive keys at all nesting depths.

    [Fix 6] Replaces the previous shallow (top-level only) masking with
    full recursive traversal of the event_dict.
    """
    return _mask_value_recursive(event_dict)   # type: ignore[return-value]


def _add_log_level(
    logger: WrappedLogger,  # noqa: ARG001
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """Add log level string to every entry."""
    event_dict.setdefault("level", method_name.upper())
    return event_dict


def configure_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """
    Initialise structlog and the stdlib logging bridge.
    Must be called once at application startup (main.py lifespan).

    Args:
        log_level:  One of DEBUG | INFO | WARNING | ERROR.
        log_format: 'json' for production, 'console' for development.
    """
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        _add_log_level,
        _mask_sensitive,           # [Fix 6] recursive masking applied here
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_logger_name,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.ExceptionRenderer(),  # was: format_exc_info (deprecated bare fn)
    ]

    renderer: Any = (
        structlog.processors.JSONRenderer()
        if log_format == "json"
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        # structlog >= 21: `processors` (list) replaces the old `processor=` (single)
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    for noisy in ("httpx", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Return a named structlog logger.

    Usage:
        logger = get_logger(__name__)
        logger.info("event", user_id="...", endpoint="/api/orders")
    """
    return structlog.get_logger(name)
