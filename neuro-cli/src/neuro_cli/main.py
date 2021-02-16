import asyncio
import io
import logging
import os
import shutil
import sys
import warnings
from pathlib import Path
from textwrap import dedent
from typing import Any, List, Optional, Sequence, Tuple, Union, cast

import aiohttp
import click
from aiodocker.exceptions import DockerError
from click.exceptions import Abort as ClickAbort
from click.exceptions import Exit as ClickExit

import neuro_sdk

import neuro_cli

from . import (
    admin,
    blob_storage,
    completion,
    config,
    disks,
    image,
    job,
    project,
    secrets,
    share,
    storage,
)
from .alias import find_alias
from .asyncio_utils import setup_child_watcher
from .const import (
    EX_DATAERR,
    EX_IOERR,
    EX_NOPERM,
    EX_OSFILE,
    EX_PLATFORMERROR,
    EX_PROTOCOL,
    EX_SOFTWARE,
    EX_TIMEOUT,
)
from .log_formatter import ConsoleHandler
from .root import Root
from .topics import topics
from .utils import (
    Context,
    DeprecatedGroup,
    Group,
    alias,
    argument,
    format_example,
    group,
    option,
    pager_maybe,
    print_help,
)


def setup_stdout(errors: str) -> None:
    if not isinstance(sys.stdout, io.TextIOWrapper):
        return
    sys.stdout.flush()
    if sys.version_info < (3, 7):
        buffered = hasattr(sys.stdout.buffer, "raw")
        buf = open(os.dup(sys.stdout.fileno()), "wb", -1 if buffered else 0)
        raw = getattr(buf, "raw", buf)
        raw.name = "<stdout>"
        sys.stdout = io.TextIOWrapper(
            buf,
            encoding=sys.stdout.encoding,
            errors=errors,
            line_buffering=sys.stdout.line_buffering,
            write_through=not buffered,
        )
    else:
        # cast() is a workaround for https://github.com/python/typeshed/issues/3049
        cast(Any, sys.stdout).reconfigure(errors=errors)


setup_stdout(errors="replace")
setup_child_watcher()


log = logging.getLogger(__name__)


def setup_logging(verbosity: int, color: bool) -> ConsoleHandler:
    root_logger = logging.getLogger()
    handler = ConsoleHandler(color=color)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)

    if verbosity > 1:
        formatter = logging.Formatter("%(name)s.%(funcName)s: %(message)s")
        handler.setFormatter(formatter)

    if verbosity < -1:
        loglevel = logging.CRITICAL
    elif verbosity == -1:
        loglevel = logging.ERROR
    elif verbosity == 0:
        loglevel = logging.WARNING
    elif verbosity == 1:
        loglevel = logging.INFO
    else:
        loglevel = logging.DEBUG

    handler.setLevel(loglevel)

    return handler


LOG_ERROR = log.error


