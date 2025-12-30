from __future__ import annotations

import json
import logging
import random
import time
from logging import config as logging_config
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(level: str = "INFO") -> None:
    logging_config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": JsonFormatter,
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                }
            },
            "root": {
                "handlers": ["default"],
                "level": level,
            },
        }
    )


def log_event(
    logger: logging.Logger,
    event: str,
    *,
    level: str = "info",
    sample_rate: float = 1.0,
    **fields: Any,
) -> None:
    if sample_rate < 1.0 and random.random() > sample_rate:
        return
    fields.setdefault("ts", int(time.time() * 1000))
    payload = {"event": event, **fields}
    message = json.dumps(payload, ensure_ascii=True)
    log_fn = getattr(logger, level, logger.info)
    log_fn(message)
