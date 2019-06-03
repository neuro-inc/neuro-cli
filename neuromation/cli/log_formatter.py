import logging

import click


class ConsoleWarningFormatter(logging.Formatter):
    """A logging.Formatter which prints WARNING and ERROR messages with
    a prefix of the log level colored appropriate for the log level.
    """

    def get_level_message(self, record: logging.LogRecord) -> str:
        separator = ": "

        if record.levelno == logging.WARNING:
            return click.style(record.levelname, fg="yellow") + separator
        if record.levelno == logging.ERROR:
            return click.style(record.levelname, fg="red") + separator

        return ""

    def format(self, record: logging.LogRecord) -> str:
        if isinstance(record.msg, bytes):
            record.msg = record.msg.decode("utf-8")
        message = super(ConsoleWarningFormatter, self).format(record)
        return "{0}{1}".format(self.get_level_message(record), message)


class ConsoleHandler(logging.StreamHandler):
    def emit(self, record: logging.LogRecord) -> None:
        if self.stream.closed:
            return
        try:
            msg = self.format(record)
            click.echo(msg, err=True)
            self.flush()
        except Exception:  # pragma: no cover
            self.handleError(record)
