#!/usr/bin/env python

import re

import docopt

from neuromation.cli.commands import commands, help_format, normalize_options, parse
from neuromation.cli.main import DEFAULTS, neuro


def parse_func(func, format_spec, stack):
    result = " ".join(stack) + "\n"
    doc = func.__doc__
    if not doc:
        result += "Not implemented"
        return result

    doc = help_format(doc, format_spec)
    result += doc
    try:
        options, tail = parse(doc, stack)
        command_result = func(**{**normalize_options(options, ["COMMAND"])})
    except docopt.DocoptExit:
        #  dead end
        if not re.search(r"\sCOMMAND\s*$", doc, re.M):
            return result
        command_result = func()

    for command in commands(command_result):
        result += parse_func(
            command_result.get(command), format_spec, stack + [command]
        )

    # strip header
    # strip footer
    # usage and options
    # examples
    return result


def main():
    print("Hello")
    result = parse_func(neuro, DEFAULTS, ["neuro"])
    print(result)


if __name__ == "__main__":
    main()
