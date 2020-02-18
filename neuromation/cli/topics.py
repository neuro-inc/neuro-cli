import re
from typing import Any, Callable, Iterable, Optional, Type

import click

from .utils import group


BOLD = re.compile(r"(?P<mark>\*\*|__)(?P<content>\S.*?\S)(?P=mark)")
EMPHASIS = re.compile(r"(?P<mark>\*|_)(?P<content>\S.*?\S)(?P=mark)")
INLINE_CODE = re.compile(r"`(?P<content>\S.*?\S)`")
CODE_BLOCK = re.compile(r"```(?P<content>.*?)```", re.DOTALL | re.MULTILINE)


def apply_styling(txt: Optional[str]) -> Optional[str]:
    if txt is None:
        return None
    txt = BOLD.sub(click.style(r"\g<content>", bold=True), txt)
    txt = EMPHASIS.sub(click.style(r"\g<content>", underline=True), txt)
    txt = INLINE_CODE.sub(click.style(r"\g<content>", bold=True, dim=True), txt)
    match = CODE_BLOCK.search(txt)
    while match is not None:
        lines = txt[: match.start()].splitlines()
        for line in match.group("content").strip().splitlines():
            lines.append(click.style(line, dim=True))
        lines.extend(txt[match.end() :].splitlines())
        txt = "\n".join(lines)
        match = CODE_BLOCK.search(txt)
    return txt


class Command(click.Command):
    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        if self.help is None:
            return
        head, rest = self.help.split("\n", 1)
        formatter.write(click.style(head, bold=True))
        formatter.write_paragraph()
        formatter.write_paragraph()
        formatter.write(apply_styling(rest))
        with open("out.txt", "w") as f:
            f.write(apply_styling(rest))


def command(
    name: Optional[str] = None, cls: Type[Command] = Command, **kwargs: Any
) -> Command:
    return click.command(name=name, cls=cls, **kwargs)  # type: ignore


class Group(click.Group):
    def command(
        self, *args: Any, **kwargs: Any
    ) -> Callable[[Callable[..., Any]], Command]:
        def decorator(f: Callable[..., Any]) -> Command:
            cmd = command(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd

        return decorator

    def group(
        self, *args: Any, **kwargs: Any
    ) -> Callable[[Callable[..., Any]], "Group"]:
        def decorator(f: Callable[..., Any]) -> Group:
            cmd = group(*args, **kwargs)(f)
            self.add_command(cmd)
            return cmd

        return decorator

    def list_commands(self, ctx: click.Context) -> Iterable[str]:
        return self.commands


def group(name: Optional[str] = None, **kwargs: Any) -> Group:
    kwargs.setdefault("cls", Group)
    return click.group(name=name, **kwargs)  # type: ignore


@group()
def topics() -> None:
    """Help topics."""


@topics.command()
async def ps_format() -> None:
    """Format for columns specification.

    The format is a sequence of column specifications separated by commas or spaces:
    `{id}, {status}, {when}`.

    A column spec has a mandatory column id plus optional properties for indication of
    alignment, minimum and maximum column width, and optional column title:

    `{id;align=center;min=10;max=30;width=20;ID TITLE}`

    Here **id** is the column id, **align**, **min**, **max**, **width** are properties
    and **ID TITLE** is the column title.

    An alternative form is specifying the column id only without additional properties,
    in this case curly brackets can be omitted: `id, status, when` or
    `id status when` are valid formats.


    Available properties:

    **align**  Column aligning, accepted values: left, right, center.
    **min**    Minimal column width.
    **max**    Maximal column width.
    **width**  Default column width.

    All properties can be skipped, the default value for specified column ID is used in
    this case.


    The system recognizes the following columns:

    **ID**            **TITLE**       **ALIGN** **MIN** **MAX**  **WIDTH**
    ---------------------------------------------
    id            ID          left  -   -    -
    name          NAME        left  -   40   -
    status        STATUS      left  -   10   -
    when          WHEN        left  -   15   -
    image         IMAGE       left  -   40   -
    owner         OWNER       left  -   25   -
    cluster_name  CLUSTER     left  -   15   -
    description   DESCRIPTION left  -   50   -
    command       COMMAND     left  -   100  -

    By default all columns are left aligned and have no minimal and default widths.

    The column id is case insensitive, it can be shrinked to any unambiguous subset of
    the full name.  For example `{CLUSTER:max=20}` is a good column spec but
    `{C:max=20}` is not; it can be expanded into both `cluster_name` and `command`
    column ids.

    """


@topics.command()
async def user_config() -> None:
    """\
    User configuration files.

    The Neuro platform supports user configuration files to provide default values for
    particular command options, user defined command aliases etc.

    There are two configuration files: **global** and **local**, both are optional and
    can be absent.

    The global file is located in the standard neuro config path.  "neuro" CLI uses
    `~/.neuro` folder by default, the path for global config file is
    `~/.neuro/user.toml`.

    The local config file is named .neuro.toml, the CLI search for this file starting
    from the current folder up to the root directory.

    Found local and global configurations are merged. If a parameter is present is both
    global and local versions the local parameter takes a precedence.

    Configuration files have a TOML format (a stricter version of well-known INI
    format). See `https://en.wikipedia.org/wiki/TOML` and
    `https://github.com/toml-lang/toml#toml` for the format specification details.

    Supported configuration sections and parameters:

    **[job]**

      A section for `neuro job` command group settings.

    **ps-format**

      Default value for `neuro ps --format=XXX` option.

      See `neuro help ps-format` for information about the value specification.

    **[storage]**

      A section for `neuro storage` command group settings.

    **cp-exclude**

      Default value for `neuro cp --exclude=XXX` and `neuro cp --include=YYY` options.

      The value is a list of shell wildcard patterns, a file or folder that matches a
      pattern is excluded from processing.

      The pattern can contain `*` and `?`, e.g. `["*.jpg"]` is for exclusion of all
      files with `.jpg` extension.

      Exclamation mark ! is used to negate the pattern, e.g. `["*.jpg", "!main.jpg"]`
      excludes all `.jpg` files except `main.jpg`.

    Example:
    ```
    # jobs section
    [job]
    ps-format = "{id;max=30}, {status;max=10}"

    # storage section
    [storage]
    cp-exclude = ["*.jpg", "!main.jpg"]
    ```
    """
