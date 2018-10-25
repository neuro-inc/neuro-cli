from unittest import mock

from neuromation.cli.command_progress_report import StandardPrintPercentOnly


def test_simple_progress():
    report = StandardPrintPercentOnly()
    file_name = 'abc'

    with mock.patch('builtins.print', return_value=None) as p:
        report.start(file_name, 100)
        p.assert_called()
        assert file_name in p.call_args_list[0][0][0]
        assert 'Starting' in p.call_args_list[0][0][0]

    with mock.patch('builtins.print', return_value=None) as p:
        report.progress(file_name, 50)
        p.assert_called()
        assert file_name in p.call_args_list[0][0][0]
        assert '50.00%' in p.call_args_list[0][0][0]

    with mock.patch('builtins.print', return_value=None) as p:
        report.progress(file_name, 75)
        p.assert_called()
        assert file_name in p.call_args_list[0][0][0]
        assert '75.00%' in p.call_args_list[0][0][0]

    with mock.patch('builtins.print', return_value=None) as p:
        report.complete(file_name)
        p.assert_called()
        assert file_name in p.call_args_list[0][0][0]
