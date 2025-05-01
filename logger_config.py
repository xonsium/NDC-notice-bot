import logging

log_format = "%(levelname)s - %(asctime)s - %(message)s"
date_format = "%d/%m/%y %H:%M:%S"

logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)

# Prevent duplicate handlers on multiple imports
if not logger.handlers:
    formatter = logging.Formatter(log_format, datefmt=date_format)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler("app.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
