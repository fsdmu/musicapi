"""Logging configuration for the music API project."""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "musicapi.log")

formatter = logging.Formatter("%(asctime)s - %(levelname)s - " "%(name)s - %(message)s")

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# avoid adding duplicate handlers on reload
if not any(
    isinstance(h, RotatingFileHandler) and h.baseFilename == os.path.abspath(LOG_FILE)
    for h in root_logger.handlers
):
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=3)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

# ensure console output still appears
if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root_logger.addHandler(console)
