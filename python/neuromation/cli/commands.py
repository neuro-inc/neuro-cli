import types
from asyncio import iscoroutine
from functools import singledispatch
from textwrap import dedent

import docopt
from neuromation.utils import run


def add_command_name(f, name):
    f._command_name = name
    return f


@singledispatch
def command(arg):
    def wrap(f):
        def wrapped(*args, **kwargs):
            return f(*args, **kwargs)

        wrapped.__doc__ = f.__doc__
        return add_command_name(wrapped, arg)

    return wrap


@command.register(types.FunctionType)
def _func(f):
    return add_command_name(f, f.__name__)


@command.register(types.CoroutineType)
def _coro(f):
    return add_command_name(f, f.__name__)


def commands(scope):
    """Return all commands in target scope (i.e. module or function)"""

    return {
        func._command_name: func
        for func in scope.values()
        if hasattr(func, "_command_name")
    }


def normalize_options(args, exclude):
    return {
        key.lstrip("-").lower().replace("-", "_"): value
        for key, value in args.items()
        if key not in exclude
    }


def parse(doc, argv):
    head = argv.copy()
    tail = []

    while head:
        try:
            return docopt.docopt(doc, argv=head, help=False), tail
        except docopt.DocoptExit:
            tail = [head.pop()] + tail

    return docopt.docopt(doc, argv=head, help=False), tail


def get_help(target, tail, stack, format_spec):
    while True:
        if not tail:
            return help_format(target.__doc__, format_spec)

        try:
            options, tail = parse(target.__doc__, stack + tail)
        except docopt.DocoptExit:
            help_msg = help_format(target.__doc__, format_spec)
            raise ValueError(f'Invalid arguments: {" ".join(tail)}\n{help_msg}')

        command = options.get("COMMAND", None)
        if not command:
            return help_format(target.__doc__, format_spec)

        res = target(**{**normalize_options(options, stack + ["COMMAND"])})
        target = commands(res).get(command, None)
        if not target:
            help_msg = help_format(target.__doc__, format_spec)
            raise ValueError(f"Invalid command: {command}\n{help_msg}")

        stack += [command]


def help_format(help, format_spec):
    if not help:
        return ""
    if format_spec:
        help = help.format(**format_spec)
    help = dedent(help)
    return help


def dispatch(target, tail, format_spec=None, **kwargs):
    def help_required(tail):
        for option in tail:
            if option == "--help":
                return True
            elif option[:1] == "-":
                continue
            else:
                return False
        return False

    stack = []

    while True:
        if not target.__doc__:
            raise NotImplementedError("Not implemented")
        target.__doc__ = help_format(target.__doc__, format_spec)
        try:
            options, tail = parse(target.__doc__, stack + tail)
        except docopt.DocoptExit:
            raise ValueError(target.__doc__)

        command = options.get("COMMAND", None)
        if command == "help" and not stack:
            return get_help(target, tail, stack, format_spec)

        if not command and tail:
            raise ValueError(f'Invalid arguments: {" ".join(tail)}')

        res = target(**{**normalize_options(options, stack + ["COMMAND"]), **kwargs})
        if iscoroutine(res):
            res = run(res)
        # Don't pass to tested commands, they will be available through
        # closure anyways
        kwargs = {}

        if not command and not tail:
            return res

        target = commands(res).get(command, None)

        if not target:
            raise ValueError(f"Invalid command: {command}")

        if help_required(tail):
            return help_format(target.__doc__, format_spec)

        stack += [command]
