import logging
import os
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

load_dotenv()

LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG").upper()
LOG_DIR = os.environ.get("LOG_DIR", "logs")
LOG_FILE = os.path.join(LOG_DIR, "energy_audit.log")

LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

_logger = logging.getLogger("energy_audit")


def _resolve_level() -> int:
    return LEVELS.get(LOG_LEVEL, logging.DEBUG)


def _build_formatter() -> logging.Formatter:
    return logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")


def _configure(logger_obj: logging.Logger, level: int) -> None:
    logger_obj.setLevel(level)
    logger_obj.handlers = []

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(_build_formatter())
    logger_obj.addHandler(stream_handler)

    os.makedirs(LOG_DIR, exist_ok=True)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(_build_formatter())
    logger_obj.addHandler(file_handler)

    logger_obj.propagate = False


def register_error_logger(app) -> None:
    level = _resolve_level()
    _configure(_logger, level)
    _configure(app.logger, level)

    _logger.debug("Logging initialized at level %s", LOG_LEVEL)
    _logger.debug("Log file: %s", LOG_FILE)
