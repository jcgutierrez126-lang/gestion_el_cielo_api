import json
import logging
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """
    Formateador de logs en JSON estructurado.
    Cada linea de log es un JSON valido — compatible con Azure Monitor / Application Insights.

    Formato:
    {
        "timestamp": "2026-03-18T21:00:00.000Z",
        "level": "INFO",
        "service": "cielo-api",
        "module": "graph_search_service",
        "correlation_id": "abc-123",
        "message": "...",
        "extra": {...}
    }
    """

    SERVICE_NAME = "cielo-api"

    def format(self, record: logging.LogRecord) -> str:
        from cieloapi.middleware import get_correlation_id

        log_entry = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level": record.levelname,
            "service": self.SERVICE_NAME,
            "module": record.module,
            "correlation_id": get_correlation_id(),
            "message": record.getMessage(),
        }

        # Agregar info de excepcion si existe
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Agregar campos extra si los hay (ej: logger.info("msg", extra={"pedido": "123"}))
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
            }:
                log_entry[key] = value

        return json.dumps(log_entry, ensure_ascii=False, default=str)
