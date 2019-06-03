import logging.handlers
import os
from pathlib import Path

import arrow

from bot.constants import Client

# start datetime
start_time = arrow.utcnow()

# set up logging
log_dir = Path("bot", "log")
log_file = log_dir / "hackbot.log"
os.makedirs(log_dir, exist_ok=True)

# file handler sets up rotating logs every 5 MB
file_handler = logging.handlers.RotatingFileHandler(
    log_file, maxBytes=5*(2**20), backupCount=10)
file_handler.setLevel(logging.DEBUG)

# console handler prints to terminal
console_handler = logging.StreamHandler()
level = logging.DEBUG if Client.debug else logging.INFO
console_handler.setLevel(level)

# remove old loggers if any
root = logging.getLogger()
if root.handlers:
    for handler in root.handlers:
        root.removeHandler(handler)

# Silence irrelevant loggers
logging.getLogger("discord").setLevel(logging.ERROR)
logging.getLogger("websockets").setLevel(logging.ERROR)

# setup new logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s %(levelname)s: %(message)s',
    datefmt="%D %H:%M:%S",
    level=logging.DEBUG,
    handlers=[console_handler, file_handler]
)
logging.getLogger().info('Logging initialization complete')
