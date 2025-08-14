import logging
import os

logger = logging.getLogger("krona")

# Set log level from environment variable, default to INFO
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logger.setLevel(getattr(logging, log_level))

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

fh = logging.FileHandler("krona.log", mode="w")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)
