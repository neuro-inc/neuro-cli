from .utils import command, group


@group()
def topics():
    """Help topics."""


@command()
def format():
    """Format for columns specification.

    The format is a sequence of column specifications separated by commas or spaces:
    {id}, {status}, {when}

    A column spec has a mandatory column id plus optional properties for indication of
    alignment, minimum and maximum column width, and optional column title:

    \b
    {id:align=center;min=10;max=30;width=20;ID TITLE}

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


topics.add_command(format)