class MainGroup(Group):
    topics = None
    skip_init = False  # use it for testing onlt

    def make_context(
        self,
        info_name: str,
        args: Sequence[str],
        parent: Optional[click.Context] = None,
        **extra: Any,
    ) -> Context:
        ctx = super().make_context(info_name, args, parent, **extra)
        if self.skip_init:
            # Run from test suite
            return ctx

        kwargs = {}
        for param in self.params:
            if param.expose_value:
                val = ctx.params.get(param.name)
                if val is not None:
                    kwargs[param.name] = val
                else:
                    kwargs[param.name] = param.get_default(ctx)

        global LOG_ERROR
        show_traceback = kwargs.get("show_traceback", False)
        if show_traceback:
            LOG_ERROR = log.exception
        tty = all(f.isatty() for f in [sys.stdin, sys.stdout, sys.stderr])
        COLORS = {"yes": True, "no": False, "auto": None}
        real_color: Optional[bool] = COLORS[kwargs["color"]]
        if real_color is None:
            real_color = tty
        ctx.color = real_color
        verbosity = kwargs["verbose"] - kwargs["quiet"]
        handler = setup_logging(verbosity=verbosity, color=real_color)
        if kwargs["hide_token"] is None:
            hide_token_bool = True
        else:
            if not kwargs["trace"]:
                option = "--hide-token" if kwargs["hide_token"] else "--no-hide-token"
                raise click.UsageError(f"{option} requires --trace")
            hide_token_bool = kwargs["hide_token"]

        # The following code is compatibility layer with old images
        # New client doesn't make use of NEURO_STEAL_CONFIG, but
        # it is better to remove it from storage
        # TODO: remove this and upload_and_map_config function
        if "NEURO_STEAL_CONFIG" in os.environ:
            path = Path(os.environ["NEURO_STEAL_CONFIG"])
            if path.exists():
                shutil.rmtree(path)
        # End of compatibility layer

        root = Root(
            verbosity=verbosity,
            color=real_color,
            tty=tty,
            disable_pypi_version_check=kwargs["disable_pypi_version_check"],
            network_timeout=kwargs["network_timeout"],
            config_path=Path(kwargs["neuromation_config"]),
            trace=kwargs["trace"],
            force_trace_all=kwargs["x_trace_all"],
            trace_hide_token=hide_token_bool,
            command_path="",
            command_params=[],
            skip_gmp_stats=kwargs["skip_stats"],
            show_traceback=show_traceback,
            iso_datetime_format=kwargs["iso_datetime_format"],
        )
        handler.setConsole(root.err_console)
        ctx.obj = root
        ctx.call_on_close(root.close)
        return ctx

    def resolve_command(
        self, ctx: click.Context, args: List[str]
    ) -> Tuple[str, click.Command, List[str]]:
        cmd_name, *args = args

        # Get the command
        cmd = self.get_command(ctx, cmd_name)

        if cmd is None:
            # find alias
            root = cast(Root, ctx.obj)
            cmd = root.run(find_alias(root, cmd_name))

        # If we don't find the command we want to show an error message
        # to the user that it was not provided.  However, there is
        # something else we should do: if the first argument looks like
        # an option we want to kick off parsing again for arguments to
        # resolve things like --help which now should go to the main
        # place.
        if cmd is None and not ctx.resilient_parsing:
            if cmd_name and not cmd_name[0].isalnum():
                self.parse_args(ctx, ctx.args)
            ctx.fail(f'No such command or alias "{cmd_name}".')

        assert cmd is not None
        return cmd_name, cmd, args

    def _format_group(
        self,
        title: str,
        grp: Sequence[Tuple[str, click.Command]],
        formatter: click.HelpFormatter,
    ) -> None:
        # allow for 3 times the default spacing
        if not grp:
            return

        width = formatter.width
        assert width is not None
        limit = width - 6 - max(len(cmd[0]) for cmd in grp)

        rows = []
        for subcommand, cmd in grp:
            help = cmd.get_short_help_str(limit)
            rows.append((subcommand, help))

        if rows:
            with formatter.section(title):
                formatter.write_dl(rows)

    def format_commands(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        """Extra format methods for multi methods that adds all the commands
        after the options.
        """
        commands: List[Tuple[str, click.Command]] = []
        groups: List[Tuple[str, click.MultiCommand]] = []
        topics: List[Tuple[str, click.Command]] = []
        if self.topics is not None:
            topics = [
                (name, self.topics.get_command(ctx, name))
                for name in self.topics.list_commands(ctx)
            ]

        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            # What is this, the tool lied about a command.  Ignore it
            if cmd is None:
                continue
            if cmd.hidden:
                continue

            if isinstance(cmd, click.MultiCommand):
                groups.append((subcommand, cmd))
            else:
                commands.append((subcommand, cmd))

        self._format_group("Commands", groups, formatter)
        self._format_group("Command Shortcuts", commands, formatter)
        self._format_group(
            f"Help topics ({ctx.info_name} help <topic>)", topics, formatter
        )

    def format_options(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        self.format_commands(ctx, formatter)
        formatter.write_paragraph()
        formatter.write_text(
            f'Use "{ctx.info_name} help <command>" for more information '
            "about a given command or topic."
        )
        formatter.write_text(
            f'Use "{ctx.info_name} --options" for a list of global command-line '
            "options (applies to all commands)."
        )


def print_options(
    ctx: click.Context, param: Union[click.Option, click.Parameter], value: Any
) -> Any:
    if not value or ctx.resilient_parsing:
        return

    formatter = ctx.make_formatter()
    formatter.write_text("Options available for any command.")
    EXAMPLE = dedent(
        """\
        # Show config without colors
        neuro --color=no config show
    """
    )
    format_example(EXAMPLE, formatter)

    opts = []
    for parameter in ctx.command.get_params(ctx):
        rv = parameter.get_help_record(ctx)
        if rv is not None:
            opts.append(rv)

    with formatter.section("Options"):
        formatter.write_dl(opts)

    click.echo(formatter.getvalue())
    ctx.exit()


@group(cls=MainGroup)
@option(
    "-v",
    "--verbose",
    count=True,
    type=int,
    default=0,
    help="Give more output. Option is additive, and can be used up to 2 times.",
)
@option(
    "-q",
    "--quiet",
    count=True,
    type=int,
    default=0,
    help="Give less output. Option is additive, and can be used up to 2 times.",
)
@option(
    "--neuromation-config",
    type=click.Path(dir_okay=True, file_okay=False),
    required=False,
    help="Path to config directory.",
    default=neuro_sdk.DEFAULT_CONFIG_PATH,
    metavar="PATH",
    envvar=neuro_sdk.CONFIG_ENV_NAME,
)
@option(
    "--show-traceback",
    is_flag=True,
    help="Show python traceback on error, useful for debugging the tool.",
)
@option(
    "--color",
    type=click.Choice(["yes", "no", "auto"]),
    default="auto",
    help="Color mode.",
)
@option(
    "--disable-pypi-version-check",
    is_flag=True,
    help="Don't periodically check PyPI to determine whether a new version of "
    "Neuro Platform CLI is available for download.",
)
@option(
    "--network-timeout", type=float, help="Network read timeout, seconds.", default=60.0
)
@click.version_option(
    version=neuro_cli.__version__, message="Neuro Platform Client %(version)s"
)
@option(
    "--options",
    is_flag=True,
    callback=print_options,
    expose_value=False,
    is_eager=True,
    hidden=True,
    help="Show common options.",
)
@option(
    "--trace",
    is_flag=True,
    help="Trace sent HTTP requests and received replies to stderr.",
)
@option(
    "--x-trace-all",
    hidden=True,
    is_flag=True,
    help="Force distribute tracing in all HTTP requests.",
)
@option(
    "--hide-token/--no-hide-token",
    is_flag=True,
    default=None,
    help=(
        "Prevent user's token sent in HTTP headers from being "
        "printed out to stderr during HTTP tracing. Can be used only "
        "together with option '--trace'. On by default."
    ),
)
@option(
    "--skip-stats/--no-skip-stats",
    is_flag=True,
    default=False,
    help=(
        "Skip sending usage statistics to Neuro servers. "
        "Note: the statistics has no sensitive data, e.g. "
        "file, job, image, or user names, executed command lines, "
        "environment variables, etc."
    ),
)
@option(
    "--iso-datetime-format/--no-iso-datetime-format",
    is_flag=True,
    default=False,
    help=("Use ISO 8601 format for printing date and time"),
)
@click.pass_context
def cli(
    ctx: click.Context,
    verbose: int,
    quiet: bool,
    neuromation_config: str,
    show_traceback: bool,
    color: str,
    disable_pypi_version_check: bool,
    network_timeout: float,
    trace: bool,
    x_trace_all: bool,
    hide_token: Optional[bool],
    skip_stats: bool,
    iso_datetime_format: bool,
) -> None:
    #   ▇ ◣
    #   ▇ ◥ ◣
    # ◣ ◥   ▇
    # ▇ ◣   ▇
    # ▇ ◥ ◣ ▇
    # ▇   ◥ ▇    Neuro Platform
    # ▇   ◣ ◥
    # ◥ ◣ ▇      Deep network training,
    #   ◥ ▇      inference and datasets
    #     ◥
    # Parameters parsing is done in MainGroup.make_context()
    pass


@cli.command(wrap_async=False)
@argument("command", nargs=-1)
@click.pass_context
def help(ctx: click.Context, command: Sequence[str]) -> None:
    """Get help on a command."""
    top_ctx = ctx.find_root()
    root = cast(Root, ctx.obj)

    if len(command) == 1:
        # try to find a topic
        for name, topic in topics.commands.items():
            if name == command[0]:
                # Found a topic
                formatter = ctx.make_formatter()
                topic.format_help(top_ctx, formatter)
                pager_maybe(
                    formatter.getvalue().rstrip("\n").splitlines(),
                    root.tty,
                    root.terminal_size,
                )
                return

    not_found = 'No such command "neuro {}"'.format(" ".join(command))

    ctx_stack = [top_ctx]
    try:
        for cmd_name in command:
            current_cmd = ctx_stack[-1].command
            if isinstance(current_cmd, click.MultiCommand):
                sub_name, sub_cmd, args = current_cmd.resolve_command(ctx, [cmd_name])
                if sub_cmd is None or sub_cmd.hidden:
                    root.print(not_found)
                    break
                sub_ctx = Context(sub_cmd, parent=ctx_stack[-1], info_name=sub_name)
                ctx_stack.append(sub_ctx)
            else:
                root.print(not_found)
                break
        else:
            print_help(ctx_stack[-1])
    finally:
        for ctx in reversed(ctx_stack[1:]):
            ctx.close()


# groups
cli.add_command(admin.admin)
cli.add_command(job.job)
cli.add_command(project.project)
cli.add_command(storage.storage)
cli.add_command(image.image)
cli.add_command(config.config)
cli.add_command(completion.completion)
cli.add_command(share.acl)
cli.add_command(blob_storage.blob_storage)
cli.add_command(secrets.secret)
cli.add_command(disks.disk)

cli.add_command(DeprecatedGroup(storage.storage, name="store", hidden=True))

# shortcuts
cli.add_command(job.run)
cli.add_command(alias(job.ls, "ps", help=job.ls.help, deprecated=False))
cli.add_command(job.status)
cli.add_command(job.exec)
cli.add_command(job.port_forward)
cli.add_command(job.attach)
cli.add_command(job.logs)
cli.add_command(job.kill)
cli.add_command(job.top)
cli.add_command(job.save)
cli.add_command(config.login)
cli.add_command(config.logout)
cli.add_command(storage.cp)
cli.add_command(storage.ls)
cli.add_command(storage.rm)
cli.add_command(storage.mkdir)
cli.add_command(storage.mv)
cli.add_command(alias(image.ls, "images", help=image.ls.help, deprecated=False))
cli.add_command(image.push)
cli.add_command(image.pull)
cli.add_command(alias(share.grant, "share", help=share.grant.help, deprecated=False))

cli.topics = topics


def _err_to_str(err: Exception) -> str:
    result = str(err)
    if result == "":
        result = type(err).__name__
    return result


def main(args: Optional[List[str]] = None) -> None:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            cli.main(args=args, standalone_mode=False)
    except ClickAbort:
        LOG_ERROR("Aborting.")
        sys.exit(130)
    except click.ClickException as e:
        e.show()
        sys.exit(e.exit_code)
    except ClickExit as e:
        sys.exit(e.exit_code)  # type: ignore

    except asyncio.TimeoutError:
        LOG_ERROR("Timeout")
        sys.exit(EX_TIMEOUT)

    except neuro_sdk.IllegalArgumentError as error:
        LOG_ERROR(f"Illegal argument(s) ({_err_to_str(error)})")
        sys.exit(EX_DATAERR)

    except neuro_sdk.ResourceNotFound as error:
        LOG_ERROR(f"{_err_to_str(error)}")
        sys.exit(EX_OSFILE)

    except neuro_sdk.AuthenticationError as error:
        LOG_ERROR(f"Cannot authenticate ({_err_to_str(error)})")
        sys.exit(EX_NOPERM)
    except neuro_sdk.AuthorizationError as error:
        LOG_ERROR(f"Not enough permissions ({_err_to_str(error)})")
        sys.exit(EX_NOPERM)

    except neuro_sdk.ClientError as error:
        LOG_ERROR(f"Application error ({_err_to_str(error)})")
        sys.exit(EX_SOFTWARE)

    except neuro_sdk.ServerNotAvailable as error:
        LOG_ERROR(f"Application error ({_err_to_str(error)})")
        sys.exit(EX_PLATFORMERROR)

    except neuro_sdk.ConfigError as error:
        LOG_ERROR(f"{_err_to_str(error)}")
        sys.exit(EX_SOFTWARE)

    except aiohttp.ClientError as error:
        LOG_ERROR(f"Connection error ({_err_to_str(error)})")
        sys.exit(EX_IOERR)

    except DockerError as error:
        LOG_ERROR(f"Docker API error: {error.message}")
        sys.exit(EX_PROTOCOL)

    except NotImplementedError as error:
        LOG_ERROR(f"{_err_to_str(error)}")
        sys.exit(EX_SOFTWARE)

    except FileNotFoundError as error:
        LOG_ERROR(f"File not found ({_err_to_str(error)})")
        sys.exit(EX_OSFILE)

    except NotADirectoryError as error:
        LOG_ERROR(f"{_err_to_str(error)}")
        sys.exit(EX_OSFILE)

    except PermissionError as error:
        LOG_ERROR(f"Cannot access file ({_err_to_str(error)})")
        sys.exit(EX_NOPERM)

    except OSError as error:
        LOG_ERROR(f"I/O Error ({_err_to_str(error)})")
        sys.exit(EX_IOERR)

    except asyncio.CancelledError:
        LOG_ERROR("Cancelled")
        sys.exit(130)

    except KeyboardInterrupt:
        LOG_ERROR("Aborting.")
        sys.exit(130)

    except ValueError as e:
        LOG_ERROR(_err_to_str(e))
        sys.exit(127)

    except SystemExit:
        raise

    except Exception as e:
        LOG_ERROR(f"{_err_to_str(e)}")
        sys.exit(1)
