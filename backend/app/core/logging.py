"""Structured logging configuration with OpenTelemetry trace ID propagation stubs."""

import logging
import sys
from typing import Any

import structlog


def configure_logging(json_logs: bool = False) -> None:
    """
    Configure structlog and stdlib logging for JSON or console output.

    OpenTelemetry trace context can be merged here when a full tracer is wired;
    for now, trace_id/span_id keys are accepted if present in the log event dict.

    Args:
        json_logs: When True, emit JSON lines suitable for log aggregators.
    """
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        _add_otel_stub_fields,
    ]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer() if not json_logs else structlog.processors.JSONRenderer(),
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def _add_otel_stub_fields(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """
    Stub processor reserving keys for OpenTelemetry trace correlation.

    When OpenTelemetry is enabled, a processor can inject trace_id and span_id;
    this stub documents the contract without importing optional SDK packages.
    """
    event_dict.setdefault("trace_id", None)
    event_dict.setdefault("span_id", None)
    return event_dict


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog-bound logger for the given module name."""
    return structlog.get_logger(name)
