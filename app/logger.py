# app/logger.py
"""
Central logging configuration for ScanSutra OCR.

Usage in any file:
    from app.logger import get_logger
    log = get_logger(__name__)
    log.info("something happened")
    log.error("something broke", exc_info=True)
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ── Config ─────────────────────────────────────────────────────────────────────
LOG_LEVEL   = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_TO_FILE = os.getenv("LOG_TO_FILE", "true").lower() == "true"
LOG_DIR     = Path(os.getenv("LOG_DIR", "logs"))
LOG_FILE    = LOG_DIR / "scansutra.log"
MAX_BYTES   = 5 * 1024 * 1024   # 5 MB per file
BACKUP_COUNT = 3                 # keep last 3 rotated files


# ── Formatter ──────────────────────────────────────────────────────────────────
class ColorFormatter(logging.Formatter):
    """Colored output for terminal."""

    COLORS = {
        "DEBUG":    "\033[36m",   # cyan
        "INFO":     "\033[32m",   # green
        "WARNING":  "\033[33m",   # yellow
        "ERROR":    "\033[31m",   # red
        "CRITICAL": "\033[35m",   # magenta
    }
    RESET = "\033[0m"

    FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    DATE_FMT = "%Y-%m-%d %H:%M:%S"

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        formatter = logging.Formatter(
            f"{color}{self.FMT}{self.RESET}",
            datefmt=self.DATE_FMT,
        )
        return formatter.format(record)


PLAIN_FORMATTER = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# ── Setup (called once at startup) ─────────────────────────────────────────────
def setup_logging():
    """Configure root logger. Call once in main.py lifespan."""
    root = logging.getLogger()
    root.setLevel(LOG_LEVEL)

    # Remove existing handlers to avoid duplicates on reload
    root.handlers.clear()

    # Console handler — colored
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(ColorFormatter())
    console.setLevel(LOG_LEVEL)
    root.addHandler(console)

    # File handler — plain text, rotating
    if LOG_TO_FILE:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(PLAIN_FORMATTER)
        file_handler.setLevel(LOG_LEVEL)
        root.addHandler(file_handler)

    # Silence noisy third-party loggers
    logging.getLogger("multipart").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("pdf2image").setLevel(logging.WARNING)

    root.info(
        f"Logging initialized | level={LOG_LEVEL} | "
        f"file={'enabled → ' + str(LOG_FILE) if LOG_TO_FILE else 'disabled'}"
    )


def get_logger(name: str) -> logging.Logger:
    """Get a named logger. Use __name__ as the name."""
    return logging.getLogger(name)