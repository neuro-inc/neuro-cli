
from neuromation.cli.command_progress_report import (
    ProgressBase,
    StandardPrintPercentOnly,
)


def test_progress_factory_none():
    progress = ProgressBase.create_progress(False)
    assert isinstance(progress, ProgressBase)


def test_progress_factory_percent():
    progress = ProgressBase.create_progress(True)
    assert isinstance(progress, StandardPrintPercentOnly)


def test_simple_progress(capsys):
    report = StandardPrintPercentOnly()
    file_name = "abc"

    report.start(file_name, 100)
    captured = capsys.readouterr()
    assert captured.out == f"Starting file {file_name}.\n"

    report.progress(file_name, 50)
    captured = capsys.readouterr()
    assert captured.out == f"\r{file_name}: 50.00%."

    report.progress(file_name, 75)
    captured = capsys.readouterr()
    assert captured.out == f"\r{file_name}: 75.00%."

    report.complete(file_name)
    captured = capsys.readouterr()
    assert captured.out == f"\rFile {file_name} upload complete.\n"
