import logging

logger = logging.getLogger("krona")
logger.setLevel(logging.INFO)
fh = logging.FileHandler("krona.log", mode="w")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)
