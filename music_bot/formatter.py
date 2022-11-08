# Standard library imports.
import logging


class Formatter(logging.Formatter):
    """Subclass Formatter to custom format logging messages."""

    def format(self, record):
        # ANSI escape codes for colors:
        # black = "\x1b[30;20m"
        # blue = "\x1b[34;20m"
        # cyan = "\x1b[36;20m"
        # dark_grey = "\x1b[30;1m"
        # grey = "\x1b[38;20m"
        # green = "\x1b[32;20m"
        # light_blue = "\x1b[34;1m"
        # light_cyan = "\x1b[36;1m"
        # light_green = "\x1b[32;1m"
        # light_grey = "\x1b[37;20m"
        # light_red = "\x1b[31;1m"
        # light_purple = "\x1b[35;1m"
        # orange = "\x1b[33;20m"
        # purple = "\x1b[35;20m"
        red = "\x1b[31;20m"
        reset = "\x1b[0m"
        # white = "\x1b[;20m"
        yellow = "\x1b[33;20m"
        if record.levelno == logging.INFO:
            self._style._fmt = "%(message)s"
        elif record.levelno == logging.ERROR:
            self._style._fmt = f"({red}%(levelname)s{reset}) [%(asctime)s]: %(message)s"
        else:
            self._style._fmt = (
                f"({yellow}%(levelname)s{reset}) [%(asctime)s]: %(message)s"
            )

        return super().format(record)
