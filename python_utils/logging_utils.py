"""General logging function"""

import logging, os


__all__ = ["configure_logging"]


def configure_logging(default_level: str = "INFO") -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", default_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )