import logging
import shutil
import sys

import aiohttp
import click
from yarl import URL

from neuromation.cli.files_formatter import (
    AcrossLayout,
    BaseFileFormatter,
    BaseLayout,
    CommasLayout,
    LongFileFormatter,
    ShortFileFormatter,
    SingleColumnLayout,
    VerticalLayout,
)
from neuromation.client import IllegalArgumentError
from neuromation.client.url_utils import (
    normalize_local_path_uri,
    normalize_storage_path_uri,
)

from .command_progress_report import ProgressBase
from .rc import Config
from .utils import command, group, run_async


log = logging.getLogger(__name__)


@group()
def storage() -> None:
    """
    Storage operations.
    """


@command()
@click.argument("path")
@click.pass_obj
@run_async
async def rm(cfg: Config, path: str) -> None:
    """
    Remove files or directories.

    Examples:

    neuro storage rm storage:///foo/bar/
    neuro storage rm storage:/foo/bar/
    neuro storage rm storage://{username}/foo/bar/
    """
    uri = normalize_storage_path_uri(URL(path), cfg.username)
    log.info(f"Using path '{uri}'")

    async with cfg.make_client() as client:
        await client.storage.rm(uri)


@command()
@click.argument("path", default="storage://~")
@click.option(
    "-C", "force_format_vertical", is_flag=True, help="list entries by columns"
)
@click.option(
    "--format",
    type=click.Choice(
        ["across", "commas", "horizontal", "long", "single-column", "vertical"]
    ),
    help="Output format accross -x, commas -m, horizontal -x,"
    " long -l, single-column -1, vertical -C",
)
@click.option(
    "--human-readable",
    "-h",
    is_flag=True,
    help="with -l/--format=long  print human readable sizes (e.g., 2K, 540M)",
)
@click.option("-l", "force_format_long", is_flag=True, help="use a long listing format")
@click.option(
    "-m",
    "force_format_commas",
    is_flag=True,
    help="fill width with a comma separated list of entries",
)
@click.option(
    "-N",
    "--literal",
    is_flag=True,
    default=True,
    help="print entry names without quoting (default)",
)
@click.option(
    "--time-style",
    "time_style",
    type=str,
    default="locale",
    help="with  -l,  show times using style TEXT: full-iso, long-iso, iso,"
    " locale, or +FORMAT; FORMAT is interpreted like in 'date'"
    "; if FORMAT is FORMAT1<newline>FORMAT2, then FORMAT1 applies to non-recent"
    "files and FORMAT2 to recent files",
)
@click.option(
    "-Q",
    "--quote-name",
    "quote",
    is_flag=True,
    help="enclose entry names in double quotes",
)
@click.option("-w", "--width", type=int, help="set output width, o means no limit")
@click.option(
    "-x",
    "force_format_across",
    is_flag=True,
    help="list entries by lines instead of by columns",
)
@click.option(
    "-1", "force_format_single_column", is_flag=True, help="list one file per line"
)
@click.pass_obj
@run_async
async def ls(
    cfg: Config,
    path: str,
    format: str,
    literal: bool,
    quote: bool,
    width: int,
    force_format_across: bool,
    force_format_commas: bool,
    force_format_long: bool,
    force_format_single_column: bool,
    force_format_vertical: bool,
    time_style: str,
    human_readable: bool,
) -> None:
    """
    List directory contents.

    By default PATH is equal user`s home dir (storage:)
    """
    uri = normalize_storage_path_uri(URL(path), cfg.username)
    log.info(f"Using path '{uri}'")

    async with cfg.make_client() as client:
        files = await client.storage.ls(uri)

    is_tty = sys.stdout.isatty()
    if width is None:
        if is_tty:
            width, _ = shutil.get_terminal_size((80, 25))
        else:
            width = 0

    if quote is None:
        quote = not literal

    layout: BaseLayout
    formatter: BaseFileFormatter
    if force_format_across or format == "across" or format == "horizontal":
        formatter = ShortFileFormatter(quote)
        layout = AcrossLayout(max_width=width)
    elif force_format_commas or format == "commas":
        formatter = ShortFileFormatter(quote)
        layout = CommasLayout(max_width=width)
    elif force_format_single_column or format == "single-column":
        formatter = ShortFileFormatter(quote)
        layout = SingleColumnLayout()
    elif force_format_vertical or format == "vertical":
        formatter = ShortFileFormatter(quote)
        layout = VerticalLayout(max_width=width)
    elif force_format_long or format == "long":
        recent_time_format = ""
        if time_style == "full-iso":
            time_format = "%Y-%m-%d %H:%M:%S.%f %z"
        elif time_style == "long-iso":
            time_format = "%Y-%m-%d %H:%M"
        elif time_style == "iso":
            time_format = "%Y-%m-%d"
            recent_time_format = "%m-%d %H:%M"
        elif time_style == "locale":
            time_format = "%b %e %Y"
            recent_time_format = "%b %e %H:%M"
        elif time_style.startswith("+"):
            time_format = time_style[1:]
            if time_format.find("\n") != -1:
                time_format, recent_time_format = time_format.split("\n", 2)
        else:
            raise IllegalArgumentError(f"Invalid time style: {time_style}")
        formatter = LongFileFormatter(
            time_format=time_format,
            recent_time_format=recent_time_format,
            human_readable=human_readable,
            quoted=quote,
        )
        layout = SingleColumnLayout()
    else:
        formatter = ShortFileFormatter(quote)
        if is_tty:
            layout = VerticalLayout(max_width=width)
        else:
            layout = SingleColumnLayout()

    for line in layout.format(formatter, files):
        click.echo(line)


@command()
@click.argument("source")
@click.argument("destination")
@click.option("-r", "--recursive", is_flag=True, help="Recursive copy, off by default")
@click.option("-p", "--progress", is_flag=True, help="Show progress, off by default")
@click.pass_obj
@run_async
async def cp(
    cfg: Config, source: str, destination: str, recursive: bool, progress: bool
) -> None:
    """
    Copy files and directories.

    Either SOURCE or DESTINATION should have storage:// scheme.
    If scheme is omitted, file:// scheme is assumed.

    Examples:

    # copy local file ./foo into remote storage root
    neuro storage cp ./foo storage:///
    neuro storage cp ./foo storage:/

    # download remote file foo into local file foo with
    # explicit file:// scheme set
    neuro storage cp storage:///foo file:///foo
    """
    timeout = aiohttp.ClientTimeout(
        total=None, connect=None, sock_read=None, sock_connect=30
    )
    src = URL(source)
    dst = URL(destination)

    progress_obj = ProgressBase.create_progress(progress)
    if not src.scheme:
        src = URL(f"file:{src.path}")
    if not dst.scheme:
        dst = URL(f"file:{dst.path}")
    async with cfg.make_client(timeout=timeout) as client:
        if src.scheme == "file" and dst.scheme == "storage":
            src = normalize_local_path_uri(src)
            dst = normalize_storage_path_uri(dst, cfg.username)
            log.info(f"Using source path:      '{src}'")
            log.info(f"Using destination path: '{dst}'")
            if recursive:
                await client.storage.upload_dir(progress_obj, src, dst)
            else:
                await client.storage.upload_file(progress_obj, src, dst)
        elif src.scheme == "storage" and dst.scheme == "file":
            src = normalize_storage_path_uri(src, cfg.username)
            dst = normalize_local_path_uri(dst)
            log.info(f"Using source path:      '{src}'")
            log.info(f"Using destination path: '{dst}'")
            if recursive:
                await client.storage.download_dir(progress_obj, src, dst)
            else:
                await client.storage.download_file(progress_obj, src, dst)
        else:
            raise RuntimeError(
                f"Copy operation of the file with scheme '{src.scheme}'"
                f" to the file with scheme '{dst.scheme}'"
                f" is not supported"
            )


@command()
@click.argument("path")
@click.pass_obj
@run_async
async def mkdir(cfg: Config, path: str) -> None:
    """
    Make directories.
    """

    uri = normalize_storage_path_uri(URL(path), cfg.username)
    log.info(f"Using path '{uri}'")

    async with cfg.make_client() as client:
        await client.storage.mkdirs(uri)


@command()
@click.argument("source")
@click.argument("destination")
@click.pass_obj
@run_async
async def mv(cfg: Config, source: str, destination: str) -> None:
    """
    Move or rename files and directories.

    SOURCE must contain path to the
    file or directory existing on the storage, and DESTINATION must contain
    the full path to the target file or directory.


    Examples:

    # move or rename remote file
    neuro storage mv storage://{username}/foo.txt storage://{username}/bar.txt
    neuro storage mv storage://{username}/foo.txt storage://~/bar/baz/foo.txt

    # move or rename remote directory
    neuro storage mv storage://{username}/foo/ storage://{username}/bar/
    neuro storage mv storage://{username}/foo/ storage://{username}/bar/baz/foo/
    """

    src = normalize_storage_path_uri(URL(source), cfg.username)
    dst = normalize_storage_path_uri(URL(destination), cfg.username)
    log.info(f"Using source path:      '{src}'")
    log.info(f"Using destination path: '{dst}'")

    async with cfg.make_client() as client:
        await client.storage.mv(src, dst)


storage.add_command(cp)
storage.add_command(ls)
storage.add_command(rm)
storage.add_command(mkdir)
storage.add_command(mv)
