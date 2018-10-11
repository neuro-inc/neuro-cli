import types
from functools import singledispatch
from textwrap import dedent

import docopt


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
def _(f):
    return add_command_name(f, f.__name__)


def commands(scope):
    """Return all commands in target scope (i.e. module or function)"""
    return {
        func._command_name: func
        for func in scope.values()
        if hasattr(func, '_command_name')
    }


def normalize_options(args, exclude):
    return {
        key.lstrip('-').lower().replace('-', '_'): value
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


def dispatch(target, tail, **kwargs):
    def help_required(tail):
        for option in tail:
            if option == '--help':
                return True
            elif option[:1] == '-':
                continue
            else:
                return False
        return False

    stack = []

    while True:
        try:
            options, tail = parse(target.__doc__, stack + tail)
        except docopt.DocoptExit:
            raise ValueError(dedent(target.__doc__))

        res = target(**{
            **normalize_options(options, stack + ['COMMAND']), **kwargs})
        # Don't pass to tested commands, they will be available through
        # closure anyways
        kwargs = {}

        command = options.get('COMMAND', None)

        if not command and tail:
            raise ValueError(f'Invalid arguments: {" ".join(tail)}')

        if not command and not tail:
            return res

        target = commands(res).get(command, None)

        if not target:
            raise ValueError(f'Invalid command: {command}')

        if help_required(tail):
            raise ValueError(dedent(target.__doc__))

        stack += [command]
