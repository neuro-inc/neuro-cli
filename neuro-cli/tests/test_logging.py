from logging import ERROR, WARNING, LogRecord

from neuromation.cli.log_formatter import ConsoleWarningFormatter


formatter = ConsoleWarningFormatter("%(name)s.%(funcName)s: %(message)s")


def test_warning() -> None:
    record = LogRecord("n", WARNING, "p", 1, "warn-message", (), None)
    formatted = formatter.format(record)
    # yellow WARNING
    assert formatted.startswith("\x1b[33mWARNING\x1b[0m")
    # message inside
    assert formatted.find("warn-message") >= 0


def test_error() -> None:
    record = LogRecord("n", ERROR, "p", 1, "error-message", (), None)
    formatted = formatter.format(record)
    # red ERROR
    assert formatted.startswith("\x1b[31mERROR\x1b[0m")
    # message inside
    assert formatted.find("error-message") >= 0
