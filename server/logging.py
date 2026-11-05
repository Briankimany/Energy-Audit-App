import logging

logger = logging.getLogger("energy_audit")


def register_error_logger(app) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    app.logger.setLevel(logging.INFO)
