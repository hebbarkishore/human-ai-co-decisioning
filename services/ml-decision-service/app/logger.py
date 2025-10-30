import logging

logger = logging.getLogger("app-logger")
logger.setLevel(logging.INFO)
logger.propagate = False

# Avoid adding multiple handlers in case of reload
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)