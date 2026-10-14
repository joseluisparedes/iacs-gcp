import json
import logging
import sys
from typing import Any, Dict


class CloudLoggingFormatter(logging.Formatter):
    """
    Formateador de logs estructurados en JSON compatible con Google Cloud Logging.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "timestamp": self.formatTime(record, self.datefmt),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id
        return json.dumps(log_entry)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CloudLoggingFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]

    # Reducir verbosidad de uvicorn access
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
