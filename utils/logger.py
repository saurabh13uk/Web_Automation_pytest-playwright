import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


_FORMATTER = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
_LOGGERS: dict[str, logging.Logger] = {}
_LOG_FILE: Path | None = None


def configure_logging(log_file: str | Path, level: int = logging.INFO) -> None:
    global _LOG_FILE
    _LOG_FILE = Path(log_file)
    _LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    for logger in _LOGGERS.values():
        _attach_handlers(logger, level)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if name in _LOGGERS:
        return logger

    _LOGGERS[name] = logger
    _attach_handlers(logger, logging.INFO)
    return logger


def _attach_handlers(logger: logging.Logger, level: int) -> None:
    logger.handlers.clear()
    logger.setLevel(level)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(_FORMATTER)
    logger.addHandler(stream_handler)

    if _LOG_FILE:
        file_handler = RotatingFileHandler(
            _LOG_FILE,
            maxBytes=2_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(_FORMATTER)
        logger.addHandler(file_handler)

    logger.propagate = False
