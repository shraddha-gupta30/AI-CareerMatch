"""
Structured Logging Configuration.
"""
import logging
import sys


def setup_logging(debug: bool = True) -> logging.Logger:
    log_level = logging.DEBUG if debug else logging.INFO
    logger = logging.getLogger("ai_careermatch")
    logger.setLevel(log_level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging()
