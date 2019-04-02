from neuromation.cli.command_spinner import SpinnerBase, StandardSpinner


def test_spinner_factory_none(capsys):
    spinner = SpinnerBase.create_spinner(False)
    assert type(spinner) == SpinnerBase
    spinner.start("No more bananas")
    spinner.tick()
    spinner.complete(":(")
    captured = capsys.readouterr()
    assert not (captured.out)


def test_spinner_factory_standard():
    spinner = SpinnerBase.create_spinner(True)
    assert type(spinner) == StandardSpinner


class TestSpinnerStandard:
    def test_start_message(self, capsys):
        spinner = SpinnerBase.create_spinner(True)
        spinner.start()
        captured = capsys.readouterr()
        spinner.complete()
        assert not captured.out

        spinner = SpinnerBase.create_spinner(True)
        spinner.start("Bananas!")
        captured = capsys.readouterr()
        spinner.complete()
        assert captured.out.strip() == "Bananas!"

    def test_complete_message(self, capsys):
        spinner = SpinnerBase.create_spinner(True)
        spinner.start()
        spinner.complete()
        captured = capsys.readouterr()
        assert captured.out.strip() == ""

        spinner = SpinnerBase.create_spinner(True)
        spinner.start("More bananas!")
        spinner.complete()
        captured = capsys.readouterr()
        assert captured.out.strip() == "More bananas!"

        spinner = SpinnerBase.create_spinner(True)
        spinner.start("More bananas!")
        spinner.complete("Yet more bananas!!!")
        captured = capsys.readouterr()
        assert captured.out.strip().endswith("Yet more bananas!!!")

    def test_tick(self, capsys):
        spinner = SpinnerBase.create_spinner(True)
        spinner.start()
        spinner.tick()
        captured = capsys.readouterr()
        assert captured.out.strip() == "|"
        spinner.tick()
        captured = capsys.readouterr()
        assert captured.out.strip() == "\\"
        spinner.complete()
