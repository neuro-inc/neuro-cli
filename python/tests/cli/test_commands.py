import re

import pytest

from neuromation.cli.commands import command, commands, dispatch


# NOTE: overriding command name to be 'person'
@command("person")
def _person(name, age, gender, city):
    """
    Usage:
      person -n NAME [options ...] COMMAND

    Options:
      -n, --name NAME             Name
      -a, --age AGE               Age
      -g, --gender GENDER         Gender

    Commands:
      work               Work
      rest               Rest
      help               command reference

    (c) {year}
    """

    @command
    def work(intensity):
        """
        Usage:
          person work [options] COMMAND

        Options:
          -i, --intensity VALUE      Intensity (HIGH, MEDIUM, LOW)  [default: LOW]
           
        (c) {year}
        """  # NOQA

        @command
        def dig(depth, what):
            """
            Usage:
              person work dig [options] WHAT

            Options:
              -d, --depth VALUE         Depth (BIG, SMALL) [default: BIG]

            (c) {year}
            """
            return f"{name} is digging {depth} {what} in {city}"

        @command
        def manage(style, whom):
            """
            Usage:
              person work manage [options] WHOM

            Options:
              -s, --style STYLE         Style (ex: seagull, etc)  [default: crushing]
            
            (c) {year}
            """  # NOQA
            return f"{name} is {style} {whom} in {city}"

        return locals()

    # NOTE: options and operands have switched places in
    # method signature. We support that as well
    @command
    def rest(where, duration):
        """
        Usage:
          person rest [options] WHERE

        Options:
          -d, --duration HOURS    Duration in hours [default: 1]

        (c) {year}
        """
        return f"{name} is resting {where} for {duration} hour"

    def nothing():
        pass

    return locals()


def test_dispatch():
    argv = ["-n", "Vasya", "work", "dig", "hole"]
    # 'manage', '-s', 'enabling', 'engineers']
    assert (
        dispatch(target=_person, tail=argv, city="Kyiv")
        == "Vasya is digging BIG hole in Kyiv"
    )

    argv = ["-n", "Vova", "work", "manage", "Petya"]
    assert (
        dispatch(target=_person, tail=argv, city="Kyiv")
        == "Vova is crushing Petya in Kyiv"
    )

    argv = ["-n", "Vova", "work", "manage", "-s", "enabling", "Petya"]
    assert (
        dispatch(target=_person, tail=argv, city="Kyiv")
        == "Vova is enabling Petya in Kyiv"
    )

    argv = ["-n", "Vova", "rest", "home"]
    assert (
        dispatch(target=_person, tail=argv, city="Kyiv")
        == "Vova is resting home for 1 hour"
    )


def test_dispatch_help():
    argv = ["-n", "Vova", "rest", "--help"]
    result = dispatch(target=_person, tail=argv, city="Kyiv")
    assert re.match(".*Usage.+person rest", result, re.DOTALL)

    argv = ["-n", "Vova", "rest", "--any-long-option", "-any-short-option", "--help"]
    result = dispatch(target=_person, tail=argv, city="Kyiv")
    assert re.match(".*Usage.+person rest", result, re.DOTALL)

    argv = ["-n", "Vova", "rest", "Alabama", "-d", "1day", "--help"]
    try:
        dispatch(target=_person, tail=argv, city="Kyiv")
    except ValueError as err:
        if str(err) != "Invalid arguments: --help":
            pytest.fail("--help option error detection")


def test_dispatch_help_format_spec():
    argv = ["--help"]
    with pytest.raises(ValueError, match=r"2018"):
        dispatch(target=_person, tail=argv, format_spec={"year": 2018})

    argv = ["Vasya", "work"]
    with pytest.raises(ValueError, match=r"2018"):
        dispatch(target=_person, tail=argv, format_spec={"year": 2018})

    argv = ["Vasya", "work", "dig", "hole"]
    with pytest.raises(ValueError, match=r"2018"):
        dispatch(target=_person, tail=argv, format_spec={"year": 2018})


def test_invalid_command():
    argv = ["-n", "Vasya", "work", "unknown", "command"]
    with pytest.raises(ValueError, match=r"Invalid command: unknown"):
        dispatch(target=_person, tail=argv, format_spec={"year": 2018}, city="Kyiv")


def test_commands():
    assert commands(scope=globals()) == {"person": _person}

    assert set(commands(scope=_person(None, None, None, None))) == {"work", "rest"}
