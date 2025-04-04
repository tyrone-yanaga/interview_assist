# app/core/logging.py
import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logging():
    logger = logging.getLogger("no_caps")
    logger.setLevel(logging.INFO)
    os.makedirs('logs', exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    file_handler = RotatingFileHandler(
        "logs/app.log", maxBytes=10485760, backupCount=5  # 10MB
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    return logger


logger = setup_logging()
