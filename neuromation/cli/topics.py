from .utils import group


@group()
def topics() -> None:
    """Help topics."""


@topics.command()
async def ps_format() -> None:
    """Format for columns specification.

    The format is a sequence of column specifications separated by commas or spaces:
    {id}, {status}, {when}

    A column spec has a mandatory column id plus optional properties for indication of
    alignment, minimum and maximum column width, and optional column title:

    \b
    {id;align=center;min=10;max=30;width=20;ID TITLE}

    Here id is the column id, aling, min, max, width are properties and ID TITLE is the
    column title.


    Available properties:

    \b
    align  Column aligning, accepted values: left, right, center.
    min    Minimal column width
    max    Maximal column width
    width  Default column width

    All properties can be skipped, the default value for specified column ID is used in
    this case.


    The system recognizes the following columns:

    \b
    ID            TITLE       ALIGN MIN MAX  WIDTH
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
    the full name.  For example {CLUSTER:max=20} is a good column spec but {C:max=20} is
    not; it can be expanded into both cluster_name and command column ids.

    """


@topics.command()
async def user_config() -> None:
    """\
    User configuration files.

    The Neuro platform supports user configuration files to provide default values for
    particular command options, user defined command aliases etc.

    There are two configuration files: global and local, both are optional and can be
    absent.

    The global file is located in the standard neuro config path.  "neuro" CLI uses
    ~/.neuro folder by default, the path for global config file is ~/.neuro/user.toml.

    The local config file is named .neuro.toml, the CLI search for this file starting
    from the current folder up to the root directory.

    Found local and global configurations are merged. If a parameter is present is both
    global and local versions the local parameter takes a precedence.

    Configuration files have a TOML format (a stricter version of well-known INI
    format). See https://en.wikipedia.org/wiki/TOML and
    https://github.com/toml-lang/toml#toml for the format specification details.

    Supported configuration sections and parameters:

    [job]

      A section for "neuro job" command group settings.


    ps-format

      Default value for "neuro ps --format=XXX" option.

      See "neuro help ps-format" for information about the value specification.

    [storage]

      A section for "neuro storage" command group settings.


    cp-exclude

      Default value for "neuro cp" --exclude=XXX" and "--include=YYY" options.

      The value is a list of shell wildcard patterns, a file or folder that matches a
      pattern is excluded from processing.

      The pattern can contain * and ?, e.g. ["*.jpg"] is for exclusion of all files with
      .jpg extension.

      Exclamation mark ! is used to negate the pattern, e.g. ["*.jpg", "!main.jpg"]
      excludes all .jpg files except "main.jpg".


    Sample of configuration file:

    \b
    # job section
    [job]
    ps-format = "{id;max=30}, {status;max=10}"
    \b
    # storage section
    [storage]
    cp-exclude = ["*.jpg", "!main.jpg"]
    """
