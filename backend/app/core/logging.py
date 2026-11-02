import logging
import sys
from contextvars import ContextVar
from datetime import datetime

# Context variable for request correlation ID
request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Returns the current request ID from context."""
    return request_id_ctx_var.get()


def set_request_id(req_id: str) -> None:
    """Sets the current request ID in context."""
    request_id_ctx_var.set(req_id)


class StructuredLogFormatter(logging.Formatter):
    """
    Production-grade structured log formatter.
    Outputs readable structured logs with request_id correlation.
    """

    def format(self, record: logging.LogRecord) -> str:
        req_id = get_request_id()
        iso_time = datetime.utcfromtimestamp(record.created).isoformat() + "Z"

        # Build structured message
        req_str = f" [req_id={req_id}]" if req_id else ""
        log_line = f"{iso_time} [{record.levelname}] {record.name}{req_str}: {record.getMessage()}"

        if record.exc_info:
            log_line += "\n" + self.formatException(record.exc_info)

        return log_line


def setup_logging(log_level: str = "INFO"):
    """Configures application-wide structured logging."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicate log outputs
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(StructuredLogFormatter())

    root_logger.addHandler(console_handler)

    # Suppress overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
