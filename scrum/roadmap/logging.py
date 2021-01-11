"""Logging helper functions."""
from __future__ import absolute_import

import logging


class Logger:
    """Helper class for logging."""

    def __init__(self, level=None):
        """Set up logging instance and set log level."""
        self.logger = logging.getLogger("cloudstats")
        if level:
            self.setLevel(level)

        if not len(self.logger.handlers):
            console = logging.StreamHandler()
            console.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)s - %(message)s")
            )
            self.logger.addHandler(console)

    def set_level(self, level="info"):
        """Set the level to the provided level."""

        if level:
            level = level.lower()

        if level == "debug":
            self.logger.setLevel(logging.DEBUG)
        elif level == "warn":
            self.logger.setLevel(logging.WARN)
        elif level == "error":
            self.logger.setLevel(logging.ERROR)
        else:
            self.logger.setLevel(logging.INFO)

    def debug(self, message):
        """Log a message with debug loglevel."""
        self.logger.debug(message)

    def info(self, message):
        """Log a message with info loglevel."""
        self.logger.info(message)

    def warn(self, message):
        """Log a message with warn loglevel."""
        self.logger.warn(message)

    def error(self, message):
        """Log a message with warn loglevel."""
        self.logger.error(message)
