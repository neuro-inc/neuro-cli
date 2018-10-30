import logging

from . import colors


class ConsoleWarningFormatter(logging.Formatter):
    """A logging.Formatter which prints WARNING and ERROR messages with
    a prefix of the log level colored appropriate for the log level.
    """

    def get_level_message(self, record: logging.LogRecord) -> str:
        separator = ": "

        if record.levelno == logging.WARNING:
            return colors.COLOR_FUNCS["yellow"](record.levelname) + separator
        if record.levelno == logging.ERROR:
            return colors.COLOR_FUNCS["red"](record.levelname) + separator

        return ""

    def format(self, record: logging.LogRecord) -> str:
        if isinstance(record.msg, bytes):
            record.msg = record.msg.decode("utf-8")
        message = super(ConsoleWarningFormatter, self).format(record)
        return "{0}{1}".format(self.get_level_message(record), message)
