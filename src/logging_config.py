import logging
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOGGER_NAME = "pavo"
LOG_FILENAME = "pavo.log"
MAX_LOG_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 3

_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_CONFIG_LOCK = threading.Lock()


def setup_logging(log_dir=None):
    """Configure Pavo logging once and return the application logger."""
    app_logger = logging.getLogger(LOGGER_NAME)

    with _CONFIG_LOCK:
        if any(getattr(handler, "_pavo_managed", False) for handler in app_logger.handlers):
            return app_logger

        app_logger.setLevel(logging.DEBUG)
        app_logger.propagate = False

        formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

        console_handler = logging.StreamHandler()
        console_handler.set_name("pavo-console")
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        console_handler._pavo_managed = True
        app_logger.addHandler(console_handler)

        try:
            target_dir = Path(log_dir).expanduser() if log_dir else Path.home() / "Library" / "Logs" / "Pavo"
            target_dir.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                target_dir / LOG_FILENAME,
                maxBytes=MAX_LOG_BYTES,
                backupCount=LOG_BACKUP_COUNT,
                encoding="utf-8",
            )
            file_handler.set_name("pavo-file")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            file_handler._pavo_managed = True
            app_logger.addHandler(file_handler)
        except Exception as exc:
            app_logger.warning("File logging is unavailable: %s", exc)

        app_logger.info("Pavo logging initialized")
        return app_logger
